#!/usr/bin/python
import pywemo

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
wemo_toggle(switches[0])
#wemo_off(switches[0])



"""
#devices = pywemo.discover_devices()
## get the wemote directly (in case discover doesn't work)
address = "10.0.1.23"
port = pywemo.ouimeaux_device.probe_wemo(address)
url = 'http://%s:%i/setup.xml' % (address, port)
device = pywemo.discovery.device_from_description(url, None)
print(device)
"""