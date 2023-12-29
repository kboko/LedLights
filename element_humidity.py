import threading
import time
import Adafruit_DHT
import json

class HumidityElement():
    def __init__(self, name, io, typ, pin, collector):
        self.pin = pin
        self.name = name
        self.io = io
        self.type = typ
        self.humidity=0
        self.temperature=0
        self.collector = collector

    def WorkThread(self, name, args):
        
        while True:
            
            humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, self.pin)
            
            if humidity == None or temperature == None:
                continue
            
            if humidity != self.humidity :
                self.humidity = humidity
                self.collector.AddEvent (self, "humidity", humidity)
                self.MqttPublish("humidity", humidity)
            if temperature != self.temperature :
                self.temperature = temperature
                self.collector.AddEvent (self, "temperature", temperature)
                self.MqttPublish("temperature", temperature)
            time.sleep(10)

    def WorkThreadStart(self):      
        t = threading.Thread(target=self.WorkThread, args=("Humidity_" + str(self.pin),None,))
        t.daemon = True
        t.start()

    def GetTemperature(self):
        return self.temperature

    def GetHumidity(self):
        return self.humidity
    
    def ProcessEvent(self, ev):
        if ev.src == "mqtt_ready":
            self.MqttInitialPublishOnReady ()
            return

    def MqttRegister(self):
        pass
    
    def MqttReceive(self, topic, msg):
        pass

    def MqttPublish(self, whatr, val):
        topic = "homeassistant/sensor/{}/{}/state".format (self.collector.name, whatr)
        self.collector.PublichMqttEvent ("{}/{}".format (topic, "state"), val)

    
    def MqttInitialPublishOnReady(self):
        config = {}
        topic = "homeassistant/sensor/{}/temperature".format (self.collector.name)
        unique_id = self.collector.name + "_temperature" 
        device = {"name":self.collector.name, "identifiers": [self.collector.name]}
                
        config["device"] = device
        config["unique_id"] = unique_id + "_temperature"

        config["name"] = "Temperature"
        
        config["state_class"] = "measurement"
        config["state_topic"] = "{}/{}".format (topic, "state")

        self.collector.PublichMqttEvent ("{}/{}".format (topic, "config"), json.dumps(config))
        self.collector.PublichMqttEvent ("{}/{}".format (topic, "state"), 0)

        config = {}
        topic = "homeassistant/sensor/{}/humitity".format (self.collector.name)
        unique_id = self.collector.name + "_humitity" 
        device = {"name":self.collector.name, "identifiers": [self.collector.name]}
                
        config["device"] = device
        config["unique_id"] = unique_id + "_humitity"

        config["name"] = "Humitity"
        
        config["state_class"] = "measurement"
        config["state_topic"] = "{}/{}".format (topic, "state")

        self.collector.PublichMqttEvent ("{}/{}".format (topic, "config"), json.dumps(config))
        self.collector.PublichMqttEvent ("{}/{}".format (topic, "state"), 0)
    
    def GetMqttProp(self):
        return "temperature, humidity"