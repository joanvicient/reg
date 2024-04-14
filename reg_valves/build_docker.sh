#!/bin/bash

cd "$(dirname "$0")"
cd ..

ls -la

docker build -t jvicient/reg_valves -f reg_valves/Dockerfile .
