#!/bin/bash

cd "$(dirname "$0")"
cd ..

ls -la

docker build -t jvicient/reg_watchdog -f reg_watchdog/Dockerfile .

# run it executing:
# docker run jvicient/reg_watchdog
#
# push to dockerhub:
# docker push jvicient/reg_watchdog:latest
