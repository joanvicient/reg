#!/bin/bash

#export TELEGRAM_TOKEN="6407991790:AAHdPyVcL8RyeJV_qOsGQ8KF-WPS6B0EQ8s"
#export TELEGRAM_CHAT_ID="4543843"
#export TELEGRAM_ADMIN_ID="4543843"

export $(cat .env | xargs)
python3 reg_telegram.py -l $1
