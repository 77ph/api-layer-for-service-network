#!/usr/bin/env python3
"""
    A pure python rabbitmq send a task to query.
    ./t45_send.py task.json
    task.json
    [{ "enode":"..00", "task":"command.json"},{}]

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

credentials = pika.PlainCredentials('andrey', '1234567890qw')
parameters = pika.ConnectionParameters("10.168.0.3", 5672, '/', credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

tasklist = sys.argv[1]

with open(tasklist) as json_file:  
	data = json.load(json_file)
	for p in data['tasks']:
		print("{} {}".format(p['enode'],p['command']))
		with open(p['command']) as json_file:
			msg = json.load(json_file)
		msg = json.dumps(msg)
		channel.queue_declare(queue=p['enode'])
		channel.basic_publish(exchange='',
                      routing_key=p['enode'],
                      body=msg)
		print("[x] Sent {} to queue {}".format(msg,p['enode']))

connection.close()

