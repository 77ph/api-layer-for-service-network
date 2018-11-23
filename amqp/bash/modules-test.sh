#!/bin/bash

sudo apt install -y timelimit > /dev/null 2>&1

which docker > /dev/null 2>&1

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

echo "rollback to zero state"
sudo killall python3 > /dev/null 2>&1
sudo docker kill transcoder > /dev/null 2>&1
sudo docker kill distributor > /dev/null 2>&1
sudo docker kill storage > /dev/null 2>&1
sudo docker rm -f transcoder > /dev/null 2>&1
sudo docker rm -f distributor > /dev/null 2>&1
sudo docker rm -f storage > /dev/null 2>&1
sudo docker rm -f tmp-nginx-container > /dev/null 2>&1

if [ -d /opt/nginx ]; then
	sudo rm -rf /opt/nginx/ > /dev/null 2>&1
	sudo rm -rf /opt/data/ > /dev/null 2>&1
fi

sudo docker pull 77phnet/nginx-rtmp > /dev/null 2>&1
sudo docker run -d -p 1935:1935 -p 8080:80 --name tmp-nginx-container --rm 77phnet/nginx-rtmp > /dev/null 2>&1
sudo docker cp tmp-nginx-container:/opt/nginx/nginx.conf test/nginx.conf
sudo docker rm -f tmp-nginx-container > /dev/null 2>&1

#State before test
echo "State before test:"
sudo docker ps
ls -al /opt/nginx/
echo ""
#

# test distributor
jobid="0200000000000000000001"
nodeid="1d94baec6903bd722953d1111d3b03ea3fa99378"
role="distributor"
echo "TEST #1. Create ${role} node. node_id ${nodeid}"
./t5_send.py test/node_create-public-distributor.json > /dev/null 2>&1

if [ $? -eq 0 ]
then
	echo "Send task to query ${nodeid}. Step pass"
else
	echo "Send task to query ${nodeid}. Step fail"
fi
echo "Waiting 15s"
sudo killall python3 > /dev/null 2>&1
sudo timelimit -S 9 -s 9 -t 15 -T 15 sudo ./t5_read.py ${nodeid} > /dev/null 2>&1
sudo killall python3 > /dev/null 2>&1

c=$(sudo docker ps -a | grep ${role} | awk '{print $1}')
if [ -n ${c} ] 
then
	echo "Task received and container created. Step pass"
	sudo docker ps -a | grep ${role}
else
	echo "Task received and container created. Step fail"
fi 

if cmp -s test/nginx.conf /opt/nginx/nginx.conf
then
	echo "The files match test/nginx.conf and /opt/nginx/nginx.conf. Step pass"
else
	echo "The files are different test/nginx.conf and /opt/nginx/nginx.conf. Step fail"

fi 

echo "TEST #2. Pipline to ${role} node. jobid ${jobid}. node_id ${nodeid}"
./t5_send.py test/pipeline-with-commands.json > /dev/null 2>&1

if [ $? -eq 0 ]
then
	echo "Send pipline to query ${nodeid}. Step pass"
else
	echo "Send pipline to query ${nodeid}. Step fail"
fi
echo "Waiting 15s"
sudo killall python3 > /dev/null 2>&1
sudo timelimit -S 9 -s 9 -T 15 -t 15 sudo ./t5_read.py ${nodeid} > /dev/null 2>&1
sudo killall python3 > /dev/null 2>&1

c=$(sudo docker ps -a --filter="name=nginx" -q)
if [ -n ${c} ] 
then
	echo "Task received and app created. Step pass"
	sudo docker ps -a --filter="name=nginx" -q
else
	echo "Task received and app created. Step fail"
fi 

if cmp -s test/distributor-app.conf /opt/nginx/app-enabled/${jobid}
then
	echo "The files match test/distributor-app.conf and /opt/nginx/app-enabled/${jobid}. Step pass"
else
	echo "The files are different test/distributor-app.conf and /opt/nginx/app-enabled/${jobid}. Step fail"
	diff test/distributor-app.conf /opt/nginx/app-enabled/${jobid}
fi

echo "rollback to zero state"
sudo killall python3 > /dev/null 2>&1
sudo docker kill transcoder > /dev/null 2>&1
sudo docker kill distributor > /dev/null 2>&1
sudo docker kill storage > /dev/null 2>&1
sudo docker rm -f transcoder > /dev/null 2>&1
sudo docker rm -f distributor > /dev/null 2>&1
sudo docker rm -f storage > /dev/null 2>&1
sudo docker rm -f tmp-nginx-container > /dev/null 2>&1

if [ -d /opt/nginx ]; then
	sudo rm -rf /opt/nginx/ > /dev/null 2>&1
	sudo rm -rf /opt/data/ > /dev/null 2>&1
fi

sudo docker pull 77phnet/nginx-rtmp > /dev/null 2>&1
sudo docker run -d -p 1935:1935 -p 8080:80 --name tmp-nginx-container --rm 77phnet/nginx-rtmp > /dev/null 2>&1
sudo docker cp tmp-nginx-container:/opt/nginx/nginx.conf test/nginx.conf
sudo docker rm -f tmp-nginx-container > /dev/null 2>&1

# test transcoder
jobid="0200000000000000000001"
nodeid="88aee28aa0a28177d2c676bfafda48d03ff44eb8"
role="transcoder"
echo "TEST #3. Create ${role} node. node_id ${nodeid}"
./t5_send.py test/node_create-public-transcoder.json > /dev/null 2>&1

if [ $? -eq 0 ]
then
	echo "Send task to query ${nodeid}. Step pass"
else
	echo "Send task to query ${nodeid}. Step fail"
fi
echo "Waiting 15s"
sudo killall python3 > /dev/null 2>&1
sudo timelimit -S 9 -s 9 -t 15 -T 15 sudo ./t5_read.py ${nodeid} > /dev/null 2>&1
sudo killall python3 > /dev/null 2>&1

c=$(sudo docker ps -a | grep ${role} | awk '{print $1}')
if [ -n ${c} ] 
then
	echo "Task received and container created. Step pass"
	sudo docker ps -a | grep ${role}
else
	echo "Task received and container created. Step fail"
fi 

if cmp -s test/nginx.conf /opt/nginx/nginx.conf
then
	echo "The files match test/nginx.conf and /opt/nginx/nginx.conf. Step pass"
else
	echo "The files are different test/nginx.conf and /opt/nginx/nginx.conf. Step fail"

fi 

echo "TEST #4. Pipline to ${role} node. jobid ${jobid}. node_id ${nodeid}"
./t5_send.py test/pipeline-with-commands.json > /dev/null 2>&1

if [ $? -eq 0 ]
then
	echo "Send pipline to query ${nodeid}. Step pass"
else
	echo "Send pipline to query ${nodeid}. Step fail"
fi
echo "Waiting 15s"
sudo killall python3 > /dev/null 2>&1
sudo timelimit -S 9 -s 9 -T 15 -t 15 sudo ./t5_read.py ${nodeid} > /dev/null 2>&1
sudo killall python3 > /dev/null 2>&1

c=$(sudo docker ps -a --filter="name=nginx" -q)
if [ -n ${c} ] 
then
	echo "Task received and app created. Step pass"
	sudo docker ps -a --filter="name=nginx" -q
else
	echo "Task received and app created. Step fail"
fi 

if cmp -s test/transcoder-app.conf /opt/nginx/app-enabled/${jobid}
then
	echo "The files match test/transcoder-app.conf and /opt/nginx/app-enabled/${jobid}. Step pass"
else
	echo "The files are different test/transcoder-app.conf and /opt/nginx/app-enabled/${jobid}. Step fail"
	diff test/transcoder-app.conf /opt/nginx/app-enabled/${jobid}
fi

echo "rollback to zero state"
sudo killall python3 > /dev/null 2>&1
sudo docker kill transcoder > /dev/null 2>&1
sudo docker kill distributor > /dev/null 2>&1
sudo docker kill storage > /dev/null 2>&1
sudo docker rm -f transcoder > /dev/null 2>&1
sudo docker rm -f distributor > /dev/null 2>&1
sudo docker rm -f storage > /dev/null 2>&1
sudo docker rm -f tmp-nginx-container > /dev/null 2>&1

if [ -d /opt/nginx ]; then
	sudo rm -rf /opt/nginx/ > /dev/null 2>&1
	sudo rm -rf /opt/data/ > /dev/null 2>&1
fi

sudo docker pull 77phnet/nginx-rtmp > /dev/null 2>&1
sudo docker run -d -p 1935:1935 -p 8080:80 --name tmp-nginx-container --rm 77phnet/nginx-rtmp > /dev/null 2>&1
sudo docker cp tmp-nginx-container:/opt/nginx/nginx.conf test/nginx.conf
sudo docker rm -f tmp-nginx-container > /dev/null 2>&1

# test storage
jobid="0200000000000000000001"
nodeid="2f45731160c02f69cad1ff8ab9a48492dc3b2022"
role="storage"
echo "TEST #5. Create ${role} node. node_id ${nodeid}"
./t5_send.py test/node_create-public-storage.json > /dev/null 2>&1

if [ $? -eq 0 ]
then
	echo "Send task to query ${nodeid}. Step pass"
else
	echo "Send task to query ${nodeid}. Step fail"
fi
echo "Waiting 15s"
sudo killall python3 > /dev/null 2>&1
sudo timelimit -S 9 -s 9 -t 15 -T 15 sudo ./t5_read.py ${nodeid} > /dev/null 2>&1
sudo killall python3 > /dev/null 2>&1

c=$(sudo docker ps -a | grep ${role} | awk '{print $1}')
if [ -n ${c} ] 
then
	echo "Task received and container created. Step pass"
	sudo docker ps -a | grep ${role}
else
	echo "Task received and container created. Step fail"
fi 

if cmp -s test/nginx.conf /opt/nginx/nginx.conf
then
	echo "The files match test/nginx.conf and /opt/nginx/nginx.conf. Step pass"
else
	echo "The files are different test/nginx.conf and /opt/nginx/nginx.conf. Step fail"

fi 

echo "TEST #6. Pipline to ${role} node. jobid ${jobid}. node_id ${nodeid}"
./t5_send.py test/pipeline-with-commands.json > /dev/null 2>&1

if [ $? -eq 0 ]
then
	echo "Send pipline to query ${nodeid}. Step pass"
else
	echo "Send pipline to query ${nodeid}. Step fail"
fi
echo "Waiting 15s"
sudo killall python3 > /dev/null 2>&1
sudo timelimit -S 9 -s 9 -T 15 -t 15 sudo ./t5_read.py ${nodeid} > /dev/null 2>&1
sudo killall python3 > /dev/null 2>&1

c=$(sudo docker ps -a --filter="name=nginx" -q)
if [ -n ${c} ] 
then
	echo "Task received and app created. Step pass"
	sudo docker ps -a --filter="name=nginx" -q
else
	echo "Task received and app created. Step fail"
fi 

if cmp -s test/storage-app.conf /opt/nginx/app-enabled/${jobid}
then
	echo "The files match test/storage-app.conf and /opt/nginx/app-enabled/${jobid}. Step pass"
else
	echo "The files are different test/storage-app.conf and /opt/nginx/app-enabled/${jobid}. Step fail"
	diff test/storage-app.conf /opt/nginx/app-enabled/${jobid}
fi

