#!/usr/bin/env python3

"""
    A pure python whisper ping daemon implementation using web3.py and geth 1.8.x.
    ./t4_whisper_rec.py RPCport
    RPCport
    example: ./t4_whisper_rec.py 8502
    listener topic: b'0080'
    topic at client side: b'0081'
"""
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

from web3 import Web3, HTTPProvider, TestRPCProvider, shh
from web3.contract import ConciseContract
from web3.auto import w3
from web3.middleware import geth_poa_middleware


def PseudoARP(address):
	with open('t4.json') as json_file:  
		data = json.load(json_file)
	for p in data['address-node']:
		if(p['address'] == address):
			return p['PubKey'],p['keyPairId']
	return "",""


def parse_mes(mes_pars):
	seq,sender,receiver,body = "","","",""
	try:
		loaded_json = json.loads(mes_pars)
	except TypeError:
		return(rseq,sender,receiver,body)
	try:
		sender = loaded_json['from']
		receiver = loaded_json['to']
		seq = loaded_json['seq']
		body = loaded_json['body']
	except TypeError:
		return(rseq,sender,receiver,body)
	return(seq,sender,receiver,body)

def send_one_packet(sender,receiver,seq,pubKey,topic,msg):
	serilaized = json.dumps({'from':sender,'to':receiver,'seq': seq,'body':msg}, sort_keys=True, indent=3)
	text = serilaized.encode()
	# topic = topic.encode()
	mes_send = ms.post({
        	"pubKey": pubKey,
        	"ttl": 100,
        	"topic": Web3.toHex(topic),
        	"powTarget": 1.0,
        	"powTime": 5,
        	"payload": Web3.toHex(text)
    	})
	if mes_send:
        	return 0
	else:
        	return 1


def wait_ack(myFilter,myaddr,topicsend):
	while True:
		messages = ms.getMessages(myFilter.filter_id)
		for i in range(0, len(messages)):
			print("messages in buffer {} do {}".format(len(messages),i))
			message = messages[i]
			mes_pars = message['payload']
			topic = message['topic']
			timestamp = message['timestamp']
			mes_pars = Web3.toText(mes_pars)
			topic = Web3.toText(topic)
			(rseq,sender,receiver,body) = parse_mes(mes_pars)
			if verbose:
				print("------ receive ack begin -----\n")
				print("threading => {}".format(threading.get_ident()))
				print('message => {}'.format(mes_pars))
				print('topic => {}'.format(topic))
				print('timestamp => {}'.format(timestamp))
				print('parsed rseq {},sender {},receiver {},body {}'.format(rseq,sender,receiver,body))
				print("------ receive nack end -----\n")
				print("send nack to {}".format(sender))		
			# do send here
			receiver = sender
			sender = myaddr
			seq = rseq
			msg = "NACK" + " " + str(seq)
			PubKey,keyPairId = PseudoARP(receiver)
			print("PONG SEQ {} to {}".format(seq,receiver))
			if verbose:
				print("PubKey {} KeyPairId {}".format(PubKey,keyPairId)) 
			d = threading.Thread(name='daemon-nack', target=send_one_packet,args=(sender,receiver,seq,PubKey,topicsend,msg))
			d.daemon = True
			d.start()
		time.sleep(0.01)

RPCport = sys.argv[1]
url = "http://localhost:" + RPCport
my_provider = Web3.HTTPProvider(url)
w3 = Web3(my_provider)
w3.middleware_stack.inject(geth_poa_middleware, layer=0)
verbose = 0
#logging.basicConfig(level=logging.DEBUG,format='(%(threadName)-9s) %(message)s',)

if verbose:
	connected = w3.isConnected()
	node = w3.version.node
	print('Connected status {0} with node: "{1}!"'.format(connected, node))

print("Sending msg via whisper \n")


ms = shh.Shh(w3)
print('version shh: ', ms.version)

timeout = 10.000;
topicsend = b'0081' # send to "port" = 81
topiclisten = b'0080' # wait answer at "port" = 80
myaddr = w3.eth.coinbase
sender = myaddr

PubKey,keyPairId = PseudoARP(myaddr)

myFilter = ms.newMessageFilter({'topic': Web3.toHex(topiclisten),'privateKeyID': keyPairId})
myFilter.poll_interval = 600;

d = threading.Thread(name='daemon', target=wait_ack,args=(myFilter,myaddr,topicsend))
d.daemon = True
d.start()

while True:
	time.sleep(0.02)

waiting = timeout + 0.2
d.join(waiting)
while d.isAlive():
	pass # Busy-wait for keyboard interrupt
print ("\nall - done.")
