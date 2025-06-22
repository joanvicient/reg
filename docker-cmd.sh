#!/bin/bash

usage () {
  echo 'Usage:'
  echo $0' <docker|dir>: build project'
  echo $0' <docker|dir> <version>: build and publish project'
  exit
}

if [ -d "$1" ]; then
    project=$(basename $1)
    tagLatest=jvicient/$project:latest
    docker_file=$project/Dockerfile
else
    usage
fi

docker build -t $tagLatest -f $docker_file .

if [ $# -eq 2 ]; then
    tagVersion=jvicient/$project:$2
    docker build -t $tagVersion -f $docker_file .

    docker push $tagLatest
    docker push $tagVersion
fi
