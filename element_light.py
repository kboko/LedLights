import threading
import time
import Queue
import datetime
import pigpio
import logging
import logging.handlers



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
		self.on_time = 120	 # seconds
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

			if old_state != self.state:
				#print hex(id(self)), old_state, "->", self.state, datetime.datetime.now()
				g_logger.info("S-ID={}:{} S={}->{} E={} P={}/{} C={}/{} OT={} DIMM={}:{} BR={}:{}".format(hex(id(self)), self.name, old_state, self.state, event, power, max_power, cycle, cycle_all, on_time, dimm_to_on, dimm_to_off, self.brightness, self.brightness_threshold))

				if self.state == State.OFF: 
					self.off_state_time =  time.time()

				self.MqttPublish (self.state)
			
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
		self.collector.SubscribeMqtt("virt_button/set")
		self.collector.SubscribeMqtt("on_time/set")
		self.collector.SubscribeMqtt("to_on/set")
		self.collector.SubscribeMqtt("to_off/set")
		self.collector.SubscribeMqtt("maxpower/set")
		self.collector.SubscribeMqtt("threshold/set")
		pass
	
	def MqttReceive(self, topic, msg):
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

	def MqttPublish(self, val):
		val_mqtt = 0
		if (val == State.OFF):
			val_mqtt = 0
		elif (val == State.TO_ON):
			val_mqtt = int(self.max_power/2 + 5)
		elif (val == State.TO_OFF):
			val_mqtt = int(self.max_power/2 - 5)
		elif (val == State.ON):
			val_mqtt = self.max_power

		self.collector.PublichMqttEvent ("{}".format(self.type), val_mqtt)

		if val == State.OFF:
			self.collector.PublichMqttEvent ("virt_button", "OFF")
		if val == State.ON:
			self.collector.PublichMqttEvent ("virt_button", "ON")
	
	def MqttInitialPublishOnReady(self):
		self.collector.PublichMqttEvent ("{}".format(self.type), 0)
		self.collector.PublichMqttEvent ("virt_button", "OFF")		
		self.collector.PublichMqttEvent ("on_time", self.on_time)		
		self.collector.PublichMqttEvent ("to_on", self.dimm_to_on)		
		self.collector.PublichMqttEvent ("to_off", self.dimm_to_off)		
		self.collector.PublichMqttEvent ("maxpower", self.max_power)	
		self.collector.PublichMqttEvent ("threshold", self.brightness_threshold)	
	
	def GetMqttProp(self):
		return self.type + ",virt_button,on_time,to_on,maxpower,to_off,threshold" 
