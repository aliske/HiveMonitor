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
int_temp = 0.0
ext_temp = 0.0

for device in device_folder:
	if(device == '/sys/bus/w1/devices/28-292bd44548b0'):
		int_temp = read_temp(device)
	else:
		ext_temp = read_temp(device)

print('Interior temperature (C):', int_temp)
print('Exterior temperature (C):', ext_temp)

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
	date_time_obj = 'Hive 1: ' + str(datetime.now())
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

target_file = open(image_name,"rb")
response = requests.post(target_url, files = {"userImage":target_file}, data = {"int_temp" : int_temp, "ext_temp" : ext_temp})

if response.ok:
	print('Data Uploaded')
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

