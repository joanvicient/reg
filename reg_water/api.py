#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from task_manager import TaskManager
from task import Task, TaskRequest

class TaskApi:
    def __init__(self, task_manager: TaskManager):
        self.task_manager = task_manager
        self.app = FastAPI(
            title="reg_water API",
            description="API for get and set irrigation valves schedduling",
            version="1.0.0"
        )

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def setup_routes(self):
        @self.app.get("/", include_in_schema=False)
        def read_root():
            """Redirect to Swagger UI"""
            return RedirectResponse(url="/docs")
        
        @self.app.get("/reg/tasks/")
        def get_tasks():
            """Get all tasks"""
            return {"tasks": self.task_manager.get_tasks()}

        @self.app.post("/reg/tasks/", response_model=dict)
        def add_task(task: TaskRequest):
            """
            Add a new irrigation task
            
            - **valve**: Valve identifier (e.g., "valve1", "main")
            - **hour**: Hour of day (0-23) when the task should run
            - **week_days**: List of days when task should repeat (e.g., ["Monday", "Tuesday"])
            - **duration**: Duration in seconds for irrigation
            """
            task_obj = Task(task.valve, task.hour, task.week_days, task.duration)
            print("Task ", task_obj, " created successfully")
            result = self.task_manager.add_task(task_obj)
            if result:
                return {"message": "Task added successfully", "success": True}
            else:
                raise HTTPException(status_code=404, detail=f"Valve {task.name} not found or test failed")

        @self.app.delete("/reg/water/{id}")
        def delete_task(id: str):
            """Delete a task"""
            result = self.task_manager.rm_task(id)
            if result:
                return {"message": "Task deleted successfully", "success": True}
            else:
                raise HTTPException(status_code=404, detail=f"Task {id} not found")

    def run(self, host="0.0.0.0", port=8080):
        self.setup_routes()
        uvicorn.run(self.app, host=host, port=port)


if __name__ == "__main__":
    manager = TaskManager()
    t1 = Task("test1", 5, ["Monday", "Tuesday"], 2)
    t2 = Task("test2", 5, ["Monday", "Tuesday"], 2)
    t3 = Task("test3", 11, ["Monday", "Tuesday"], 2)
    manager.add_task(t1)
    manager.add_task(t2)
    manager.add_task(t3)

    api = TaskApi(manager)

    print("API running on http://localhost:8080, test all endpoints")
    api.run()
