import threading
import time
import pigpio
import json

class MovementElement():
    def __init__(self, name, io, typ, pin, collector):
        self.type = typ
        self.name = name
        self.pin = pin
        self.state = 0
        self.collector = collector
        self.io=io
        self.publish_movement = True

    def WorkThread(self, name, args):
        if self.pin:
            self.state = self.io.read(self.pin)
        while True:
            c_state = self.io.read(self.pin)
            if c_state != self.state :
                self.state = c_state
                self.collector.AddEvent (self, "movement", self.state)
                self.MqttPublish("ON" if self.state else "OFF" )
            time.sleep(0.1)

    def WorkThreadStart(self):      
        t = threading.Thread(target=self.WorkThread, args=("Movement_" + str(self.pin),None,))
        t.daemon = True
        t.start()
    
    def ProcessEvent(self, ev):
        if ev.src == "mqtt":
            self.MqttReceive (ev.name, ev.data)
            return
        if ev.src == "mqtt_ready":
            self.MqttInitialPublishOnReady ()
            return

    def Get(self, what):
        if what == "state":
            return self.state
        else:
            return None

    def MqttRegister(self):
        pass
    
    def MqttReceive(self, topic, msg):
        pass

    def MqttPublish(self, val):
        if self.publish_movement:
            self.collector.PublichMqttEvent ("{}".format(self.type), val)
    
    def MqttInitialPublishOnReady(self):    
        config = {}
        topic = "homeassistant/binary_sensor/{}/movement".format (self.collector.name)
        unique_id = self.collector.name + "_movement" 
        device = {"name":self.collector.name, "identifiers": [self.collector.name]}
                
        config["device"] = device
        config["unique_id"] = unique_id + "_movement"

        config["name"] = "Movement"
        config["device_class"] = "motion"
        
        config["state_class"] = "measurement"
        config["state_topic"] = "{}/{}".format (topic, "state")
        config["value_template"] =  "{%if is_state(entity_id,\"on\")-%}OFF{%-else-%}ON{%-endif%}"   

        self.collector.PublichMqttEvent ("{}/{}".format (topic, "config"), json.dumps(config))
        self.collector.PublichMqttEvent ("{}/{}".format (topic, "state"), "ON" if self.publish_movement else "OFF")


    def GetMqttProp(self):
        return "" 
