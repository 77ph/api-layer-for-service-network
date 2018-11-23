#!/usr/bin/env python3
"""
    A pure python read a task via AMQP from query and create a docker cointainer/reconfig nginx in container.
    ./t5_read.py node_id
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
import docker as docker_sdk

credentials = pika.PlainCredentials('andrey', '1234567890qw')
parameters = pika.ConnectionParameters("10.168.0.2", 5672, '/', credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

enode = sys.argv[1]
verbose = 1


"""
Ref: 
"apiVersion": "1.00",
"typeApi": "private",
"command": "pipeline" link: pipleline-with-commands-internal.json

{
	"command": "config",
	"type": "transcoder",
	"nginx-rtmp-core": {
	"listen": "1935",
		"application": "0200000000000000000001"
	},
	"nginx-rtmp-live": {
		"live": "on"
        },
	"ffmpeg-rtmp": {
		"output": {
			"application": "0200000000000000000001",
			"variant": "_480p",
			"codec": "libx264",
			"bitrate": "1000000",
			"resolution": "1280x720",
			"ip": "35.197.4.197",
			"failover_ip": "35.197.4.198"
                        }
	}
}
to
application stream {
        live on;
        exec ffmpeg -i rtmp://localhost:1935/0200000000000000000001/0200000000000000000001
                -vcodec libx264 -vf scale=854x480 -b:v 1000000 -f flv rtmp://35.197.4.197:1935/0200000000000000000001/0200000000000000000001_480p;
}

failover_ip now ignored.
"""
def reconfig_nginx_transcoder(data):
	res_conf_file = "application " + data['nginx-rtmp-core']['application'] + " {\n"
	res_conf_file += "\t" + "live on;\n"
	res_conf_file += "\t" + "exec ffmpeg -i rtmp://localhost:" + data['nginx-rtmp-core']['listen'] + "/" + data['nginx-rtmp-core']['application'] + "/" + data['nginx-rtmp-core']['application'] + "\n"
	res_conf_file += "\t\t" + "-vcodec " + data['ffmpeg-rtmp']['output']['codec'] + " -b:v " + data['ffmpeg-rtmp']['output']['bitrate'] + " -vf scale=" + data['ffmpeg-rtmp']['output']['resolution']
	res_conf_file += " -f flv "
	res_conf_file += "rtmp://" + data['ffmpeg-rtmp']['output']['ip'] + ":" + data['nginx-rtmp-core']['listen'] + "/" + data['ffmpeg-rtmp']['output']['application'] + "/" + data['ffmpeg-rtmp']['output']['application'] 
	try:
		res_conf_file += data['ffmpeg-rtmp']['output']['variant'] + ";\n"
	except KeyError:
		res_conf_file += ";\n"
	res_conf_file += "}\n"
	if verbose:
		print("conf = {}".format(res_conf_file))
	with open(os.path.join('/opt/nginx/app-enabled/',data['nginx-rtmp-core']['application']), "w") as file1:
    		file1.write(res_conf_file)
	## reload nginx
	cmd = 'sudo docker container exec transcoder /opt/nginx/sbin/nginx -s reload'
	proc = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE)
	proc.communicate()
	return 0

"""
Json file to nginx config and reload.
{
	"command": "config",
        "type": "storage",
        "nginx-rtmp-core": {
		"listen": "1935",
               	"application": "0200000000000000000001"
                 },
        "nginx-rtmp-live": {
        	"live": "on"
        },
        "nginx-rtmp-hls": {
        	"hls_fragment": "5",
                "hls_playlist_length": "30",
		"hls_fragment_naming": "timestamp",
                "hls_fragment_naming_granularity": "2",
                "hls_fragment_slicing": "aligned",
                "hls_variant": [{
                	"variant": "_4k",
                        "params": "BANDWIDTH=50000000,RESOLUTION=3840x2160"
                  	}, {
                        "variant": "_1080p",
                        "params": "BANDWIDTH=6000000,RESOLUTION=1920x1080"
                        }, {
                        "variant": "_720p",
                        "params": "BANDWIDTH=3000000,RESOLUTION=1280x720"
                        }, {
                        "variant": "480",
                        "params": "BANDWIDTH=1000000,RESOLUTION=854x480"
                         }]
                }
}

to
        application 0200000000000000000001 {
            live on;
            hls on;
            hls_fragment 5s;
	    hls_playlist_length 30;
	    hls_fragment_naming timestamp;
	    hls_fragment_naming_granularity 2;
	    hls_fragment_slicing aligned;
            hls_path /opt/data/0200000000000000000001;
            hls_variant _480 BANDWIDTH=1000000,RESOLUTION=854x480;
            hls_variant _720 BANDWIDTH=3000000,RESOLUTION=1280x720;
            hls_variant _1080 BANDWIDTH=6000000,RESOLUTION=1920x1080;
            hls_variant _4k BANDWIDTH=50000000,RESOLUTION=3840x2160;
		
        }

"""
def reconfig_nginx_storage(data):
	hls_path="/opt/data/" + data["nginx-rtmp-core"]["application"] ## fixed
	res_conf_file = "application " + data["nginx-rtmp-core"]["application"] + " {\n"
	app=data["nginx-rtmp-core"]["application"]
	res_conf_file += "\t" + "live on;\n"
	res_conf_file += "\t" + "hls on;\n"
	try:
		res_conf_file += "\t" + "hls_fragment " +  data["nginx-rtmp-hls"]["hls_fragment"] +"s;\n"
	except KeyError:
		res_conf_file += "\t" + "hls_fragment 5s;\n"
	try:	
		res_conf_file += "\t" + "hls_playlist_length " +  data["nginx-rtmp-hls"]["hls_playlist_length"] +";\n"    
	except KeyError:
		res_conf_file += "\t" + "hls_playlist_length 30;\n"
	try:
		res_conf_file += "\t" + "hls_fragment_naming " +  data["nginx-rtmp-hls"]["hls_fragment_naming"] +";\n"     
	except KeyError:
		res_conf_file += "\t" + "hls_fragment_naming  timestamp;\n"
	try:
		res_conf_file += "\t" + "hls_fragment_naming_granularity " +  data["nginx-rtmp-hls"]["hls_fragment_naming_granularity"] +";\n"     
	except KeyError:
		res_conf_file += "\t" + "hls_fragment_naming_granularity 2;\n"
	try:
		res_conf_file += "\t" + "hls_fragment_slicing " +  data["nginx-rtmp-hls"]["hls_fragment_slicing"] +";\n"     
	except KeyError:
		res_conf_file += "\t" + "hls_fragment_slicing aligned;\n"
	res_conf_file += "\t" + "hls_path " + hls_path + ";\n"
	for p in data["nginx-rtmp-hls"]["hls_variant"]:
		res_conf_file += "\t"	+ "hls_variant " + p['variant'] + " " + p['params'] + ";\n" 
	res_conf_file += "}\n"
	if verbose:
		print("conf = {}".format(res_conf_file))
	with open(os.path.join('/opt/nginx/app-enabled/',app), "w") as file1:
    		file1.write(res_conf_file)
	## clear data and reload nginx
	if not os.path.exists(hls_path):
		os.makedirs(hls_path)
	res_conf_file = "server {\n"
	res_conf_file += "listen 80;\n"
	res_conf_file += "\tlocation /" + data["nginx-rtmp-core"]["application"] + "{\n"
	res_conf_file += "\t\tadd_header Cache-Control no-cache;\n"
	res_conf_file += "\t\tadd_header 'Access-Control-Allow-Origin' '*' always;\n"
	res_conf_file += "\t\tadd_header 'Access-Control-Expose-Headers' 'Content-Length';\n"
	res_conf_file += "\t\tif ($request_method = 'OPTIONS') {\n"
	res_conf_file += "\t\t\tadd_header 'Access-Control-Allow-Origin' '*';\n"
	res_conf_file += "\t\t\tadd_header 'Access-Control-Max-Age' 1728000;\n"
	res_conf_file += "\t\t\tadd_header 'Content-Type' 'text/plain charset=UTF-8';\n"
	res_conf_file += "\t\t\tadd_header 'Content-Length' 0;\n"
	res_conf_file += "\t\t\treturn 204;\n"
	res_conf_file += "\t\t}\n"
	res_conf_file += "\t\ttypes {\n"
	res_conf_file += "\t\t\tapplication/vnd.apple.mpegurl m3u8;\n";
	res_conf_file += "\t\t\tvideo/mp2t ts;\n"
	res_conf_file += "\t\t}\n"
	res_conf_file += "\troot /opt/data/;\n"
	res_conf_file += "\t}\n"
	res_conf_file += "}\n"
	with open(os.path.join('/opt/nginx/sites-enabled/',app), "w") as file1:
		file1.write(res_conf_file)
	cmd = 'sudo docker container exec storage /opt/nginx/sbin/nginx -s reload'
	proc = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE)
	proc.communicate()
	return 0

"""
Json command to nginx config and reload.
{
	"command": "config",
	"type": "distributor",
	"nginx-rtmp-core": {
		"listen": "1935",
		"application": "0200000000000000000001"
	},
	"nginx-rtmp-live": {
		"live": "on"
        },	
	"ffmpeg-rtmp": {
		"outputs": [{
                	"variant": "_4k",
                       	"ip": "35.242.172.58",
                        "failover_ip": "35.242.172.59"
                        },
                        {
			"ip": "35.233.205.84",
                        "failover_ip": "35.233.205.85"
                        },
                   	{
                        "ip": "35.197.27.59",
                        "failover_ip": "35.197.27.60"
                       	},
                        {
                        "ip": "35.197.4.197",
                        "failover_ip": "35.197.4.198"
                        }
                        ]
       }
}

to
application 0200000000000000000001 {
        live on;
        exec ffmpeg -i rtmp://localhost:1935/0200000000000000000001/0200000000000000000001
                -c:a copy -c:v copy -f rtmp://35.242.172.58:1935/0200000000000000000001/0200000000000000000001_4k
                -c:a copy -c:v copy -f rtmp://35.233.205.84:1935/0200000000000000000001/0200000000000000000001
		-c:a copy -c:v copy -f rtmp://35.197.27.59:1935/0200000000000000000001/0200000000000000000001
		-c:a copy -c:v copy -f rtmp://35.197.4.197:1935/0200000000000000000001/0200000000000000000001
}


failover_ip now ignored.
"""	
def reconfig_nginx_distributor(data):
	res_conf_file = "application " + data['nginx-rtmp-core']['application'] + " {\n"
	res_conf_file += "\t" + "live on;\n"
	res_conf_file += "\t" + "exec ffmpeg -i rtmp://localhost" + ":" + data['nginx-rtmp-core']['listen'] + "/" + data['nginx-rtmp-core']['application'] + "/" + data['nginx-rtmp-core']['application'] + "\n"
	for p in data['ffmpeg-rtmp']['outputs']:
		res_conf_file += "\t\t"	+ "-c:a copy -c:v copy"
		res_conf_file += " -f flv "
		res_conf_file += "rtmp://" + p['ip'] + ":" + data['nginx-rtmp-core']['listen'] + "/" + data['nginx-rtmp-core']['application'] + "/" + data['nginx-rtmp-core']['application']
		try:
                	res_conf_file += p['variant'] + "\n"
		except KeyError:
			res_conf_file += "\n"
	res_conf_file = res_conf_file[:-1]
	res_conf_file += ";\n"
	res_conf_file += "}\n"
	if verbose:
		print("conf = {}".format(res_conf_file))
	with open(os.path.join('/opt/nginx/app-enabled/',data['nginx-rtmp-core']['application']), "w") as file1:
    		file1.write(res_conf_file)
	cmd = 'sudo docker container exec distributor /opt/nginx/sbin/nginx -s reload'
	proc = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE)
	proc.communicate()
	return 0

"""
Json command to nginx create in docker. version 0.1
{
	"_comments": "version 1.0 API. Top level describe ref: https://docs.google.com/document/d/1fFYMT2GRLFBQrtF0fltHrq_-3tciqQ6-fT_43CoPBS0, former t5_task_gen.json",
        "apiVersion": "1.00",
        "typeApi": "private",
        "command": "node",
        "subcommand": "create",
        "params": "distributor",
        "node_id": "88aee28aa0a28177d2c676bfafda48d03ff44eb8",
        "spec": {
                "containers":
                        { 
                                "image": "77phnet/nginx-rtmp",
                                "ports": {"1935":"1935","80":"8080"},
                                "volume-mounts": {
                                	"/opt/nginx/nginx.conf": "/opt/nginx/nginx.conf",
                                	"/opt/nginx/app-enabled": "/opt/nginx/app-enabled",
                                	"/opt/nginx/sites-enabled": "/opt/nginx/sites-enabled",
					"/opt/data": "/opt/data"
                                }	
                        }
        }
}
"""
def nginx_node_create(data):
	cmd = './prepare-container-node.sh'
	proc = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE)
	proc.communicate()
	myimage = data["spec"]["containers"]["image"]
	vol = data["spec"]["containers"]["volume-mounts"]
	portlist = {}
	portlist.update(data["spec"]["containers"]["ports"])
	### hardcore now volumes .. fix? volumes now is staic binded
	if data["spec"]["containers"]["volume-mounts"]:
		myvolumes = {}
		myvolumes = {"/opt/nginx/nginx.conf":{"bind":"/opt/nginx/nginx.conf", "mode":"ro"}, 
			"/opt/nginx/app-enabled": {"bind":"/opt/nginx/app-enabled","mode":"ro"},
			"/opt/nginx/sites-enabled": {"bind":"/opt/nginx/sites-enabled","mode":"ro"},
			"/opt/data": {"bind":"/opt/data","mode":"rw"}}
		container = docker.containers.run(image=myimage,command='/opt/nginx/sbin/nginx',name=data["params"],ports=portlist,
			volumes=myvolumes,
		detach=True,auto_remove=True)
	else:
		container = docker.containers.run(image=myimage,command='/opt/nginx/sbin/nginx',name=data["params"],ports=portlist,detach=True,auto_remove=True)
	print("Container status: {}".format(container.status))
	return 0

def callback(ch, method, properties, body):
	print(" [x] Received data for nginx config or node create command ..")
	try:
		data = json.loads(body.decode('utf-8'))
	except TypeError:
		print("Unknow commands .. not json")
		return 3
	if data['command'] == 'config':
		res = 1
		if data['type'] == 'distributor':
			for container in docker.containers.list():
				if container.name == "distributor":
					res = reconfig_nginx_distributor(data)
					break
			return res 
		elif data['type'] == 'transcoder':
			for container in docker.containers.list():
				if container.name == "transcoder":
					res = reconfig_nginx_transcoder(data)
					break
			return res
		elif data['type'] == 'storage':
			for container in docker.containers.list():
				if container.name == "storage":
					res = reconfig_nginx_storage(data)
					break
			return res
		else:
			print("Undefined type node.")
			return 2
	if data['command'] == 'node':
		if data['subcommand'] == 'create':
			res = nginx_node_create(data)
			return res
	return 2

docker = docker_sdk.from_env()
channel.queue_declare(queue=enode)
channel.basic_consume(callback,
                      queue=enode,
                      no_ack=True)

print('[*] Waiting for task. To exit press CTRL+C')
channel.start_consuming()

