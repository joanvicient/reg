#!/bin/bash

usage () {
  echo 'Usage:'
  echo $0' <docker|dir>: build project and run it'
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

if [ $# -eq 1 ]; then
    #docker run -it --rm -p 8080:$8080 jvicient/$project
    echo "Run with: docker run -it --rm -p 8080:8080 jvicient/$project"
elif [ $# -eq 2 ]; then
    tagVersion=jvicient/$project:$2
    docker build -t $tagVersion -f $docker_file .

    docker push $tagLatest
    docker push $tagVersion
else
    usage
fi
