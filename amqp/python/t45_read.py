#!/usr/bin/env python3
"""
    A pure python rabbitmq read a task from query and reconfig nginx without docker.
    ./t45_read.py enode
"""

import pika
import datetime
import json
import web3
import sys
import time
import pprint
import sys
import os
import threading
import logging
import subprocess

credentials = pika.PlainCredentials('andrey', '1234567890qw')
parameters = pika.ConnectionParameters("10.168.0.3", 5672, '/', credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

enode = sys.argv[1]
verbose = 1

"""
{
        "command": "config",
        "type":    "transcoder", 
        "input": {
                "proto": "rtmp",
                "application": "stream",
                "name": "test",
                "port": "1935"  
        },
        "parameters": {
                "codec": "libx264",
                "vbitrate": "2000000",
                "resolution": "1280x720"
        },
        "output": {
                "proto": "rtmp",
                "application": "hls",
                "name": "test",
                "variant": "hq",
                "ip": "35.242.172.58",
                "port": "1935"
        }
}
to
application stream {
        live on;
        exec ffmpeg -i rtmp://localhost:1935/stream/test
                -vcodec libx264 -vf scale=1280x720 -b:v 2000000 -f flv rtmp://35.242.172.58:1935/hls/test_hq;
}


"""
def reconfig_nginx_transcoder(data):
	res_conf_file = "application " + data['input']['application'] + " {\n"
	res_conf_file += "\t" + "live on;\n"
	res_conf_file += "\t" + "exec ffmpeg -i " + data['input']['proto'] + "://localhost" + ":" + data['input']['port'] + "/" + data['input']['application'] + "/" + data['input']['name'] + "\n"
	res_conf_file += "\t\t" + "-vcodec " + data['parameters']['codec'] + " -b:v " + data['parameters']['vbitrate'] + " -vf scale=" + data['parameters']['resolution']
	if data['output']['proto'] == "rtmp":
		res_conf_file += " -f flv "
	res_conf_file +=  data['output']['proto'] + "://" + data['output']['ip'] + ":" + data['output']['port'] + "/" + data['output']['application'] + "/" + data['output']['name'] 
	try:
		res_conf_file += "_" + data['output']['variant'] + "\n"
	except KeyError:
		res_conf_file += "\n"
	res_conf_file += "}\n"
	if verbose:
		print("conf = {}".format(res_conf_file))
	with open(os.path.join('/etc/nginx/app-available/',data['input']['application']), "w") as file1:
    		file1.write(res_conf_file)
	## make link and reload nginx
	src = '/etc/nginx/app-available/' + data['input']['application']
	dst = '/etc/nginx/app-enabled/' + data['input']['application']
	# This creates a symbolic link on python in tmp directory
	try:
    		os.remove(dst)
	except OSError:
    		pass
	os.symlink(src, dst)
	cmd = '/bin/systemctl reload nginx.service'
	proc = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE)
	proc.communicate()
	return 0

"""
Json file to nginx config and reload.
{
        "command": "config",
        "type": "storage",
        "fragemt_duration": "5",
        "inputs": [
                {
                        "proto": "rtmp",
                        "application": "hls",
                        "name": "test",
                        "variant": "original",
                        "resolution": "1920x1080",
                        "vbitrate": "8000",
                        "port": "1935"
                },
                {
                        "proto": "rtmp",
                        "application": "hls",
                        "name": "test",
                        "variant": "hq"
                        "resolution": "1920x1080",
                        "vbitrate": "8000",
                        "port": "1935"
                }
        ]

}

to
        application hls {
            live on;
            hls on;
            hls_fragment 5s;
            hls_path /opt/data/hls;
        }

"""
def reconfig_nginx_storage(data):
	app=""
	for p in data['inputs']:
		res_conf_file = "application " + p['application'] + " {\n"
		app=p['application']
		break
	hls_path="/opt/data/" + app 
	res_conf_file += "\t" + "live on;\n"
	res_conf_file += "\t" + "hls on;\n"
	try:
		res_conf_file += "\t" + "hls_fragment " +  p['fragemt_duration'] +"s;\n"
	except KeyError:
		res_conf_file += "\t" + "hls_fragment 5s;\n"
	res_conf_file += "\t" + "hls_path " + hls_path + ";\n"
	res_conf_file += "\t" + "hls_nested off;\n"
	res_conf_file += "\t" + "hls_fragment_naming timestamp;\n"
	res_conf_file += "\t" + "hls_fragment_naming_granularity 2;\n"
	res_conf_file += "\t" + "hls_fragment_slicing aligned;\n"	
	for p in data['inputs']:
		res_conf_file += "\t"	+ "hls_variant" + " _" + p['variant'] + " BANDWIDTH=" + p['vbitrate'] + "," + "RESOLUTION=" + p['resolution'] + ";\n" 
	res_conf_file += "}\n"
	if verbose:
		print("conf = {}".format(res_conf_file))
	with open(os.path.join('/etc/nginx/app-available/',app), "w") as file1:
    		file1.write(res_conf_file)
	## make link and reload nginx
	src = '/etc/nginx/app-available/' + app
	dst = '/etc/nginx/app-enabled/' + app
	# This creates a symbolic link on python in tmp directory
	try:
    		os.remove(dst)
	except OSError:
    		pass
	os.symlink(src, dst)
	cmd = '/bin/systemctl reload nginx.service'
	proc = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE)
	proc.communicate()
	return 0

"""
Json command to nginx config and reload.
{
        "command": "config",
        "type": "distributor",
        "input": {
                "proto": "rtmp",
                "application": "stream",
                "name": "test",
                "port": "1935"
        },
       "outputs": [
        {
                        "proto": "rtmp",
                        "application": "hls",
                        "name": "test",
                        "variant": "original",
                        "ip": "35.242.172.58",
                        "port": "1935"
        },
        {
                        "proto": "rtmp",
                        "application": "stream",
                        "name": "test",
                        "ip": "35.236.33.116",
                        "port": "1935"
        }
    ]
}

to
application stream {
        live on;
        exec ffmpeg -i rtmp://localhost:1935/stream/test
                -c:a copy -c:v copy -f rtmp://35.242.172.58:1935/hls/test_original
                -c:a copy -c:v copy -f rtmp://35.236.33.116:1935/stream/test
}

"""	
def reconfig_nginx_distributor(data):
	res_conf_file = "application " + data['input']['application'] + " {\n"
	res_conf_file += "\t" + "live on;\n"
	res_conf_file += "\t" + "exec ffmpeg -i " + data['input']['proto'] + "://localhost" + ":" + data['input']['port'] + "/" + data['input']['application'] + "/" + data['input']['name'] + "\n"
	for p in data['outputs']:
		res_conf_file += "\t\t"	+ "-c:a copy -c:v copy"
		if p['proto'] == "rtmp":
			res_conf_file += " -f flv "
		res_conf_file += p['proto'] + "://" + p['ip'] + ":" + p['port'] + "/" + p['application'] + "/" + p['name'] 
		try:
                	res_conf_file += "_" + p['variant'] + "\n"
		except KeyError:
			res_conf_file += "\n"
	res_conf_file = res_conf_file[:-1]
	res_conf_file += ";\n"
	res_conf_file += "}\n"
	if verbose:
		print("conf = {}".format(res_conf_file))
	with open(os.path.join('/etc/nginx/app-available/',data['input']['application']), "w") as file1:
    		file1.write(res_conf_file)
	## make link and reload nginx
	src = '/etc/nginx/app-available/' + data['input']['application']
	dst = '/etc/nginx/app-enabled/' + data['input']['application']
	# This creates a symbolic link on python in tmp directory
	try:
    		os.remove(dst)
	except OSError:
    		pass
	os.symlink(src, dst)
	cmd = '/bin/systemctl reload nginx.service'
	proc = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE)
	proc.communicate()
	return 0

def callback(ch, method, properties, body):
	print(" [x] Received config ..")
	try:
		data = json.loads(body.decode('utf-8'))
	except TypeError:
		print("Unknow commands .. not json")
		return 3
	if data['command'] == 'config':
		if data['type'] == 'distributor':
			res = reconfig_nginx_distributor(data)
			return res 
		elif data['type'] == 'transcoder':
			res = reconfig_nginx_transcoder(data)
			return res
		elif data['type'] == 'storage':
			res = reconfig_nginx_storage(data)
			return res
		else:
			print("Undefined type node.")
			return 2

channel.queue_declare(queue=enode)
channel.basic_consume(callback,
                      queue=enode,
                      no_ack=True)

print('[*] Waiting for task. To exit press CTRL+C')
channel.start_consuming()
