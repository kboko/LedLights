import threading
import time
import Adafruit_DHT

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
		self.collector.PublichMqttEvent ("{}".format(whatr),val)
		pass
	
	def MqttInitialPublishOnReady(self):
		self.collector.PublichMqttEvent ("temperature", self.temperature)
		self.collector.PublichMqttEvent ("humidity", self.humidity)

	def GetMqttProp(self):
		return "temperature, humidity"