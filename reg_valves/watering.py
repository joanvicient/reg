#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from myMariaDB import DBTasks, DBValves
from myESP32 import Valve


def __weekday2dia(day):
    if day == 0:
        return "dl"
    elif day == 1:
        return "dm"
    elif day == 2:
        return "dc"
    elif day == 3:
        return "dj"
    elif day == 4:
        return "dv"
    elif day == 5:
        return "ds"
    elif day == 6:
        return "dg"
    else:
        return ""


if __name__ == "__main__":
    print("watering executed")

    # tenir en compte que es UTC (entre una i dues hores de diferencia)
    ## TODO: hora que toca segons zona geofràfica
    weekday = datetime.now().weekday()
    hour = datetime.now().hour
    tasks = DBTasks().get(__weekday2dia(weekday), hour)
    for task in tasks:
        name = task["valve"]
        duration = task["duration"]
        valve = DBValves().get(name)

        print("Watering " + name + " for " + str(duration) + " seconds")
        valve.water(duration)
