import threading
import time
import Queue
import pigpio

class SwitchElement():
	def __init__(self, name, io, typ, pin, collector):
		self.type = typ
		self.name = name
		self.pin = pin
		self.state = 0
		self.collector = collector
		self.io = io

	def WorkThread(self, name, args):
		if self.pin:
			self.state = self.io.read(self.pin)
		while True:
			c_state = self.io.read(self.pin)
			if c_state != self.state :
				self.state = c_state
				self.collector.AddEvent (self, "button", self.state)
			time.sleep(0.01)

	def WorkThreadStart(self):		
		t = threading.Thread(target=self.WorkThread, args=("Button_" + str(self.pin),None,))
		t.daemon = True
		t.start()

	def ProcessEvent(self, ev):
		pass
		
	
	def MqttRegister(self):
		pass
	
	def MqttReceive(self, topic, msg):
		pass

	def MqttPublish(self):
		
		pass

	def GetState(self):
		return self.state
	def GetMqttProp(self):
		return ""
