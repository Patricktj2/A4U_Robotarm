PI_IP   = '192.168.0.2'
PI_PORT = 5000

I2C_SDA_PIN = 22
I2C_SCL_PIN = 21

PCA_ADDR_1 = 0x40

HOME = {
    'gribber':          1700,
    'gribber_rotation': 1500,
    'haandled':         1950,
    'albue':            2600,
    'skulder_1':        3000,
    'skulder_2':        0,
    'base':             2500,
}

GRIBBER_AABEN   = 1700
GRIBBER_LUKKET  = 2000
HAANDLED_PICK   = 1900

PICK_PUNKTER = {
    "top_højre": {
        "pixel": (550, 50),      
        "albue":    1400,
        "skulder_1": 1640,
        "skulder_2": 1360,
        "base":     2900,
    },
    "top_venstre": {
        "pixel": (150, 150),    
        "albue":    1400,
        "skulder_1": 1640,
        "skulder_2": 1360,
        "base":     2300,
    },
    "bund_venstre": {
        "pixel": (100, 350),     
        "albue":    2060,
        "skulder_1": 1830,
        "skulder_2": 1170,
        "base":     2100,
    },
    "bund_højre": {
        "pixel": (600, 350),     
        "albue":    2060,
        "skulder_1": 1830,
        "skulder_2": 1170,
        "base":     2900,
    },
}

DROP_POSITIONS = {
    'yellow': {
        'gribber':          GRIBBER_AABEN,
        'gribber_rotation': 1500,
        'haandled':         1900,
        'albue':            2060,
        'skulder_1':        2120,
        'skulder_2':        880,
        'base':             800,
    },
    'green': {
        'gribber':          GRIBBER_AABEN,
        'gribber_rotation': 1500,
        'haandled':         1900,
        'albue':            2110,
        'skulder_1':        2120,
        'skulder_2':        880,
        'base':             1100,
    },
    'red': {
        'gribber':          GRIBBER_AABEN,
        'gribber_rotation': 1500,
        'haandled':         1990,
        'albue':            2110,
        'skulder_1':        2120,
        'skulder_2':        880,
        'base':             1300,
    },
}

MOVE_DELAY_MS = 800
GRIP_DELAY_MS = 500