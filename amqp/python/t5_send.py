#!/usr/bin/env python3
"""
    A pure python rabbitmq send a task to query of node [node_id].
    ./t5_send.py pipeline.json
    pipeline.json
	{
        "_comments": "version 1.0 API. Top level describe ref: https://docs.google.com/document/d/1fFYMT2GRLFBQrtF0fltHrq_-3tciqQ6-fT_43CoPBS0",
        "apiVersion": "1.00",
        "typeApi": "public",
        "pipeline": 
                {
                        "type_source": "file"
			...
	} 

    ./t5_send.py node_create-public.json   

ToDo: t5_send => vcli | API gate

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

"""
{
	"_comments": "version 1.0 API. Top level describe ref: https://docs.google.com/document/d/1fFYMT2GRLFBQrtF0fltHrq_-3tciqQ6-fT_43CoPBS0",
	"apiVersion": "1.00",
        "typeApi": "public",
        "command": "pipeline",
        "subcommand": "start",
	"pipeline": 
		{
			"type_source": "file",
        		"job_id": "0200000000000000000001",
        		"number_of_streams": "3",
        		"source": {
                		"resolution_name": "_4k", 
                		"resolution": "3840x2160",
                		"bitrate": "50000000"
        		},
        		"transcoding": { [
                		{
                        		"resolution_name": "_1080p", 
                        		"resolution": "1920x1080",
                        		"bitrate": "6000000"
                		},
                		{
                        		"resolution_name": "_720p", 
                        		"resolution": "1280x720",
                        		"bitrate": "3000000"
                		},
                		{
                        		"resolution_name": "_480p", 
                        		"resolution": "854x480",
                        		"bitrate": "1000000"
                		}
        			]
        		},
        	"nodes": { [
                	{
                        	"type": "distributor",
                        	"node_id": "1d94baec6903bd722953d1111d3b03ea3fa99378", 
                        	"ip": "35.198.30.225",
                        	"failover_ip": "35.221.152.9"
                	},
                	{
                        	"type": "storage",
                        	"node_id": "2f45731160c02f69cad1ff8ab9a48492dc3b2022", 
                        	"ip": "35.242.172.58",
                        	"failover_ip": "35.242.172.59"
                	},
                	{
                        	"type": "transcoder",
                        	"node_id": "88aee28aa0a28177d2c676bfafda48d03ff44eb8", 
                        	"ip": "35.233.205.84",
                        	"failover_ip": "35.233.205.85" 
                	},
                	{
                        	"type": "transcoder",
                        	"node_id": "d8a9d07b9884d32da3700634aab1d373fffd36ef",
                        	"ip": "35.197.27.59",
                        	"failover_ip": "35.197.27.60"
                	},
                	{
                        	"type": "transcoder",
                        	"node_id": "4586f87cdeb706f037d4cddcac051c04b2f55d16",
                        	"ip": "35.197.4.197",
                        	"failover_ip": "35.197.4.198"
                	}
        		]
        	}
	}
}

to

{
        "_comments": "version 1.0 API. Top level describe ref: https://docs.google.com/document/d/1fFYMT2GRLFBQrtF0fltHrq_-3tciqQ6-fT_43CoPBS0, former t5_task_gen.json",
        "apiVersion": "1.00",
        "typeApi": "private",
        "command": "pipeline",
        "subcommand": "start",
        "pipeline": {
                "tasks": [{
                                "node_id": "1d94baec6903bd722953d1111d3b03ea3fa99378",
                                "msg": {
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
                        },
                        {
                                "node_id": "2f45731160c02f69cad1ff8ab9a48492dc3b2022",
                                "msg": {
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
                        },
                        {
                                "node_id": "88aee28aa0a28177d2c676bfafda48d03ff44eb8",
                                "msg": {
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
                                                        "variant": "_1080p",
                                                        "codec": "libx264",
                                                        "bitrate": "6000000",
                                                        "resolution": "1920x1080",
                                                        "ip": "35.233.205.84",
                                                        "failover_ip": "35.233.205.85"
                                                }
                                        }
                                }
                        },
                        {
                                "node_id": "d8a9d07b9884d32da3700634aab1d373fffd36ef",
                                "msg": {
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
                                                        "variant": "_720p",
                                                        "codec": "libx264",
                                                        "bitrate": "3000000",
                                                        "resolution": "1280x720",
                                                        "ip": "35.197.27.59",
                                                        "failover_ip": "35.197.27.60"
                                                }
                                        }
                                }
                        },
                        {
                                "node_id": "4586f87cdeb706f037d4cddcac051c04b2f55d16",
                                "msg": {
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
                                                        "resolution": "854x480",
                                                        "ip": "35.197.4.197",
                                                        "failover_ip": "35.197.4.198"
                                                }
                                        }
                                }
                        }
                ]
        }
}

"""	
def convertPublicApi2PivatePipeline(data):
	transcoder_c = 0
	json_res = {}	
	json_res['tasks'] = [];
	dataorig = data
	data = data["pipeline"]
	jobid = data['job_id']	
	for p in data['nodes']:
		print("{} {} {}\n".format(p['type'],p['node_id'],p['ip']))
		if(p['type'] == "distributor"):
			item = generate_dist(data)
			json_res['tasks'].append(item)
		if(p['type'] == "storage"):
			item = generate_storage(data)
			json_res['tasks'].append(item)
		if(p['type'] == "transcoder"):
			item = generate_transcoder(data,transcoder_c)
			json_res['tasks'].append(item)
			transcoder_c += 1
	mainres = {}
	mainres.update({"_comments":dataorig["_comments"],"apiVersion":dataorig["apiVersion"],"typeApi":"private","command":dataorig["command"],"subcommand":dataorig["subcommand"],"pipeline":json_res})
	return mainres


def convertPublicApi2PivateNodeCreate(data):
	mainres = {}
	mainres.update({"_comments":data["_comments"],"apiVersion":data["apiVersion"],"typeApi":"private","command":data["command"],"subcommand":data["subcommand"],"params":data["params"],"node_id":data["node_id"],"spec":{"containers":{"image": "77phnet/nginx-rtmp","ports": {"1935":"1935","80":"8080"}, "volume-mounts": {"/opt/nginx/nginx.conf": "/opt/nginx/nginx.conf","/opt/nginx/app-enabled": "/opt/nginx/app-enabled","/opt/nginx/sites-enabled": "/opt/nginx/sites-enabled","/opt/data":"/opt/data"}}}})
	return mainres


def data2ip(data,type,c):
	failover_ip,ip = ("","")
	c1 = 0
	for p in data['nodes']:
		if(p['type'] == type):
			if c >= 0:
				if(c1 == c):
					ip = p['ip']
					try:
						failover_ip = p['failover_ip']
					except KeyError:
						failover_ip = ""
					break
				c1 += 1				
			else:
				ip = p['ip']
				try:
					failover_ip = p['failover_ip']
				except KeyError:
					failover_ip = ""
				break
	return(ip,failover_ip)


def data2nodeid(data,type,c):
	id = ""
	c1 = 0
	for p in data['nodes']:
		if(p['type'] == type):
			if c >= 0:
				if(c1 == c):
					id = p['node_id']
					break
				c1 += 1
			else:
				id = p['node_id']
				break
	return id		

	

def generate_dist(data):
	# print("call generate_dist {}\n".format(data['job_id']))
	o = {}
	o['outputs'] = [];
	ip,failover_ip = data2ip(data,"distributor",-1)
	nodeid = data2nodeid(data,"distributor",-1)
	o['outputs'].append({ "variant": data['source']["resolution_name"], "ip": ip, "failover_ip": failover_ip })
	for p in data['transcoding']:
		ip,failover_ip = data2ip(data,"transcoder",-1)	
		o['outputs'].append({"ip": ip, "failover_ip": failover_ip})
	nginxcore = {}
	nginxcore.update({ "listen": "1935", "application": data["job_id"]})
	subitem = {}
	subitem.update({ "command": "config", "type": "distributor", "nginx-rtmp-core": nginxcore, "nginx-rtmp-live" : { "live": "on" }, "ffmpeg-rtmp": o })
	item = {}
	item.update({ "node_id": nodeid, "msg": subitem })
	return item

def generate_storage(data):
	print("call generate_storage {}\n".format(data['job_id']))
	nodeid = data2nodeid(data,"storage",-1)
	o = {}
	variants = {}
	variants = []
	params = "BANDWIDTH=" + data["source"]["bitrate"] + "," + "RESOLUTION=" +  data["source"]["resolution"]
	variants.append({ "variant": data["source"]["resolution_name"], "params": params })
	for p in data['transcoding']:
		params = "BANDWIDTH=" + p["bitrate"] + "," + "RESOLUTION=" +  p["resolution"]
		variants.append({ "variant": p["resolution_name"], "params": params })
	o = {  "hls_fragment": "5", "hls_playlist_length": "30", "hls_fragment_naming": "timestamp", "hls_fragment_naming_granularity": "2", "hls_fragment_slicing": "aligned", "hls_variant" : variants }
	nginxcore = {}
	nginxcore.update({ "listen": "1935", "application": data["job_id"]})
	subitem = {}
	subitem.update({ "command": "config", "type": "storage", "nginx-rtmp-core": nginxcore, "nginx-rtmp-live" : { "live": "on" }, "nginx-rtmp-hls": o })
	item = {}
	item.update({ "node_id": nodeid, "msg": subitem })
	return item

def generate_transcoder(data,c):
	# print("call generate_transcoder {} {}\n".format(data['job_id'],c))
	nodeid = data2nodeid(data,"transcoder",c)
	c1 = 0
	(ip,failover_ip) = data2ip(data,"storage",-1)
	transcoderdata = {}
	for p in data['transcoding']:
		if(c1 == c):
			transcoderdata = { "application": data['job_id'], "variant": p["resolution_name"], "codec": "libx264", "bitrate": p["bitrate"], "resolution": p["resolution"], "ip": ip, "failover_ip": failover_ip }
			break
		c1 += 1
	item = {}	
	o = {}
	o.update({"output": transcoderdata })
	nginxcore = {}
	nginxcore.update({ "listen": "1935", "application": data["job_id"]})
	subitem = {}
	subitem.update({ "command": "config", "type": "transcoder", "nginx-rtmp-core": nginxcore, "nginx-rtmp-live" : { "live": "on" }, "ffmpeg-rtmp": o })
	item.update({ "node_id": nodeid, "msg": subitem })
	return item




credentials = pika.PlainCredentials('andrey', '1234567890qw')
parameters = pika.ConnectionParameters("10.168.0.2", 5672, '/', credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

tasklist = sys.argv[1]

with open(tasklist) as json_file:  
	data = json.load(json_file)
	if (data['command'] == "pipeline" and data["typeApi"] == "public"):
		data = convertPublicApi2PivatePipeline(data)
		print(data) 
	if data['command'] == "pipeline":
		for p in data["pipeline"]['tasks']:
			msg = json.dumps(p['msg'])
			channel.queue_declare(queue=p['node_id'])
			channel.basic_publish(exchange='',
                      	routing_key=p['node_id'],
                     	 body=msg)
			print("[x] Sent {} to queue {}".format(msg,p['node_id']))
	if data['command'] == "node":
		if (data['command'] == "node" and data["typeApi"] == "public"):
			data = convertPublicApi2PivateNodeCreate(data)
		msg = json.dumps(data)
		channel.queue_declare(queue=data['node_id'])
		channel.basic_publish(exchange='',
                        routing_key=data['node_id'],
                         body=msg)
		print("[x] Sent {} to queue {}".format(msg,data['node_id']))		

connection.close()

