#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from manager import ValvesManager

class ValveApi:
    def __init__(self, valves_manager: ValvesManager):
        self.valves_manager = valves_manager
        self.app = FastAPI(
            title="reg_valves API",
            description="API for discovering and controlling irrigation valves via ESP devices",
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
        
        @self.app.get("/reg/valves/")
        def get_valves():
            """Get all valves"""
            return {"valves": self.valves_manager.get_valves_json()}
    
        @self.app.get("/reg/esps/")
        def get_esps():
            """Get all ESPs"""
            return {"esps": self.valves_manager.get_esp32_json()}

        @self.app.get("/reg/valves/{valve_name}")
        def get_valve(valve_name: str):
            """Get a specific valve"""
            result = self.valves_manager.get_valve_json(valve_name)
            if result:
                return result
            else:
                raise HTTPException(status_code=404, detail=f"Valve {valve_name} not found")

        @self.app.post("/reg/valves/{valve_name}/test")
        def test_valve(valve_name: str):
            """Test a valve"""
            result = self.valves_manager.test_valve(valve_name)
            if result:
                return {"message": f"Valve {valve_name} tested successfully", "success": True}
            else:
                raise HTTPException(status_code=404, detail=f"Valve {valve_name} not found or test failed")

        @self.app.post("/reg/valves/{valve_name}/water")
        def water_valve(valve_name: str):
            """Water a valve"""
            result = self.valves_manager.water_valve(valve_name)
            if result:
                return {"message": f"Valve {valve_name} watered successfully", "success": True}
            else:
                raise HTTPException(status_code=404, detail=f"Valve {valve_name} not found or water failed")

    def run(self, host="0.0.0.0", port=8080):
        self.setup_routes()
        uvicorn.run(self.app, host=host, port=port)


if __name__ == "__main__":
    manager = ValvesManager()
    manager.set_esp_value("test", "status", "ON")
    manager.set_esp_value("test", "uptime", "aaaaaa")
    manager.set_esp_value("test", "rssi", "-124")
    manager.set_esp_value("test", "ip1", "192")
    manager.set_esp_value("test", "ip2", "168")
    manager.set_esp_value("test", "ip3", "0")
    manager.set_esp_value("test", "ip4", "146")

    api = ValveApi(manager)

    print("API running on http://localhost:8080, test all endpoints")
    print("Note that 'water' will fail if 'main' valve is not found")
    api.run()
