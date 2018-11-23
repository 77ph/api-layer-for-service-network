#!/usr/bin/env python3

"""
    A pure python whisper ping daemon implementation using web3.py and geth 1.8.x.
    ./t4_whisper_genpub.py RPCport
    RPCport
    example: ./t4_whisper_send.py 8502
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

verbose = 1

print("Gen PubKey whisper \n")

data = {}  
data['address-node'] = [] 


for i in range(int(sys.argv[1]), int(sys.argv[2])):
	print(i)
	RPCport = str(i)
	url = "http://localhost:" + RPCport
	my_provider = Web3.HTTPProvider(url)
	w3 = Web3(my_provider)
	w3.middleware_stack.inject(geth_poa_middleware, layer=0)
	verbose = 1
	#logging.basicConfig(level=logging.DEBUG,format='(%(threadName)-9s) %(message)s',)
	if verbose:
		connected = w3.isConnected()
		node = w3.version.node
		print('Connected status {0} with node: "{1}!"'.format(connected, node))
	ms = shh.Shh(w3)
	print('version shh: ', ms.version)

	keyPairId = ms.newKeyPair()
	PubKey  = ms.getPublicKey(keyPairId)
	address = w3.eth.coinbase
	print('coinbase: {} {}'.format(address,len(address)))
	print('keyPairId: {} {}'.format(keyPairId,len(keyPairId)))
	print('PubKey: {} {}'.format(PubKey,len(PubKey)))
	print('Know privateKey {}'.format(ms.hasKeyPair('310872b97005ae098ec6f3d9ec35794c8ace205ea3b4bcd689123f9c90331353')))

	data['address-node'].append({  
    		'address': address,
    		'keyPairId': keyPairId,
    		'PubKey': PubKey
	})

with open('t4.json', 'w') as outfile:  
	json.dump(data, outfile)
