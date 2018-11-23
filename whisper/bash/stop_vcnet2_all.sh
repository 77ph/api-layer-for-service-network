#!/bin/bash
for V in $( screen -ls) 
do  
if [[ $V =~ "geth"  ]]  
        then screen -S $V -X quit  
fi  
done

