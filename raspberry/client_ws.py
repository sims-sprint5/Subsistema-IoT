#!/usr/bin/env python3
import asyncio
import json
import time
import math
import os
import websockets

try:
    from actuator_gpio import GPIOActuator
    ACTUATOR_AVAILABLE = True
except ImportError:
    ACTUATOR_AVAILABLE = False
    print("WARNING: Could not import actuator_gpio")

try:
    from ADCDevice import PCF8591, ADS7830
    import smbus
except ImportError:
    print("WARNING: ADCDevice or smbus not found")


# ======== CONFIG =========
API_WS_URL = os.getenv("API_WS_URL", "ws://127.0.0.1:8088/ws/vehicle/001")
SEND_INTERVAL = float(os.getenv("SEND_INTERVAL", "10"))
VEHICLE_ID = os.getenv("VEHICLE_ID", "001")


# Global actuator instance
actuator = None
if ACTUATOR_AVAILABLE:
    actuator = GPIOActuator.from_env()

# Global ADC instance
adc = None

def setup_adc():
    global adc
    try:
        from ADCDevice import PCF8591, ADS7830, ADCDevice
        tmp_adc = ADCDevice()
        if tmp_adc.detectI2C(0x48):
            adc = PCF8591()
        elif tmp_adc.detectI2C(0x4b):
            adc = ADS7830()
        else:
            print("No correct I2C address found for ADC.")
    except Exception as e:
        print(f"I2C ADC setup failed: {e}")

def read_temperature():
    if not adc:
        return None
    try:
        value = adc.analogRead(0)
        voltage = value / 255.0 * 3.3
        if voltage == 3.3: # prevent div/0
            return None
        Rt = 10 * voltage / (3.3 - voltage)
        if Rt <= 0:
            return None
        tempK = 1 / (1 / (273.15 + 25) + math.log(Rt / 10) / 3950.0)
        tempC = tempK - 273.15

        return {
            "type": "temperature",
            "adc_value": value,
            "voltage": round(voltage, 2),
            "temperature_c": round(tempC, 2),
        }
    except Exception as e:
        print(f"Error reading temperature: {e}")
        return None

async def send_sensor_data(websocket):
    while True:
        data = read_temperature()
        if data:
            print(f"[{VEHICLE_ID}] Sending sensor data: {data}")
            await websocket.send(json.dumps(data))
        else:
            # Dummy data fallback for testing without physical sensor
            dummy_data = {
                "type": "temperature",
                "adc_value": 150,
                "voltage": 1.7,
                "temperature_c": 22.5 + (time.time() % 5)
            }
            print(f"[{VEHICLE_ID}] Sending dummy sensor data: {dummy_data}")
            await websocket.send(json.dumps(dummy_data))
        await asyncio.sleep(SEND_INTERVAL)

async def receive_commands(websocket):
    async for message in websocket:
        try:
            data = json.loads(message)
            print(f"[{VEHICLE_ID}] Received command: {data}")
            
            if data.get("command") == "ON":
                if actuator:
                    actuator.on()
                print(f"[{VEHICLE_ID}] Actuator turned ON")
                
            elif data.get("command") == "OFF":
                if actuator:
                    actuator.off()
                print(f"[{VEHICLE_ID}] Actuator turned OFF")
                
        except json.JSONDecodeError:
            print("Received unparseable message")

async def main():
    setup_adc()
    if actuator:
        actuator.setup()
        
    url = API_WS_URL.replace("http://", "ws://").replace("https://", "wss://")
    print(f"[{VEHICLE_ID}] Connecting to WebSocket {url}...")
    
    while True:
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=20) as websocket:
                print(f"[{VEHICLE_ID}] Connected!")
                
                # Start two parallel tasks: one for sending data, one for receiving commands
                send_task = asyncio.create_task(send_sensor_data(websocket))
                receive_task = asyncio.create_task(receive_commands(websocket))
                
                done, pending = await asyncio.wait(
                    [send_task, receive_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # If one task fails/exits, cancel the other and reconnect
                for task in pending:
                    task.cancel()
                    
        except Exception as e:
            print(f"[{VEHICLE_ID}] Connection failed or dropped: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        if actuator:
            actuator.cleanup()
        if adc:
            adc.close()
        print("Stopped.")
