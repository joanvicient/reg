#!/bin/bash

#require:
# sudo apt-get install mosquitto-clients

usage () {
  echo 'Usage:'
  echo $0' <server> <topic>'
  exit
}

if [ $# -ne 2 ]; then
    usage
fi

# Publish Data
server=$1
topic=$2
 
mosquitto_sub -h $server -v -t $topic
