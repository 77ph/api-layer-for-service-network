#!/bin/bash


portrpc=8502
hostname=$( hostname )

i=0
echo "Welcome $i t4_whisper_send.py"
screen -d -m -S t4_whisper_send_$i ./t4_whisper_send.py $portrpc 1000000
sleep 5

portrpc=$((portrpc+1))

for i in 1 2 3 4
do
        echo "Welcome $i t4_whisper_rec.py"
	screen -d -m -S t4_whisper_rec_$i ./t4_whisper_rec.py $portrpc > t4_rec_$i.log
        portrpc=$((portrpc+1))
done
