from rpi_ws281x import PixelStrip, Color
import time

LED_COUNT = 12

ring1 = PixelStrip(LED_COUNT, 12, 800000, 10, False, 200, 0)
ring2 = PixelStrip(LED_COUNT, 13, 800000, 10, False, 200, 1)

ring1.begin()
ring2.begin()

for i in range(LED_COUNT):
    ring1.setPixelColor(i, Color(255, 255, 255))
    ring2.setPixelColor(i, Color(255, 255, 255))

ring1.show()
ring2.show()

while True:
    time.sleep(1)
