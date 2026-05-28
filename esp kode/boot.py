import network
import time
import machine
from secrets import SSID, PASSWORD, STATIC_IP, SUBNET_MASK, GATEWAY

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.ifconfig((STATIC_IP, SUBNET_MASK, GATEWAY, GATEWAY))
wlan.connect(SSID, PASSWORD)
machine.freq(240000000)

timeout = 20
while not wlan.isconnected() and timeout > 0:
    time.sleep(1)
    timeout -= 1

if not wlan.isconnected():
    machine.reset()

