#!/bin/bash

if [ -f .env ]; then
    export $(cat .env | xargs)
else
    echo "Error: .env file not found."
fi

if [ -n "$1" ]; then
    python3 reg_telegram.py -l "$1"
else
    python3 reg_telegram.py
fi
