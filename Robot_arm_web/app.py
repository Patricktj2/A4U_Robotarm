from flask import Flask, render_template, redirect, url_for
from picamera2 import Picamera2
from datetime import datetime
import time
from sqlite3 import Connection
import urllib.request


app = Flask(__name__)

ESP_IP = "192.168.0.3"


def select_all_images():
    con = Connection("dataarm.db")
    cur = con.cursor()

    cur.execute("""SELECT filnavn, Dato_tid FROM A4U_images ORDER BY rowid DESC""")
    img_rows = cur.fetchall()

    con.close()
    return img_rows


def select_latest_image():
    con = Connection("dataarm.db")
    cur = con.cursor()

    cur.execute("""SELECT filnavn, Dato_tid FROM A4U_images ORDER BY rowid DESC LIMIT 1""")
    img_row = cur.fetchone()

    con.close()
    return img_row


def insert_img(filnavn):
    con = Connection("dataarm.db")
    cur = con.cursor()

    dato_tid = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    params = (filnavn, 2, dato_tid)

    sql = """INSERT INTO A4U_images (filnavn, antal_sorteret, Dato_tid) VALUES (?, ?, ?)"""
    cur.execute(sql, params)

    con.commit()
    con.close()


def take_picture():
    filnavn = datetime.now().strftime("%d-%m-%Y-%H-%M-%S.jpg")

    picam = Picamera2()
    config = picam.create_still_configuration(
        main={"size": (640, 480)},
        buffer_count=1
    )

    picam.configure(config)
    picam.start()
    time.sleep(2)

    picam.capture_file(f"static/img/{filnavn}")

    picam.stop()
    picam.close()

    insert_img(filnavn)


def select_taeller():
    con = Connection("dataarm.db")
    cur = con.cursor()

    cur.execute("""SELECT farve, antal FROM "tæller" """)
    rows = cur.fetchall()

    con.close()
    return rows


@app.route("/")
def home():
    latest = select_latest_image()
    taeller_rows = select_taeller()

    return render_template("home.html",
        image=latest[0],
        dato_tid=latest[1],
        taeller_rows=taeller_rows
    )


@app.route("/take_photo/")
def take_photo():
    take_picture()
    return redirect(url_for("home"))


@app.route("/galleri/")
def galleri():
    image_rows = select_all_images()
    return render_template("galleri.html", image_rows=image_rows)


@app.route("/robot_on/")
def robot_on():
    urllib.request.urlopen(f"http://{ESP_IP}/on")
    return redirect(url_for("home"))


@app.route("/robot_off/")
def robot_off():
    urllib.request.urlopen(f"http://{ESP_IP}/off")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)