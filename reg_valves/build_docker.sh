#!/bin/bash

cd "$(dirname "$0")"
cd ..

ls -la

docker build -t jvicient/reg_valves -f reg_valves/Dockerfile .

# run it executing:
# docker run -p 5001:5001 jvicient/reg_valves
#
# push
# docker push jvicient/reg_valves:latest
