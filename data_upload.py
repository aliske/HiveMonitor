# Python Beehive Monitor
# Aaron Liske
# April 2024
# Todo:
#  * HX711 support for quad load cells for weight monitoring
#  * Options to dictate which is internal/external load cells
#    - Currently hardcoded device ID

import os
import glob
import time
import requests
import yaml
from datetime import datetime
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import RPi.GPIO as GPIO
from picamera import PiCamera
from hx711 import HX711

image_name = 'image.jpg'

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')

with open('config.yml','r') as file:
	data = yaml.load(file, Loader=yaml.SafeLoader)

print('External Sensor:',data['external_sensor'])
external_sensor = data['external_sensor']

def read_temp_raw(device):
	device_file = device + '/w1_slave'
	f = open(device_file,'r')
	lines = f.readlines()
	f.close()
	return lines

def read_temp(device):
	lines = read_temp_raw(device)
	while lines[0].strip()[-3:] != 'YES':
		time.sleep(0.2)
		lines = read_temp_raw(device)
	equals_pos = lines[1].find('t=')
	if equals_pos != -1:
		temp_string = lines[1][equals_pos+2:]
		temp_c = float(temp_string) / 1000.0
		return temp_c

ext_temp = 0.0
for device in device_folder:
	if(device == '/sys/bus/w1/devices/'+ external_sensor):
		ext_temp = read_temp(device)

for hives in data['hives']:
	int_temp = 0.0
	hive_id = str(hives['id'])
	print('Hive ID:',hive_id)

	if hives['internal_sensor'] != False:
		internal_sensor = hives['internal_sensor']
		print('Internal Sensor:',hives['internal_sensor'])
	else:
		internal_sensor = False
		print('No Internal Sensor Installed')

	if internal_sensor != False:
		for device in device_folder:
			if(device == '/sys/bus/w1/devices/'+ internal_sensor):
				int_temp = read_temp(device)

	print('Interior temperature (C):', int_temp)
	print('Exterior temperature (C):', ext_temp)
	if(hives['camera'] == True):
		camera = PiCamera()
		time.sleep(5)
#this line is optional.  It's necessary for the enclosure in my setup
		camera.zoom = (0.15,0.0,0.70,0.80)
		camera.capture(image_name)
		if(os.path.isfile(image_name)):
			print('Image Captured')
			img = Image.open(image_name)
			#I1 = img.crop((100,0,0,100))
			I1 = ImageDraw.Draw(img)
			date_time_obj = 'Hive ' + hive_id + ': ' + str(datetime.now())
			myFont = ImageFont.truetype('FreeMono.ttf', 20)
			I1.rectangle(((20,30),(450, 60)), fill="#cccccc")
			I1.text((28, 36), date_time_obj, font=myFont, fill=(0,0,0))
			I1.rectangle(((20,60),(325, 90)), fill="#cccccc")
			temp_text = f'Int: {int_temp} Ext: {ext_temp}' 
			I1.text((28, 68), temp_text, font=myFont, fill=(0,0,0))
			img.save(image_name)
		else:
			print('Failed to capture image')
	
	target_url = "https://aaronliske.com/bees/upload_data.php"
	
	if hives['camera'] == True:
		target_file = open(image_name,"rb")
		response = requests.post(target_url, files = {"userImage":target_file}, data = {"int_temp" : int_temp, "ext_temp" : ext_temp, "hive" : hive_id})
	else:
		print('No Camera for this Hive')
		target_file = open('no_camera.jpg',"rb")
		response = requests.post(target_url, files = {"userImage":target_file}, data={"int_temp": int_temp, "ext_temp" : ext_temp, "hive": hive_id })
	
	if response.ok:
		print('Data Uploaded')
		if hives['camera'] == True:
			os.remove(image_name)
			print('Local Image File Deleted')
	else:
		print('Error during data upload')

#try:
#	hx711 = HX711 (
#		dout_pin=5,
#		pd_sck_pin=6,
#		channel='A',
#		gain=64
#	)
#	measures = hx711.get_raw_data()
#finally:
#	GPIO.cleanup()
#print(measures)

