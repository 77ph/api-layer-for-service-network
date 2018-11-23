#!/usr/bin/env python3
"""
    A rabbitmq send. Hello world exmple.
    ./hello_world_send.py
"""
import pika
credentials = pika.PlainCredentials('andrey', '1234567890qw')
parameters = pika.ConnectionParameters("10.168.0.3", 5672, '/', credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

channel.queue_declare(queue='test')

channel.basic_publish(exchange='',
                      routing_key='test',
                      body='Hello World!')
print(" [x] Sent 'Hello World!'")

connection.close()

