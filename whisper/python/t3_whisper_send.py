#!/usr/bin/env python3
"""
Send message via whisper using cryptography with symmetric key. Network vcnet2.

./t3_whisper_send.py "start"|"stop"
PoC
"""
import datetime
import json
import web3
import sys
import time
import pprint
import sys
import os

from web3 import Web3, HTTPProvider, TestRPCProvider, shh
from web3.contract import ConciseContract
from web3.auto import w3
from web3.middleware import geth_poa_middleware

verbose = 1

#my_provider = Web3.IPCProvider('/home/andrey/vcnet/geth.ipc')
my_provider = Web3.HTTPProvider('http://localhost:8502')
w3 = Web3(my_provider)
w3.middleware_stack.inject(geth_poa_middleware, layer=0)

if verbose:
	connected = w3.isConnected()
	node = w3.version.node
	print('Connected status {0} with node: "{1}!"'.format(connected, node))

print("Sending msg via whisper \n")


ms = shh.Shh(w3)
print('version shh: ', ms.version)

symKeyID = ms.generateSymKeyFromPassword("shh_secret_pwd")
print('id ===>>>> ', symKeyID)
print(sys.argv[1])
command = sys.argv[1]
command_as_bytes = command.encode()

topic = Web3.toHex(b'1111')
text = command_as_bytes

mes_send = ms.post(
    {
        "symKeyID": symKeyID,
        "ttl": 100,
        "topic": topic,
        "powTarget": 2.0,
        "powTime": 2,
        "payload": Web3.toHex(text)
    }
)
if mes_send:
        print('Message Send')
else:
        print('Message not send')

