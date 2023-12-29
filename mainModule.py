import Queue
import json
import time
import threading
import subprocess
import datetime
import sys

import socket
import paho.mqtt.client as mqtt
from uuid import getnode as get_mac
from time import gmtime, strftime
from static_config import STATIC_CONFIG 
from element_movement import MovementElement
from element_ilum import IlluminanceElement
from element_light import LightElement
from element_switch import SwitchElement
from element_humidity import HumidityElement
from pprint import pprint
from uuid import getnode as get_mac
import psutil
import pigpio

import helpers
#DEBUG = True
DEBUG=False
# Globals
g_config = ""
g_my_mac = 0
g_unit = []
g_io=None
g_client=None

g_stat_interval = 60

def mqtt_init():
	global g_client
	g_client = mqtt.Client(client_id=str(helpers.get_local_mac()))
	g_client.max_inflight_messages_set(100)
	g_client.on_connect = mqtt_on_connect
	g_client.on_message = mqtt_on_message
	#g_client.on_publish = mqtt_on_publish
	g_client.on_log = mqtt_log
	g_client.username_pw_set("mqtt_user", "mqtt_user")
	try:
		g_client.connect("192.168.0.5")
	except:
		print "No mtqq server" 
		return
	g_client.loop_start()


def mqtt_on_publish(mqttc, obj, mid):
    print(str(obj) + str(mid))
    pass

def mqtt_log(client, userdata, level, buf):
	#print client, userdata, level, buf 
	pass

def mqtt_deinit():
	global g_client
	g_client.loop_stop()

def mqtt_on_connect (client, userdata, flags, rc):
	global g_unit
	#now send read event, so all send theit current status
	for circ in g_unit:
		for elem in circ.elements:
			elem.MqttRegister()
		circ.AddEvent( "mqtt_ready", "", "")
	#start the I-m here 
	


	
# The callback for when a PUBLISH message is received from the server.
def mqtt_on_message(client, userdata, msg):
	global g_unit, g_client, g_stat_interval, DEBUG
	if DEBUG:
		print("RECEIVE '" + str(msg.payload) + "' on topic '" + msg.topic + "' with QoS " + str(msg.qos))
	splitted = msg.topic.split("/")
	if splitted[0] != "homeassistant":
		return
	for circ in g_unit:
		if splitted[2] == circ.name:
			for elem in circ.elements:
				if splitted[3] in  elem.GetMqttProp():
					circ.AddEvent( "mqtt", msg.topic, msg.payload)
					

def ConstructUnit(config):
	global g_unit
	
	for circ_cfg in config["Nodes"]:
		name = circ_cfg["name"]
		circuit = Circuit(name)
		g_unit.append(circuit)
		for elem in circ_cfg:
			circuit.AddElement(elem, circ_cfg[elem])

class Event():
	def __init__(self, src, name, data):
		self.src = src
		self.name = name
		self.data = data

class Circuit():
	def __init__(self, name):
		self.name = name
		self.elements = []
		self.eventQueue = Queue.Queue()
	
	def AddElement(self, typ, element_cfg):
		element = None

		if typ == "name":
			return
		if typ == "movement":
			element = MovementElement(self.name , g_io, typ, element_cfg["pin"], self)
		if typ == "light":
			if "bright_thresh" in element_cfg:
				element = LightElement(self.name , g_io, typ, element_cfg["pin"], self, element_cfg["bright_thresh"])
			else:
				element = LightElement(self.name , g_io, typ, element_cfg["pin"], self, 0)
		if typ == "brightness":
			element = IlluminanceElement(self.name , g_io, typ, element_cfg["pin"], self)
		if typ == "humidity":
			element = HumidityElement(self.name , g_io, typ, element_cfg["pin"], self)
		if typ == "button":
			element = SwitchElement(self.name , g_io, typ, element_cfg["pin"], self)
		if element:
			self.elements.append(element)
	
	def AddEvent(self, src, name, value):
		ev = Event (src, name, value)
		self.eventQueue.put(ev)

	def PublichMqttEvent(self, topic, value):
		if DEBUG:
			print ("PULISH {}\n \t{}".format (topic , value))
		if not isinstance(value, bytes):
			value = bytes (str(value).encode("utf-8"))
		infot = g_client.publish(topic, value, qos=1, retain=True)
		

	def SubscribeMqtt(self, topic):
		if DEBUG:
			print ("SUBSCRIBE", topic)
		g_client.subscribe(topic)

	def CircuitThread(self):
		for elem in self.elements:
			if elem:
				elem.WorkThreadStart()
		while True:
			ev = self.eventQueue.get()
			if ev:
				for elem in self.elements:
					if elem != ev.src:
						elem.ProcessEvent(ev)
		time.sleep(0.01)
	
	def start_working(self):
		t = threading.Thread(target=self.CircuitThread)
		t.daemon = True
		t.start()


# MAIN

g_config = None
g_my_mac = get_mac()
g_io=pigpio.pi()


if g_config == None:
	config_all = json.loads(STATIC_CONFIG)
	#print hex(g_my_mac)
	for unit_mac in config_all:
		if unit_mac == hex(g_my_mac):
			g_config = config_all[unit_mac]

ConstructUnit(g_config)

mqtt_init()
for circ in g_unit:
	#print hex(id(circ)), "START"
	circ.start_working()
	pass
while True:
	time.sleep(5)
