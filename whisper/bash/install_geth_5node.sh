geth_path=$( whereis geth )
if [[ -z $geth_path ]]; then
	sudo apt-get install software-properties-common
	sudo add-apt-repository -y ppa:ethereum/ethereum
	sudo apt-get update
	sudo apt-get install 
fi


echo "123456" > ./password.txt
portcom=30313
portrpc=8502
hostname=$( hostname )

rm -rf ./vcnet2-*
rm -rf start_vc*sh

for i in 1 2 3 4 5
do
	echo "Welcome $i node"
	geth --datadir=./vcnet2-$i/ --password ./password.txt account new > account-$hostname-$i.txt
	geth --datadir ./vcnet2-$i/ init vcnet2.json
	cp ./password.txt ./vcnet2-$i/
	echo "My account $i:"
	acc=$( cat account-$hostname-$i.txt | awk '{ print $2 }' | tr -d { | tr -d })
	echo "geth --datadir vcnet2-$i/ --identity $hostname-$i --verbosity 5 --port $portcom --rpc --rpcaddr 'localhost' --rpcport $portrpc --rpcapi 'personal,db,eth,net,web3,txpool,miner,shh' --networkid 1936 -unlock $acc --bootnodes 'enode://ac65401c4bb561ce2cb0d07fba4055e40c5b1efb65fcaf66613906f1d877781b499404c4d9479054df398367476a61512baa545983deb729d8fd5a4331e4f151@35.203.28.0:30312' --password vcnet2-$i/password.txt --targetgaslimit 23000000 --shh" > start_vcnet2-$i.sh
	chmod 755 start_vcnet2-$i.sh
	# screen -d -m -t nameofwindow sh nameoflaunch.sh
	cat start_vcnet2-$i.sh
	portcom=$((portcom+1))
	portrpc=$((portrpc+1))
done




