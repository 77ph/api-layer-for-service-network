#!/usr/bin/env python3

"""
    A pure python whisper ping/pong implementation using web3.py and geth 1.8.x with asymetric cryptography algorithms.
    ./t4_whisper_send.py PRCport
    
    t4.json struct :
    {
    "address-node": [
    {
    "address": "0xAd12F90BE5A51163aac69DfeF2AaF9E37C4D1591", 
    "keyPairId": "48e7f279acaf225688e95c2d46ea861c3440b8e208c66f1c16cad2466bc18ac3", 
    "PubKey": "0x0494793ff515cc6fe553ef0283c182d36fc2210dce140b704356486480c385bf5ea2f68e531b6cf9e6894dd2e11ab6a0e56df04c6b11a10b3a40285adf4bef1430"}, {"address": "0x2Eeccf69A28422b4ADfe4c21DDBa3853dd8EBEC5", "keyPairId": "a4b16a71e2cfb4a92660940f96b61334cfccba814f3dab409a1d57e918b58885", "PubKey": "0x04555c4acc1d4abec063f7a9d7d1523c0b3fc639c8dce7632ac32f2b9aed4b47d089f3110c8d7972dabff6d600c77a5c753a712f0d6362448b33da684e629d51db"
    }
    ..
    ]
    }
    list of keypair for nodes.
    
    example: ./t4_whisper_send.py 8502
    topic (pre-defined): b'0080' port for send
    topic (pre-defined): b'0081' port for listen
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

def SizeArpTable():
	with open('t4.json') as json_file:
		data = json.load(json_file)
	count = 0
	for p in data['address-node']:
		count = count + 1
	return count

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

def send_one_packet(count,sender,receiver,seq,pubKey,topic,msg):
	time.sleep(1.00)
	serilaized = json.dumps({'from':sender,'to':receiver,'seq': seq,'body':msg}, sort_keys=True, indent=3)
	text = serilaized.encode()
	mes_send = ms.post({
        	"pubKey": pubKey,
        	"ttl": 100,
        	"topic": Web3.toHex(topic),
        	"powTarget": 1.0,
        	"powTime": 5,
        	"payload": Web3.toHex(text)
    	})
	if mes_send:
		if verbose:
        		print("PING # {0} SEQ {1}.".format(count,seq))
	else:
        	print("PING # {0}. Message not send".format(count))


def wait_nack(myFilter):
	count = 0
	while True:
		messages = ms.getMessages(myFilter.filter_id)
		for i in range(0, len(messages)):
			print("messages in buffer {} do {}".format(len(messages),i))
			message = messages[i]
			mes_pars = message['payload']
			mes_pars = Web3.toText(mes_pars)
			(rseq,sender,receiver,body) = parse_mes(mes_pars)
			if verbose:
				print("PONG [Detail]: Seq in packet {},sender {},receiver {}, total count {}".format(seq, rseq,sender,receiver,count))
			count = count + 1
			totalrseq = seqstat.get(rseq)
			if totalrseq is None:
				totalrseq = 0
			totalrseq = totalrseq + 1
			d = {rseq:totalrseq}
			seqstat.update(d)
			print("PONG from {} SEQ {} totalrseq {} packets".format(sender,rseq,totalrseq))
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

i = 0
timeout = 10.000
topicsend = b'0080' # send to "port" = 80
topiclisten = b'0081' # wait answer at "port" = 81
n = int(sys.argv[2])
myaddr = w3.eth.coinbase
sender = myaddr

PubKey,keyPairId = PseudoARP(myaddr)

### ToDo fix to list in Contract
with open('t4.json') as json_file:
	data = json.load(json_file)


myFilter = ms.newMessageFilter({'topic': Web3.toHex(topiclisten),'privateKeyID': keyPairId})
myFilter.poll_interval = 600;

numnodes = SizeArpTable() 
numnodes = numnodes - 1 ## dont ping self

seqstat = dict()

d = threading.Thread(name='daemon', target=wait_nack,args=(myFilter,))
d.daemon = True
d.start()

while i < n:
	timenow = datetime.datetime.now()
	mymsg = "ACK" + " " + str(int(round(time.time() * 1000000)))
	seq = int(round(time.time() * 1000000))
	print("Send unicast PING SEQ {} to {} nodes".format(seq,numnodes))
	### ToDo to list nodes from Contract
	for p in data['address-node']:
		if(p['address'] != myaddr):
			seqstat.setdefault(seq, 0)
			send_one_packet(i,sender,p['address'],seq,p['PubKey'],topicsend,mymsg)	
	time.sleep(5.00)
	i = i + 1

waiting = timeout + 0.2
d.join(waiting)
while d.isAlive():
	pass # Busy-wait for keyboard interrupt
print("send: {} packets.".format(i))

