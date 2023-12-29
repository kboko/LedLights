import threading
import time
import json
import pigpio
import time

class IlluminanceElement():
    def __init__(self, name, io, typ, pin, collector):
        self.type = typ
        self.name = name
        self.pin = pin
        self.illuminance = 0
        self.collector = collector
        self.io = io

    def WorkThread(self, name, args):
        if self.pin == None:
            self.illuminance = 5000
            return
        
        while True:
            self.io.set_mode( self.pin, pigpio.OUTPUT)
            self.io.write(self.pin,0)
            time.sleep(0.1)
            start = time.time()
            self.io.set_mode( self.pin, pigpio.INPUT)
            count = 0
            while True:
                if self.io.read(self.pin) == 0:
                    count += 1
                    if count > 5000:
                        break
                else:
                    break
            calc =  time.time() - start
            self.illuminance = calc * 1000  
            self.collector.AddEvent (self, "brightness", int(self.illuminance))
            self.MqttPublish (int(self.illuminance))
            time.sleep(60)

    def WorkThreadStart(self):      
        t = threading.Thread(target=self.WorkThread, args=("Brightness" + str(self.pin),None,))
        t.daemon = True
        t.start()

    def ProcessEvent(self, ev):
        if ev.src == "mqtt_ready":
            self.MqttInitialPublishOnReady ()
            return

    def GetIlluminance(self):
        return self.illuminance

    def MqttRegister(self):
        pass
    
    def MqttReceive(self, topic, msg):
        pass

    def MqttPublish(self, val):
        topic = "homeassistant/sensor/{}/illuminance".format (self.collector.name)
        self.collector.PublichMqttEvent ("{}/{}".format (topic, "state"), self.illuminance)


    def MqttInitialPublishOnReady(self):
        config = {}
        
        topic = "homeassistant/sensor/{}/illuminance".format (self.collector.name)
        unique_id = self.collector.name + "_illuminance" 
        device = {"name":self.collector.name, "identifiers": [self.collector.name]}
                
        config["device"] = device
        config["unique_id"] = unique_id

        config["name"] = "Iluminance"
        #config["device_class"] = "illuminance"
        
        config["state_class"] = "measurement"
        config["state_topic"] = "{}/{}".format (topic, "state")
        

        self.collector.PublichMqttEvent ("{}/{}".format (topic, "config"), json.dumps(config))
        
        self.collector.PublichMqttEvent ("{}/{}".format (topic, "state"), self.illuminance)
        

    def GetMqttProp(self):
        return "illuminance"