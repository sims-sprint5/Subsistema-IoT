#!/usr/bin/env python3
#############################################################################
# DIY Thermometer + MongoDB Atlas
#############################################################################

import time
import math
import datetime
from pymongo import MongoClient
from ADCDevice import *

# ======== CONFIG MONGO =========
MONGO_URI = ""
DB_NAME = "raspberry"
COLLECTION_NAME = "temperatura"

# Conexn Mongo
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

adc = ADCDevice()

def setup():
    global adc
    if(adc.detectI2C(0x48)):
        adc = PCF8591()
    elif(adc.detectI2C(0x4b)):
        adc = ADS7830()
    else:
        print("No correct I2C address found.")
        exit(-1)

def loop():
    while True:
        try:
            value = adc.analogRead(0)
            voltage = value / 255.0 * 3.3
            Rt = 10 * voltage / (3.3 - voltage)
            tempK = 1/(1/(273.15 + 25) + math.log(Rt/10)/3950.0)
            tempC = tempK - 273.15

            data = {
                "adc_value": value,
                "voltage": round(voltage, 2),
                "temperature_c": round(tempC, 2),
                "timestamp": datetime.datetime.utcnow()
            }

            collection.insert_one(data)

            print("Enviado a Mongo:", data)

        except Exception as e:
            print("Error enviando a Mongo:", e)

        time.sleep(2)  #  envo cada 2 segundos

def destroy():
    adc.close()
    client.close()

if __name__ == '__main__':
    print('Program is starting ... ')
    setup()
    try:
        loop()
    except KeyboardInterrupt:
        destroy()
        print("Ending program")

