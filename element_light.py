import threading
import time
import Queue
import datetime
import pigpio
import logging
import logging.handlers
import json

class Event():
    MOVEMENT = 0
    USER_ACTION = 1
    BRIGHTNESS = 4

class State():
    OFF = "OFF"
    TO_ON = "TO_ON"
    ON = "ON"
    TO_OFF = "TO_OFF"


def get_cycle(dimm_to_on, idle_time):
    result = int(round(dimm_to_on / idle_time))
    return result

def get_power(cycle, cycle_all, power):
    return int(round(power*cycle/cycle_all))
    
def logger():
    logger = logging.getLogger("Light")
    logger.setLevel(logging.DEBUG)
    handler = logging.handlers.SysLogHandler(address = '/dev/log')
    logger.addHandler(handler)
    return logger

g_logger = logger()

class LightElement():

    def __init__(self, name, io, typ, pin, collector, brightness_threshold):
        self.io = io
        self.type = typ
        self.name = name
        self.power_pin = pin
        self.state = State.OFF
        self.dimm_to_on = 5  # seconds
        self.dimm_to_off = 10 # seconds
        self.max_power = 100
        self.on_time = 120   # seconds
        self.events = Queue.Queue()
        self.collector = collector
        self.brightness = brightness_threshold
        self.brightness_threshold = brightness_threshold
        self.off_state_time =  time.time()
        g_logger.info("Start {}:{}".format (hex(id(self)),self.name))
        




    def WorkThread(self, name, args):
        new_power = 0
        power = -1
        self.off_state_time =  time.time()
        dimm_to_on = 0
        dimm_to_off = 0
        max_power = 0
        on_time = 0

        cycle = 0
        cycle_all = 0
        idle_time = 0.01
        
        while True:
            event = None
            try:
                event = self.events.get_nowait()
                g_logger.info("E-ID={}:{} S={} E={} P={}/{} C={}/{} OT={} DIMM={}:{} BR={}:{}".format(hex(id(self)), self.name, self.state, event, power, max_power, cycle, cycle_all, on_time, dimm_to_on, dimm_to_off, self.brightness, self.brightness_threshold))
            except:
                pass
            
            old_state = self.state
            if self.state == State.OFF:
                dimm_to_on = self.dimm_to_on
                dimm_to_off = self.dimm_to_off
                max_power =  self.max_power
                on_time = self.on_time
                #print  self.brightness , self.brightness_threshold
                if self.brightness < self.brightness_threshold:
                    time.sleep(1)
                    continue

                if (event == Event.MOVEMENT or event == Event.USER_ACTION):
                    cycle = 0
                    cycle_all = get_cycle(dimm_to_on, idle_time)
                    self.state = State.TO_ON    
                
            elif self.state == State.TO_ON:
                if event == Event.USER_ACTION:
                    self.state = State.OFF
                    new_power = 0
                else:
                    cycle = cycle + 1
                    new_power = get_power(cycle, cycle_all, max_power)
                    if cycle >= cycle_all:
                        self.state = State.ON 
                        cycle_all = cycle = get_cycle(on_time, idle_time)

            elif self.state == State.TO_OFF:
                if event == Event.MOVEMENT:
                    #complex calculation convert cycle to_on state
                    cycle_old = cycle
                    cycle_all_old = cycle_all
                    cycle_all = get_cycle(dimm_to_on, idle_time)
                    cycle = round(cycle_all*cycle_old/cycle_all_old)
                    self.state = State.TO_ON
                elif event == Event.USER_ACTION:
                    self.state = State.OFF
                    new_power = 0
                else:
                    cycle = cycle - 1
                    new_power = get_power(cycle, cycle_all, max_power)
                    if cycle == 0:
                        self.state = State.OFF 

            elif self.state == State.ON:
                cycle = cycle - 1
                if event == Event.USER_ACTION:
                    self.state = State.OFF
                    new_power = 0
                elif event == Event.MOVEMENT:
                    cycle_all = cycle = get_cycle(on_time, idle_time)
                elif cycle == 0:
                    self.state = State.TO_OFF
                    cycle_all = cycle = get_cycle(dimm_to_off, idle_time)
                    
            if new_power != power:
                power = new_power
                if power > 255:
                    power = 255
                if power < 0:
                    power = 0
                    #print hex(id(self)), self.power_pin, str(power)
                self.io.set_PWM_dutycycle(self.power_pin,str(power))
                self.MqttPublish (power)

            if old_state != self.state:
                #print hex(id(self)), old_state, "->", self.state, datetime.datetime.now()
                g_logger.info("S-ID={}:{} S={}->{} E={} P={}/{} C={}/{} OT={} DIMM={}:{} BR={}:{}".format(hex(id(self)), self.name, old_state, self.state, event, power, max_power, cycle, cycle_all, on_time, dimm_to_on, dimm_to_off, self.brightness, self.brightness_threshold))

                if self.state == State.OFF: 
                    self.off_state_time =  time.time()

                
            
            time.sleep(idle_time)

    def WorkThreadStart(self):      
        t = threading.Thread(target=self.WorkThread, args=("Light_" + str(self.power_pin),None,))
        t.daemon = True
        t.start()

    def ProcessEvent(self, ev):
        if ev.src == "mqtt_ready":
            self.MqttInitialPublishOnReady ()
            return
        if ev.src == "mqtt":
            self.MqttReceive (ev.name, ev.data)
            return
        if ev.name == "movement" and ev.data == 1:
            self.events.put(Event.MOVEMENT)
        if ev.name == "button":
            self.events.put(Event.USER_ACTION)
        if ev.name == "brightness":
            if self.state == State.OFF and (time.time() - self.off_state_time ) > 60:
                self.brightness = int (ev.data);
    def GetState():
        return self.state


    def MqttRegister(self):
        pass
    
    def MqttReceive(self, topic, msg):
        print ("RECEIVE", topic, msg)
        if "virt_button" in topic:
            self.events.put(Event.USER_ACTION)
        elif "on_time" in topic:
            self.on_time = int (float(msg))
        elif "to_on" in topic:
            self.dimm_to_on = int (float(msg))
        elif "to_off" in topic:
            self.dimm_to_off = int (float(msg))
        elif "power" in topic:
            self.max_power = int (float(msg))
        elif "threshold" in topic:
            self.brightness_threshold = int (float(msg))
        g_logger.info("M-ID={}:{} T={} OT={} DIMM={}:{} MP={}".format(hex(id(self)), self.type, topic, self.on_time, self.dimm_to_on, self.dimm_to_off, self.max_power))

        pass

    def MqttPublish(self, power):
        payload = {}
        payload["state"] = "ON" if power else "OFF"
        payload["brightness"] = power
                
        topic = "homeassistant/light/{}/led/state".format (self.collector.name)
        self.collector.PublichMqttEvent (topic, json.dumps(payload))
       
    def MqttInitialPublishOnReady(self):
        #setup for HASS
        config = {}
        topic = "homeassistant/light/{}/led".format (self.collector.name)
        unique_id = self.collector.name + "_led" 
        device = {"name":self.collector.name, "identifiers": [self.collector.name]}
                
        config["device"] = device
        config["unique_id"] = unique_id

        config["name"] = self.collector.name

        config["schema"] = "json"
        config["state_topic"] = "{}/{}".format (topic, "state")
        config["command_topic"] = "{}/{}".format (topic, "set")
                
        config["brightness"] = True
        config["color_mode"] = True
        config["supported_color_modes"] = ["brightness"]                
                
        self.collector.PublichMqttEvent ("{}/{}".format (topic, "config"), json.dumps(config))

        self.collector.PublichMqttEvent (config["state_topic"], json.dumps({"state":"OFF", "brightness":0}))
        self.collector.SubscribeMqtt(config["command_topic"])

        for param in [["ontime", "ON Time", "Sec", self.on_time], 
                      ["dimm_to_on", "Dimm to ON", "Sec", self.dimm_to_on], 
                      ["dimm_to_off", "Dimm to OFF", "Sec", self.dimm_to_off], 
                      ["max_power", "MAX Power", "1-255", self.max_power],
                      ["brightness_threshold", "On Threshold", "Val", self.brightness_threshold]]:
            config = {}
            topic = "homeassistant/number/{}/{}".format (self.collector.name, param[0])
            unique_id = self.collector.name + "_" + param[0]
            config["device"] = device
            config["unique_id"] = unique_id

            config["name"] =  param[1]
            config["unit_of_measurement"] =  param[2]
            config["state_topic"] = "{}/{}".format (topic, "state")
            config["command_topic"] = "{}/{}".format (topic, "set")
                    
            self.collector.PublichMqttEvent ("{}/{}".format (topic, "config"), json.dumps(config))
            self.collector.PublichMqttEvent ("{}/{}".format (topic, "state"), param[3])
            self.collector.SubscribeMqtt(config["command_topic"])


    
    def GetMqttProp(self):
        return "led,ontime,dimm_to_on,dimm_to_off,max_power,brightness_threshold" 
