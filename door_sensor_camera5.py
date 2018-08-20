#!/usr/bin/python

## resources
# https://community.home-assistant.io/t/mqtt-trigger-remote-camera/16980
# https://www.pyimagesearch.com/2016/01/18/multiple-cameras-with-the-raspberry-pi-and-opencv/
# https://datascience.stackexchange.com/questions/27694/is-there-a-person-class-in-imagenet-are-there-any-classes-related-to-humans?noredirect=1&lq=1
# imagenetDoesn't have a person class. 

## transfer to pi
# scp myfile.txt pi@192.168.0.3:home/pi/projects/motion_camera

import paho.mqtt.client as mqttClient
import paho.mqtt.publish as mqttPublish
import time
import requests
import picamera
import threading
import pywemo

from threading import Thread

brokerAddress= "192.168.0.3" 
port = 1883   
channel = "acelab/sensors/motion"

IMAGE_PATH = "roomObject.jpg"
REST_API = "http://192.168.0.6:8000/yolopredict"

keywords = ["person","human","wardrobe","dumbbell","barbell","photocopier"]
flags = {"roomOccupied": False}

######### WEMO ######################

def get_devices():
	""" Find all the devices and return them in a list """
	# sometimes the built in library discovery doesn't work on the network. 
	addresses = ["192.168.0.17"]
	devices = []
	for i in addresses:
		port = pywemo.ouimeaux_device.probe_wemo(i)
		url = 'http://%s:%i/setup.xml' % (i, port)
		device = pywemo.discovery.device_from_description(url, None)
		devices.append(device)
	return devices

def wemo_toggle(switch):
	""" toggle the state of the switch """
	state = switch.get_state()
	if state:
		switch.off()
	else:
		switch.on()

def wemo_on(switch):
	switch.on()

def wemo_off(switch):
	switch.off()

switches = get_devices()
print(switches)


######### CAMERA HELPERS ########################

def shoot_camera():
	camera = picamera.PiCamera()
	camera.capture(IMAGE_PATH)
	print("shooting image")
	time.sleep(.5)
	camera.close()
	image = open(IMAGE_PATH, "rb").read()
	payload = {"image": image}
	return payload

def motion_detected():
	isOccupied = flags["roomOccupied"]
	if not isOccupied:
		payload = shoot_camera()
		## make the model request
		print("making model requests")
		r = requests.post(REST_API, files=payload).json()
		isPerson = False
		if r["success"]:
			#print(r)
			for (i, result) in enumerate(r["predictions"]):
				label = result["label"]
				print(label)
				if label in keywords:
					isPerson = True
		else:
			print("model not reached")
		if isPerson:
			print("a person")
			wemo_on(switches[0])
			flags.update({'roomOccupied': True})
			
			
		else:
			wemo_off(switches[0])
			print("not a person")
		

def monitor_room():
	## it would be better if I could open a camera stream instead, but let's do this first. 
	## good / not good? hm.
	while True:
		isOccupied = flags["roomOccupied"]
		#print("!monitor_room: ", isOccupied)
		if isOccupied:
			print("monitoring, could be a stream to an http endpoint, or a still shot or something? publish image to a channel?")
			time.sleep(5)
		else:
			#print("heartbeat test")
			time.sleep(1)


######### MQTT CALLBACKS #########################

def on_connect(client, userdata, flags, rc):
	"""The callback function for connecting to the MQTT Broker"""
	print(client,userdata,flags)
	if rc == 0:
		print("!onConnect: Connected to broker")
	else:
		print("!onConnect: Connection failed")

def on_subscribe(mqttc, obj, mid, granted_qos):
	"""The callback for subscribing to the MQTT broker"""
	print("!on_subscribe: Subscribed: " + str(mid) + " " + str(granted_qos))
 
def on_message(client, userdata, msg):
	"""On message logic for MQTT """
	print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
	topic = msg.topic
	payload = msg.payload.decode("utf-8")
	isOccupied = flags["roomOccupied"]
	if topic == channel:
		if payload == "on":
			motion_detected()
		elif payload == "off":
			print("motion detector off")



client = mqttClient.Client("Pi Agent")        					#create new instance
client.on_connect= on_connect                   				#attach function to callback
client.on_message= on_message                   				#attach function to callback
client.connect(brokerAddress,port=port,keepalive=60)           	#connect to broker
client.subscribe(channel)

if __name__== "__main__":
	
	# room thread to monitor room if it is occupied. 
	roomThread = Thread(target=monitor_room)
	roomThread.daemon = True
	roomThread.start()
	print("starting room thread")

	try:
		client.loop_forever() 
	except KeyboardInterrupt:
		print("exiting")
		client.disconnect()
		client.loop_stop()

