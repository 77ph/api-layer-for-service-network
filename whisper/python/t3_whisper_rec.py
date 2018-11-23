import datetime
import json
import web3
import sys
import time
import pprint
import sys
import os
import subprocess

from subprocess import call
from web3 import Web3, HTTPProvider, TestRPCProvider, shh
from web3.contract import ConciseContract
from web3.auto import w3
from web3.middleware import geth_poa_middleware

def start_stop(command):
	count = contract.functions.getCount().call()
	print('Contract count. count records: {0}'.format(count))
	if(command == "start"):
		print("Exec start")
		contract.functions.incrementCounter().transact({'from': w3.eth.coinbase})
		# rc = call("/home/andrey/start_stream.sh")
		rc = 1
		print("Status start {}".format(rc))
		return 1
	print("Exec stop")
	contract.functions.derementCounter().transact({'from': w3.eth.coinbase})
	# rc = call("/home/andrey/stop_stream.sh")
	rc = 0	
	print("Status stop {}".format(rc))
	return 0

verbose = 1
contract_address = "0x986c2a8c3dd8f14eb4dfbec4fb4652cf35e4a756"

#my_provider = Web3.IPCProvider('/home/andrey/vcnet/geth.ipc')
my_provider = Web3.HTTPProvider('http://localhost:8502')
w3 = Web3(my_provider)
w3.middleware_stack.inject(geth_poa_middleware, layer=0)

if verbose:
        connected = w3.isConnected()
        node = w3.version.node
        print('Connected status {0} with node: "{1}!"'.format(connected, node))

with open('Counter2.json') as f:
     ADDCHUNK_ABI = json.load(f)

dbAddress = Web3.toChecksumAddress(contract_address)
contract = w3.eth.contract(address=dbAddress, abi=ADDCHUNK_ABI)


print("Receive msg via whisper \n")




ms = shh.Shh(w3)
print('version shh: ', ms.version)

symKeyID = ms.generateSymKeyFromPassword("shh_secret_pwd")
print('id ===>>>> ', symKeyID)

myFilter = ms.newMessageFilter({'symKeyID': symKeyID})
myFilter.poll_interval = 600;
print('FilterID: ' + myFilter.filter_id)

count = 0
ccount = 0

while True:
	ccount = contract.functions.getCount().call()
	if ccount != count:
		print('Contract count. count records: {}'.format(ccount))
		count = ccount	
	messages = ms.getMessages(myFilter.filter_id)
	if messages != []:
		message = messages[0]
		mes_pars = message['payload']
		topic = message['topic']
		timestamp = message['timestamp']
		topic = Web3.toText(topic)
		content = Web3.toText(mes_pars)
		print('message => {}'.format(content))
		print('topic => {}'.format(topic))
		print('timestamp => {}'.format(timestamp))
		count = contract.functions.getCount().call()
		print('Contract count before {0}. count records: {1}'.format(content,count))
		res = start_stop(content)
	time.sleep(0.3)

