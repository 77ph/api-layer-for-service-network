sudo add-apt-repository ppa:jonathonf/python-3.6
sudo apt-get update
sudo apt-get install python3.6
python3.6 -V
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.5 1
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 2
sudo update-alternatives --config python3
sudo apt-get remove python3-pip
sudo apt-get install python3-pip
sudo apt-get install python3.6-dev
pip3 install web3

