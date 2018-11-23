Some approaches to api control layer for DSN
============================================

**Main objecive**


- choose suitable messaging protocol for control to DSN instances
- define criteria for such protocol

**Abstract Scheme**

![DSN](./docs/dsn.png)

Considered two protocols
- Ethereum wisper
- AMGP (RabbitMQ)

Each of them has its advantages and disadvantages.

**[Wisper protocol](https://github.com/ethereum/go-ethereum/wiki/Whisper)**

Native ethereum messaging protocol, part of official realise

*advantages*

1. decentrilized (not so important for poa network)
2. encrypted messages
3. part of eth api (not need additional software)

*limitations*

1. slow
2. poor and non stable api
3. sync keys security problem


**simple control scheme for videocoin network**

videocoin network consist of set of instances like nginx-rtmp/ffmpeg

![test scheme](./docs/whisper1.png)

**Process description**

- two nodes use geth with shh-api (whisper) on a vcnet2 network
- whisper sender sends messages to the vcnet2 network
- whisper receiver receives messages and turns them into system commands
- the start message starts streaming to ffmpeg / nginx and sends the transaction to the ethereum counter contract, increasing the counter by 1
- the stop message stops streaming to ffmpeg / nginx and sends the transaction to the ethereum counter contract, decreasing the counter by 1










