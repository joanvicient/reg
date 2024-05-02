#!/bin/bash

cd "$(dirname "$0")"
cd ..

ls -la

docker build -t jvicient/reg_telegram -f reg_telegram/Dockerfile .

# run it
docker run --env-file reg_telegram/.env jvicient/reg_telegram

# push to dockerhub:
# docker push jvicient/reg_telegram:latest
