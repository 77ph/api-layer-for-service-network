#!/bin/bash
for V in $( screen -ls) 
do  
if [[ $V =~ "whisper"  ]]  
        then screen -S $V -X quit  
fi  
done

