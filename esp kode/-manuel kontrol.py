import network
import espnow
import ujson
from machine import Pin, ADC
from time import sleep

GRIBBER = 0
GRIBBER_ROTATION = 1
HAANDLED = 2
ALBUE = 3
SKULDER_1 = 4
SKULDER_2 = 5
BASE_ROTATION = 6

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.disconnect()

esp_now = espnow.ESPNow()
esp_now.active(True)

robotarm_mac = b'\x1c\xc3\xab\xc2\x35\xd4'
esp_now.add_peer(robotarm_mac)

potentiometer_pins = [36, 39, 34, 35, 32, 33]

potentiometre = []

for pin_nummer in potentiometer_pins:
    potentiometer = ADC(Pin(pin_nummer))
    potentiometer.atten(ADC.ATTN_11DB)
    potentiometer.width(ADC.WIDTH_12BIT)
    potentiometre.append(potentiometer)

def til_vinkel(adc_værdi):
    return int(adc_værdi * 180 / 4095)

while True:
    servo_vinkler = []

    for potentiometer in potentiometre:
        adc_værdi = potentiometer.read()
        vinkel = til_vinkel(adc_værdi)
        servo_vinkler.append(vinkel)

    servo_data = [
        servo_vinkler[0],  
        servo_vinkler[1],  
        servo_vinkler[2],  
        servo_vinkler[3],  
        servo_vinkler[4],  
        servo_vinkler[4],  
        servo_vinkler[5]   
    ]

    esp_now.send(robotarm_mac, ujson.dumps(servo_data))

    sleep(0.5)