#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from pydantic import BaseModel

class TaskRequest(BaseModel):
    """Pydantic model for task creation requests"""
    valve: str
    hour: int
    week_days: list[str]
    duration: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "valve": "valve1",
                "hour": 12,
                "week_days": ["Monday", "Tuesday"],
                "duration": 10
            }
        }
    }

class Task:
    def __init__(self, valve: str, hour: int, week_days: list[str], duration: int):
        #TODO validate the hour and the week_days
        #provude documentation of how to use the week_days
        self.valve = valve
        self.hour = hour
        self.week_days = week_days
        self.duration = duration

    def is_the_same(self, task: 'Task') -> bool:
        """ Returns True if the task relates to the same valve and hour """
        return self.valve == task.valve and self.hour == task.hour

    def copy_from_task(self, task: 'Task'):
        self.valve = task.valve
        self.hour = task.hour
        self.week_days = task.week_days
        self.duration = task.duration

    def __str__(self):
        return f"Task(valve={self.valve}, hour={self.hour}, week_days={self.week_days}, duration={self.duration})"

    def active_now(self) -> bool:
        now = datetime.now()
        current_weekday = now.weekday()
        current_hour = now.hour

        if not current_weekday in self.week_days:
            return False

        return current_hour == self.hour


######### Testing #########
if __name__ == "__main__":
    task1 = Task("valve1", 12, ["monday", "tuesday"], 10)
    task2 = Task("valve1", 12, ["monday", "tuesday"], 10)
    if not task1.is_the_same(task2):
        print("Error comparing the same task")
        exit(1)

    task3 = Task("valve1", 18, ["monday"], 18)
    if task1.is_the_same(task3):
        print("Error comparing different tasks")
        exit(1)

    task2.copy_from_task(task3)
    if not task2.is_the_same(task3):
        print("Error copying task")
        exit(1)

    print(task1)
    print(task2)
    print(task3)

    now = datetime.now()
    current_weekday = now.weekday()
    current_hour = now.hour
    task = Task("valve1", current_hour, [current_weekday], 10)
    if not task.active_now():
        print("ERROR: it should be active now!")

    task = Task("valve1", current_hour, [current_weekday+1], 10)
    if task.active_now():
        print("ERROR: it should not be active now!")

    print("Done!")
