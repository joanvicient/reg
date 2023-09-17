#!/bin/bash

usage () {
  echo 'Usage:'
  echo $0' build <docker|dir>'
  echo $0' publish <docker|dir>'
  exit
}

tagname="latest"
if [ $# -ne 2 ]; then
    usage
fi

if [ -d "$2" ]; then
    project=$(basename $2)
    tag=jvicient/$project:latest
    docker_file=$project/Dockerfile
    #echo $docker_file
else
    usage
fi

if [ "$1" = "build" ]; then
    docker build -t $tag - < $docker_file
elif [ "$1" = "publish" ]; then
    docker push jvicient/$project:$tagname
else
    usage
fi
