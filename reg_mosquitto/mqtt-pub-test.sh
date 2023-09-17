#!/bin/bash

#require:
# sudo apt-get install mosquitto-clients

usage () {
  echo 'Usage:'
  echo $0' <server> <topic> <message>'
  exit
}

if [ $# -ne 3 ]; then
    usage
fi

# Publish Data
server=$1
topic=$2
message=$3
 
mosquitto_pub -h $server -t $topic -m $message
