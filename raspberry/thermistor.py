#!/usr/bin/env python3
#############################################################################
# Raspberry Pi - Sensor de Temperatura
# Envía lecturas a FastAPI via HTTP
#############################################################################

import time
import math
import requests
from ADCDevice import *

# ======== CONFIG API =========
# Cambiar por la IP/dominio donde corre el Docker con FastAPI
API_URL = "http://192.168.1.100:8000/api/temperature/"
API_KEY = "mi-api-key-secreta-cambiar-en-produccion"

# Intervalo de envío en segundos
SEND_INTERVAL = 2

# ======== Buffer para envío por lotes (si falla la conexión) =========
pending_readings = []
MAX_BUFFER = 100  # máximo de lecturas acumuladas antes de descartar las más viejas

adc = ADCDevice()


def setup():
    global adc
    if adc.detectI2C(0x48):
        adc = PCF8591()
    elif adc.detectI2C(0x4b):
        adc = ADS7830()
    else:
        print("No correct I2C address found.")
        exit(-1)


def read_temperature():
    """Lee el sensor y retorna los datos."""
    value = adc.analogRead(0)
    voltage = value / 255.0 * 3.3
    Rt = 10 * voltage / (3.3 - voltage)
    tempK = 1 / (1 / (273.15 + 25) + math.log(Rt / 10) / 3950.0)
    tempC = tempK - 273.15

    return {
        "adc_value": value,
        "voltage": round(voltage, 2),
        "temperature_c": round(tempC, 2),
    }


def send_to_api(data):
    """Envía una lectura individual a la API."""
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY,
    }
    response = requests.post(API_URL, json=data, headers=headers, timeout=5)
    response.raise_for_status()
    return response.json()


def send_bulk_to_api(readings):
    """Envía múltiples lecturas acumuladas a la API."""
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY,
    }
    url = API_URL.rstrip("/") + "/bulk"
    response = requests.post(url, json=readings, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()


def loop():
    global pending_readings

    while True:
        try:
            data = read_temperature()
            print(f"Lectura: {data}")

            # Si hay lecturas pendientes, intentar enviarlas primero
            if pending_readings:
                try:
                    pending_readings.append(data)
                    result = send_bulk_to_api(pending_readings)
                    print(f"Enviadas {len(pending_readings)} lecturas acumuladas: {result}")
                    pending_readings = []
                except requests.exceptions.RequestException:
                    print(f"Sin conexión. Acumuladas: {len(pending_readings)} lecturas")
                    if len(pending_readings) > MAX_BUFFER:
                        pending_readings = pending_readings[-MAX_BUFFER:]
            else:
                # Envío normal individual
                try:
                    result = send_to_api(data)
                    print(f"Enviado a API: {result}")
                except requests.exceptions.RequestException as e:
                    print(f"Error de conexión, acumulando lectura: {e}")
                    pending_readings.append(data)

        except Exception as e:
            print(f"Error leyendo sensor: {e}")

        time.sleep(SEND_INTERVAL)


def destroy():
    adc.close()


if __name__ == "__main__":
    print("Program is starting ...")
    print(f"API URL: {API_URL}")
    setup()
    try:
        loop()
    except KeyboardInterrupt:
        destroy()
        print("Ending program")
