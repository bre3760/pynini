#!/usr/bin/python
import sys
import paho.mqtt.client as mqtt
from MyMQTT import *
import Adafruit_DHT

while True:

    humidity, temperature = Adafruit_DHT.read_retry(11, 4)
    print ('Temp: {0:0.1f} C  Humidity: {1:0.1f} %'.format(temperature, humidity))

    client = MyMQTT('Raspi', 'www.test.mosquitto.org', 1883)  #####notifier da verificare
    # RB raccoglie i dati dai sensori: non comunica tramite mqtt!
    # ciascun attuatore si registra ad una topic,
    # creo un cliente per ciascun parametro e pubblico sulla topic la stringa di dati rilevati
    # attuatore realtivo a quella topic legge ed esegue determinati comandi
    client.start()
    # sottoscrivo il cliente a tutte le topics d'interesse
    client.mySubscribe('temperature')
    client.mySubscribe('humidity')
    #client.mySubscribe('CO2')

    client.myPublish('temperature', temperature)
    client.myPublish('humidity', humidity)
    #client.myPublish('CO2', CO2)



