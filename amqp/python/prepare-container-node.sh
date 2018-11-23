#!/bin/bash

which docker

if [ $? -eq 0 ]
then
	docker --version | grep "Docker version"
	if [ $? -eq 0 ]
	then
        	echo "docker existing" > /dev/null
	else
        	echo "install docker"
		sudo apt-get update
        	sudo apt-get install apt-transport-https ca-certificates curl software-properties-common 
        	curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
        	sudo apt-key fingerprint 0EBFCD88
        	sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" 
        	sudo apt-get update
        	sudo apt-get install -y docker-ce
    	fi
else
    	echo "install docker"
	sudo apt-get update
	sudo apt-get install apt-transport-https ca-certificates curl software-properties-common
	curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
	sudo apt-key fingerprint 0EBFCD88
	sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
	sudo apt-get update
	sudo apt-get install -y docker-ce
fi

if [ -f /opt/nginx/nginx.conf ]; then
	echo "nginx existing"
	exit 0	
fi

sudo mkdir -p /opt/nginx/
sudo mkdir -p /opt/nginx/app-enabled/
sudo mkdir -p /opt/nginx/sites-enabled/
sudo mkdir -p /opt/data/

sudo docker pull 77phnet/nginx-rtmp
sudo docker run -d -p 1935:1935 -p 8080:80 --name tmp-nginx-container --rm 77phnet/nginx-rtmp
sudo docker cp tmp-nginx-container:/opt/nginx/nginx.conf /opt/nginx/nginx.conf
sudo docker rm -f tmp-nginx-container

