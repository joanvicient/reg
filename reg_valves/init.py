#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Check for valves and init db tables.
# To find a valve, there must be a EspEasy firmware with a "Generic  - Dummy device" named "Valves" with a value "<valve_name>:<GPIO>"
#
# requisites:
#   pip3 install mysql-connector-python
#   pip3 install crontab
#
# to run outside docker-compose, it should be run as:
#   DATABASE_IP=<db_server_ip> python3 init.py

from time import sleep
from myMariaDB import DBTables, DBValves
from myESP32 import DiscoverValves, DiscoverWemos
from myTelegram import RegBot
import myCron

# from myTelegram import telegram_bot as telegram


def init():
    print("### Sleep 10 in order to get de MariaDB ready ###")
    sleep(10)

    print("")
    print("### Connecting to Database ###")
    tables = DBTables()
    t = tables.get()
    if len(t) == 0:
        print("Database don't have any table")
        tables.create()
    else:
        print("s'ha trobat les seguents taules: ")
        for table in t:
            print("-" + str(table))

    print("")
    print("### Finding Wemos ###")
    wemosList = DiscoverWemos()

    print("")
    print("### Finding Valves ###")
    ValveList = DiscoverValves(wemosList)

    print("")
    print("### Adding valves to database ###")
    db_valves = DBValves()
    for valve in ValveList:
        db_valves.add(valve)

    print("")
    print("### Enabling Services (cron) ###")
    cron = myCron.myCron()
    cron.set("watering", "/usr/local/bin/python /src/watering.py", "0 * * * *")
    # cron.PrintJobs()

    print("")
    print("### Init Telegram bot ###")
    RegBot()

    print("")
    print("### Infinite loop ###")
    while True:
        sleep(300)

if __name__ == "__main__":
    init()