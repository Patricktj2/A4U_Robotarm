import cv2
import numpy as np
import time
import requests
import sqlite3
from picamera2 import Picamera2

ESP32_IP = "192.168.0.3"

COLOR_RANGES = {
    "red":      [(np.array([140, 120, 70]), np.array([180, 255, 255]))],
    "yellow":   [(np.array([20, 100, 100]), np.array([35, 255, 255]))],
    "green":    [(np.array([40, 70, 70]), np.array([90, 255, 255]))]
}

picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (640, 480)})
picam2.configure(config)
picam2.start()
time.sleep(2)

picture = picam2.capture_array()
picam2.stop()
picture = cv2.cvtColor(picture, cv2.COLOR_RGB2BGR)
picture_copy = picture.copy()
picture_copy[400:, 0:] = 0
picture_copy[:400, :100] = 0
picture_copy[:400, 600:] = 0
picture_copy[:50, :600] = 0
picture_copy[:150, :200] = 0
picture_copy[:300, :150] = 0
picture_copy = cv2.rotate(picture_copy, cv2.ROTATE_180)
picture_copy_website = picture.copy()
hsv_picture = cv2.cvtColor(picture, cv2.COLOR_BGR2HSV)
hsv_picture[400:, 0:] = 0
hsv_picture[:400, :100] = 0
hsv_picture[:400, 600:] = 0
hsv_picture[:50, :600] = 0
hsv_picture[:150, :200] = 0
hsv_picture[:300, :150] = 0
hsv_picture = cv2.rotate(hsv_picture, cv2.ROTATE_180)

funde_farver = []
farve_tæller = {"red": 0, "yellow": 0, "green": 0}

def farve_genkend():
    for farve, farve_værdi in COLOR_RANGES.items():
        lower, upper = farve_værdi[0]
        mask = cv2.inRange(hsv_picture, lower, upper)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for område in contours:
            if cv2.contourArea(område) < 400:
                continue

            M = cv2.moments(område)
            if M["m00"] == 0:
                continue

            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])

            cv2.circle(picture_copy, (cx, cy), 10, (230, 50, 150), -1)
            cv2.putText(picture_copy, farve, (cx - 20, cy - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (230, 50, 150), 2)

            funde_farver.append((farve, cx, cy))
            farve_tæller[farve] += 1

def tegn_grid(billede, grid_størrelse=50):
    højde, bredde = billede.shape[:2]

    for x in range(0, bredde, grid_størrelse):
        cv2.line(billede, (x, 0), (x, højde), (50, 255, 50), 1)
        cv2.putText(billede, str(x), (x + 2, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (50, 255, 50), 1)

    for y in range(0, højde, grid_størrelse):
        cv2.line(billede, (0, y), (bredde, y), (50, 255, 50), 1)
        cv2.putText(billede, str(y), (2, y + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (50, 255, 50), 1)

    return billede

def ping():
    r = requests.get(f"http://{ESP32_IP}/ping", timeout=3)
    print("Ping svar:", r.text)

def home():
    r = requests.post(f"http://{ESP32_IP}/home", timeout=5)
    print("Home svar:", r.text)

def sort(farve, cx, cy):
    r = requests.post(f"http://{ESP32_IP}/sort", json={"farve": farve, "cx": cx, "cy": cy}, timeout=60)
    print("Sort svar:", r.text)

def vent_på_esp():
    while True:
        try:
            svar = requests.get(f"http://{ESP32_IP}/ping", timeout=3)
            data = svar.json()

            if not data.get("busy", False):
                break

        except Exception:
            pass

        time.sleep(1)

def sort_esp():
    for farve, cx, cy in funde_farver:
        vent_på_esp()
        sort(farve, cx, cy)

def sort_website():
    conn = sqlite3.connect("/home/gruppe3/Robot_arm_web/dataarm.db")
    cur = conn.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS tæller (farve TEXT PRIMARY KEY, antal INTEGER)''')

    for farve, antal in farve_tæller.items():
        cur.execute('INSERT OR REPLACE INTO tæller VALUES (?, ?)', (farve, antal))

    conn.commit()
    conn.close()

farve_genkend()

picture_copy = tegn_grid(picture_copy)

cv2.imwrite("resultat.jpg", picture_copy)
cv2.imwrite("plade.jpg", picture_copy_website)

sort_website()

try:
    ping()
    home()
    sort_esp()

except Exception as e:
    print("Ingen forbindelse til esp, Error:", e)
