#!/bin/bash

sudo chmod 755 *.sh

for i in 1 2 3 4 5 
do
	echo "Start instance $i"
	screen -d -m -S geth_$i sh start_vcnet2-$i.sh
	sleep 60
done
