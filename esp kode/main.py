import usocket
import ujson
import espnow
from machine import Pin, I2C
from time import sleep_ms

SDA_PIN  = 22
SCL_PIN  = 21
PCA_ADDR = 0x40

MODE1     = 0x00
MODE2     = 0x01
PRESCALE  = 0xFE
LED0_ON_L = 0x06
FREQ_HZ   = 50

GRIBBER          = 0
GRIBBER_ROTATION = 1
HAANDLED         = 2
ALBUE            = 3
SKULDER_1        = 4  
SKULDER_2        = 5
BASE_ROTATION    = 6

ALL_CHANNELS = [GRIBBER, GRIBBER_ROTATION, HAANDLED, ALBUE, SKULDER_1, SKULDER_2, BASE_ROTATION]

MOVE_STEP_US        = 7   
MOVE_DELAY_MS       = 12  
WRIST_MOVE_STEP_US  = 5   
WRIST_MOVE_DELAY_MS = 12
STEP_DELAY_MS       = 220 
FIRST_DELAY_MS      = 250 
GRAB_DELAY_MS       = 350 
DROP_DELAY_MS       = 400 

GRIBBER_LUKKET = 1200
GRIBBER_AABEN  = 2150

ALBUE_SAFE        = 1400
SHOULDER_TRAVEL_1 = 2400  
SHOULDER_TRAVEL_2 = 600

HOME_GRIBBER          = 1700
HOME_GRIBBER_ROTATION = 1500
HOME_HAANDLED         = 1950
HOME_ALBUE            = 2600
HOME_SKULDER_1        = 3000
HOME_SKULDER_2        = 0
HOME_BASE             = 2500

HOME_OFF_CHANNELS = [GRIBBER, GRIBBER_ROTATION, BASE_ROTATION]

OLD_HOME_HAANDLED = 1300
HAANDLED_OFFSET   = HOME_HAANDLED - OLD_HOME_HAANDLED

def wrist_old(old_value):
    return int(old_value + HAANDLED_OFFSET)

HAANDLED_PICK         = wrist_old(1900)  
HAANDLED_BOX_STANDARD = wrist_old(1900)  
HAANDLED_BOX_ROD      = wrist_old(1990)  

BOXES = {
    "yellow": {
        "name":           "Gul boks",
        GRIBBER_ROTATION: 1500,
        HAANDLED:         HAANDLED_BOX_STANDARD,
        ALBUE:            2060,
        SKULDER_1:        2120,
        SKULDER_2:        880,
        BASE_ROTATION:    800
    },
    "green": {
        "name":           "Grøn boks",
        GRIBBER_ROTATION: 1500,
        HAANDLED:         HAANDLED_BOX_STANDARD,
        ALBUE:            2110,
        SKULDER_1:        2120,
        SKULDER_2:        880,
        BASE_ROTATION:    1100
    },
    "red": {
        "name":           "Rød boks",
        GRIBBER_ROTATION: 1500,
        HAANDLED:         HAANDLED_BOX_ROD,
        ALBUE:            2110,
        SKULDER_1:        2120,
        SKULDER_2:        880,
        BASE_ROTATION:    1300
    }
}

PICK_PUNKTER = {
    "top_venstre": {
        "pixel":       (110, 80),
        HAANDLED:      HAANDLED_PICK,
        ALBUE:         1400,
        SKULDER_1:     1640,
        SKULDER_2:     1360,
        BASE_ROTATION: 2300
    },
    "top_hoejre": {
        "pixel":       (530, 80),
        HAANDLED:      HAANDLED_PICK,
        ALBUE:         1400,
        SKULDER_1:     1640,
        SKULDER_2:     1360,
        BASE_ROTATION: 2900
    },
    "bund_venstre": {
        "pixel":       (110, 390),
        HAANDLED:      HAANDLED_PICK,
        ALBUE:         2060,
        SKULDER_1:     1830,
        SKULDER_2:     1170,
        BASE_ROTATION: 2000
    },
    "bund_hoejre": {
        "pixel":       (530, 390),
        HAANDLED:      HAANDLED_PICK,
        ALBUE:         2060,
        SKULDER_1:     1830,
        SKULDER_2:     1170,
        BASE_ROTATION: 2900
    }
}

current_us = {
    GRIBBER:          HOME_GRIBBER,
    GRIBBER_ROTATION: HOME_GRIBBER_ROTATION,
    HAANDLED:         HOME_HAANDLED,
    ALBUE:            HOME_ALBUE,
    SKULDER_1:        HOME_SKULDER_1,
    SKULDER_2:        HOME_SKULDER_2,
    BASE_ROTATION:    HOME_BASE
}

enabled    = {ch: False for ch in ALL_CHANNELS}
auto_busy  = False

class PCA9685:
    def __init__(self, i2c, address):
        self.i2c     = i2c
        self.address = address
        self.reset()
        self.set_pwm_freq(FREQ_HZ)

    def write8(self, reg, value):
        self.i2c.writeto_mem(self.address, reg, bytes([value & 0xFF]))

    def read8(self, reg):
        return self.i2c.readfrom_mem(self.address, reg, 1)[0]

    def reset(self):
        self.write8(MODE1, 0x00)
        sleep_ms(10)

    def set_pwm_freq(self, freq_hz):
        prescale = int(25000000.0 / 4096.0 / float(freq_hz) - 1.0 + 0.5)
        oldmode  = self.read8(MODE1)
        self.write8(MODE1, (oldmode & 0x7F) | 0x10)  
        self.write8(PRESCALE, prescale)
        self.write8(MODE1, oldmode)
        sleep_ms(5)
        self.write8(MODE1, oldmode | 0xA1)            
        self.write8(MODE2, 0x04)

    def set_pwm(self, channel, on, off):
        off  = max(0, min(4095, off))
        reg  = LED0_ON_L + 4 * channel
        data = bytes([on & 0xFF, (on >> 8) & 0xFF, off & 0xFF, (off >> 8) & 0xFF])
        self.i2c.writeto_mem(self.address, reg, data)

    def off(self, channel):
        reg  = LED0_ON_L + 4 * channel
        data = bytes([0, 0, 0, 0x10])
        self.i2c.writeto_mem(self.address, reg, data)

def us_to_tick(us):
    return max(0, min(4095, int((int(us) * 4096) / 20000)))

def set_servo_us(channel, us):
    pca.set_pwm(channel, 0, us_to_tick(int(us)))
    current_us[channel] = int(us)
    enabled[channel]    = True

def release_channel(channel):
    pca.off(channel)
    enabled[channel] = False

def release_all():
    for ch in ALL_CHANNELS:
        release_channel(ch)

def smooth_move(targets):
    for ch in targets:
        targets[ch] = int(targets[ch])

    if HAANDLED in targets:
        step_us  = WRIST_MOVE_STEP_US
        delay_ms = WRIST_MOVE_DELAY_MS
    else:
        step_us  = MOVE_STEP_US
        delay_ms = MOVE_DELAY_MS

    max_diff = max(abs(targets[ch] - current_us[ch]) for ch in targets)

    if max_diff == 0:
        for ch in targets:
            set_servo_us(ch, targets[ch])
        return

    steps        = max(1, max_diff // step_us + (1 if max_diff % step_us != 0 else 0))
    start_values = {ch: current_us[ch] for ch in targets}

    for i in range(1, steps + 1):
        for ch in targets:
            new_us = start_values[ch] + ((targets[ch] - start_values[ch]) * i) // steps
            set_servo_us(ch, new_us)
        sleep_ms(delay_ms)

    for ch in targets:
        set_servo_us(ch, targets[ch])

def move_step(targets):
    smooth_move(targets)
    sleep_ms(STEP_DELAY_MS)

def clamp(value, low, high):
    return max(low, min(high, value))

def lerp(a, b, t):
    return a + (b - a) * t

def interpoler(cx, cy):
    tl = PICK_PUNKTER["top_venstre"]
    tr = PICK_PUNKTER["top_hoejre"]
    bl = PICK_PUNKTER["bund_venstre"]
    br = PICK_PUNKTER["bund_hoejre"]

    tx = clamp((cx - tl["pixel"][0]) / (tr["pixel"][0] - tl["pixel"][0]), 0.0, 1.0)
    ty = clamp((cy - tl["pixel"][1]) / (bl["pixel"][1] - tl["pixel"][1]), 0.0, 1.0)

    base      = int(lerp(lerp(tl[BASE_ROTATION], tr[BASE_ROTATION], tx),
                         lerp(bl[BASE_ROTATION], br[BASE_ROTATION], tx), ty))
    albue     = int(lerp(lerp(tl[ALBUE],         tr[ALBUE],         tx),
                         lerp(bl[ALBUE],         br[ALBUE],         tx), ty))
    skulder_1 = int(lerp(lerp(tl[SKULDER_1],     tr[SKULDER_1],     tx),
                         lerp(bl[SKULDER_1],     br[SKULDER_1],     tx), ty))
    skulder_2 = int(lerp(lerp(tl[SKULDER_2],     tr[SKULDER_2],     tx),
                         lerp(bl[SKULDER_2],     br[SKULDER_2],     tx), ty))

    return base, albue, skulder_1, skulder_2

def go_home():
    move_step({SKULDER_1: HOME_SKULDER_1, SKULDER_2: HOME_SKULDER_2})
    sleep_ms(FIRST_DELAY_MS)
    move_step({HAANDLED: HOME_HAANDLED})
    sleep_ms(FIRST_DELAY_MS)
    move_step({ALBUE: HOME_ALBUE})
    sleep_ms(FIRST_DELAY_MS)
    move_step({GRIBBER: HOME_GRIBBER, GRIBBER_ROTATION: HOME_GRIBBER_ROTATION, BASE_ROTATION: HOME_BASE})
    for ch in HOME_OFF_CHANNELS:
        release_channel(ch)

def go_sort_safe():
    move_step({ALBUE: ALBUE_SAFE})
    sleep_ms(FIRST_DELAY_MS)
    move_step({SKULDER_1: SHOULDER_TRAVEL_1, SKULDER_2: SHOULDER_TRAVEL_2})
    sleep_ms(FIRST_DELAY_MS)

def go_to_pick(base, albue, skulder_1, skulder_2):
    move_step({ALBUE: ALBUE_SAFE})
    sleep_ms(FIRST_DELAY_MS)

    move_step({HAANDLED: HAANDLED_PICK})
    sleep_ms(FIRST_DELAY_MS)

    move_step({SKULDER_1: SHOULDER_TRAVEL_1, SKULDER_2: SHOULDER_TRAVEL_2})
    sleep_ms(FIRST_DELAY_MS)

    move_step({BASE_ROTATION: base, GRIBBER_ROTATION: 1500})
    sleep_ms(FIRST_DELAY_MS)

    move_step({GRIBBER: GRIBBER_AABEN})
    sleep_ms(180)

    move_step({SKULDER_1: skulder_1, SKULDER_2: skulder_2})

def grab(albue):
    move_step({ALBUE: albue})            
    sleep_ms(180)
    move_step({GRIBBER: GRIBBER_LUKKET}) 
    sleep_ms(GRAB_DELAY_MS)
    move_step({ALBUE: ALBUE_SAFE})        
    sleep_ms(180)

def go_to_box(box):
    move_step({ALBUE: ALBUE_SAFE})
    sleep_ms(FIRST_DELAY_MS)
    move_step({HAANDLED: box[HAANDLED]})
    sleep_ms(FIRST_DELAY_MS)
    move_step({SKULDER_1: box[SKULDER_1], SKULDER_2: box[SKULDER_2]})
    sleep_ms(FIRST_DELAY_MS)
    move_step({BASE_ROTATION: box[BASE_ROTATION]})
    move_step({GRIBBER_ROTATION: box[GRIBBER_ROTATION]})
    move_step({ALBUE: box[ALBUE]})

def drop():
    move_step({GRIBBER: GRIBBER_AABEN})  
    sleep_ms(DROP_DELAY_MS)
    move_step({ALBUE: ALBUE_SAFE})
    sleep_ms(180)

def sort_brick(farve, cx, cy):
    global auto_busy

    if farve not in BOXES:
        return False

    auto_busy = True

    try:
        base, albue, skulder_1, skulder_2 = interpoler(cx, cy)

        go_to_pick(base, albue, skulder_1, skulder_2)
        grab(albue)
        go_to_box(BOXES[farve])
        drop()
        go_sort_safe()

    finally:
        auto_busy = False  

    return True

def start_server():
    addr = usocket.getaddrinfo("0.0.0.0", 80)[0][-1]
    server_socket    = usocket.socket()
    server_socket.setsockopt(usocket.SOL_SOCKET, usocket.SO_REUSEADDR, 1)
    server_socket.bind(addr)
    server_socket.listen(5)
    server_socket.settimeout(0)
    print("HTTP server klar på port 80")
    return server_socket

def parse_request(raw):
    try:
        idx = raw.find("\r\n\r\n")
        if idx == -1:
            return None
        return ujson.loads(raw[idx + 4:])
    except Exception:
        return None

def send_response(conn, data):
    body = ujson.dumps(data)
    http = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n" + body
    conn.send(http.encode())

def handle_http(server):
    try:
        conn, addr = server.accept()
    except Exception:
        return

    try:
        raw = conn.recv(1024).decode("utf-8")

        if "POST /sort" in raw:
            if auto_busy:
                send_response(conn, {"status": "busy"})
            else:
                data = parse_request(raw)
                if data and "farve" in data and "cx" in data and "cy" in data:
                    success = sort_brick(data["farve"], int(data["cx"]), int(data["cy"]))
                    send_response(conn, {"status": "ok" if success else "unknown_color"})
                else:
                    send_response(conn, {"status": "bad_request"})

        elif "POST /home" in raw:
            go_home()
            send_response(conn, {"status": "ok"})

        elif "GET /ping" in raw:
            send_response(conn, {"status": "alive", "busy": auto_busy})

        else:
            send_response(conn, {"status": "not_found"})

    except Exception as e:
        try:
            send_response(conn, {"status": "error", "msg": str(e)})
        except Exception:
            pass

    finally:
        conn.close()

def start_espnow():
    host, msg = esp.recv(0) 
    if msg:
        try:
            vinkler = ujson.loads(msg.decode('utf-8'))
            
            for kanal in range(7):
                us_vaerdi = 500 + int((vinkler[kanal] * 2000) / 180)
                set_servo_us(kanal, us_vaerdi)
                
        except Exception:
            pass 

i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=400000)

print("Scanner I2C...")
devices = i2c.scan()

if PCA_ADDR not in devices:
    print("FEJL: PCA9685 ikke fundet")
    raise SystemExit

print("PCA9685 fundet")
pca = PCA9685(i2c, PCA_ADDR)

release_all()
sleep_ms(700)

go_home()

server = start_server()
print("Klar. Lytter på HTTP fra Pi")

esp = espnow.ESPNow()
esp.active(True)

while True:
    handle_http(server)
    start_espnow()
    sleep_ms(20)
