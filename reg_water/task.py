#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class WeekDay(str, Enum):
    """Enumeration of valid week days"""
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


class TaskRequest(BaseModel):
    """Pydantic model for task creation requests"""
    valve: str
    hour: int = Field(ge=0, le=23, description="Hour of day (0-23)")
    week_days: list[WeekDay] = Field(description="List of days when task should run")
    duration: int = Field(gt=0, description="Duration in minutes")

    model_config = {
        "json_schema_extra": {
            "example": {
                "valve": "valve1",
                "hour": 12,
                "week_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                "duration": 10
            }
        }
    }

class Task:
    def __init__(self, valve: str, hour: int, week_days: list[WeekDay], duration: int):
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
        current_weekday_num = now.weekday()  # 0=Monday, 6=Sunday
        current_hour = now.hour

        # Convert weekday number to string name
        weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        current_weekday_name = weekday_names[current_weekday_num]

        if current_weekday_name not in [day.value for day in self.week_days]:
            return False

        return current_hour == self.hour


######### Testing #########
if __name__ == "__main__":
    task1 = Task("valve1", 12, [WeekDay.MONDAY, WeekDay.TUESDAY], 10)
    task2 = Task("valve1", 12, [WeekDay.MONDAY, WeekDay.TUESDAY], 10)
    if not task1.is_the_same(task2):
        print("Error comparing the same task")
        exit(1)

    task3 = Task("valve1", 18, [WeekDay.MONDAY], 18)
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
    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    current_weekday_name = weekday_names[current_weekday]
    current_weekday_enum = WeekDay(current_weekday_name)
    task = Task("valve1", current_hour, [current_weekday_enum], 10)
    if not task.active_now():
        print("ERROR: it should be active now!")

    next_weekday_name = weekday_names[(current_weekday + 1) % 7]
    next_weekday_enum = WeekDay(next_weekday_name)
    task = Task("valve1", current_hour, [next_weekday_enum], 10)
    if task.active_now():
        print("ERROR: it should not be active now!")

    print("Done!")
