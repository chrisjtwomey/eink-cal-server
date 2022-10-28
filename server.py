#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import io
import sys
import json
import time
import threading
import datetime as dt
import logging.config
import paho.mqtt.client as mqtt
from flask import Flask, send_file, request, abort
from werkzeug.serving import make_server
from pytz import timezone
from views.homepage import Homepage
from weather.weather import WeatherService

app = Flask(__name__)
has_served = False
client_user_agent = "tinys3"
use_user_agent = False

cwd = os.path.dirname(os.path.realpath(__file__))

# Create and configure logger
logging.config.fileConfig(os.path.join(cwd, "logging.dev.ini"))
log = logging.getLogger("server")


class ServerThread(threading.Thread):
    def __init__(self, app, user_agent):
        threading.Thread.__init__(self)
        self.server = make_server("0.0.0.0", 8080, app)
        self.ctx = app.app_context()
        self.ctx.push()
        self.serve_user_agent = user_agent
        self.has_served = False

    def run(self):
        log.info("starting http server")
        self.server.serve_forever()

    def shutdown(self, timeout=60):
        log.info(f"stopping http server in {timeout} seconds")
        time.sleep(timeout)
        self.server.shutdown()


@app.route("/homepage.bmp")
def serve_cal_bmp():
    global has_served, client_user_agent
    """
    Returns the calendar image directly through send_file
    """
    user_agent = request.headers.get("User-Agent")
    if user_agent is not None and user_agent == client_user_agent:
        has_served = True

    bmp_path = os.path.join(cwd, "views/bmp/homepage.bmp")

    if not os.path.exists(bmp_path):
        log.error(f"{bmp_path}: no such file exists")
        abort(404)

    f = open(bmp_path, "rb")
    stream = io.BytesIO(f.read())

    return send_file(
        stream, mimetype="image/bmp", as_attachment=True, download_name=f"homepage.bmp"
    )

@app.route("/homepage.png")
def serve_cal_png():
    global has_served, client_user_agent, use_user_agent
    """
    Returns the calendar image directly through send_file
    """
    user_agent = request.headers.get("User-Agent")
    if user_agent is not None and user_agent == client_user_agent:
        has_served = True

    png_path = os.path.join(cwd, "views/png/homepage.png")

    if not os.path.exists(png_path):
        log.error(f"{png_path}: no such file exists")
        abort(404)

    f = open(png_path, "rb")
    stream = io.BytesIO(f.read())

    has_served = True

    return send_file(
        stream, mimetype="image/png", as_attachment=True, download_name=f"homepage.png"
    )


def main():
    # Basic configuration settings (user replaceable)
    configFile = open(os.path.join(cwd, "config.json"))
    config = json.load(configFile)

    displayTZ = timezone(
        config["timezone"]
    )  # list of timezones - print(pytz.all_timezones)
    weekStartDay = config["weekStartDay"]  # Monday = 0, Sunday = 6
    imageWidth = config["imageWidth"] 
    imageHeight = config["imageHeight"]
    rotateAngle = config[
        "rotateAngle"
    ]  # If image is rendered in portrait orientation, angle to rotate to fit screen
    client_user_agent = config["clientUserAgent"]
    use_user_agent = config["useUserAgent"]
    use_server = config["useServer"]
    max_wait_serve_seconds = config["maxWaitServerMinutes"] * 60

    apikey = config["weather"]["apikey"]
    location = config["weather"]["location"]

    weather = WeatherService(apikey, location, debug=False)

    log.info("Starting daily calendar update")

    try:
        homepage = Homepage(imageWidth, imageHeight, rotateAngle)
        homepage.generate(
            weather_service=weather
        )
        homepage.save()

    except Exception as e:
        raise e
        # log.error(e)

    log.info("Completed daily calendar update")

    if not use_server:
        sys.exit(0)

    mqtt_client = mqtt.Client("eink-cal-server")
    def on_connect(client, userdata, flags, rc):
        if rc != 0:
            log.error("Connection calendar client logging broker failed")
        
        log.info("Connected to calendar client logging broker")

    def on_disconnect(client, userdata, rc):
        if rc != 0:
            log.error("Unexpected broker disconnection")

        log.info("Disconnected from calendar client logging broker")

    def on_message(client, userdata, message):
        log.info("Cal client: {}".format(message.payload.decode()))

    mqtt_client.on_connect=on_connect
    mqtt_client.on_disconnect=on_disconnect
    mqtt_client.on_message=on_message
    try:
        mqtt_client.connect(
            config["mqtt"]["host"], 
            config["mqtt"]["port"], 
            60
        )
    except Exception as e:
        log.error(e)
        
    mqtt_client.subscribe(config["mqtt"]["topic"])
    mqtt_client.loop_start()

    log.info("Serving calendar image for esp32 client")

    http_server = ServerThread(app, client_user_agent)
    http_server.start()

    log.info(
        "Waiting {} seconds to serve esp32 client before shutdown".format(
            max_wait_serve_seconds
        )
    )
    start_wait_dt = dt.datetime.now(displayTZ)
    diff = dt.datetime.now(displayTZ) - start_wait_dt
    while not has_served and diff.seconds < max_wait_serve_seconds:
        time.sleep(1)
        diff = dt.datetime.now(displayTZ) - start_wait_dt
    http_server.shutdown(timeout=120)

    if not has_served:
        log.error("Timeout waiting to server esp32 client, exiting")
        sys.exit(1)

    mqtt_client.loop_stop()
    mqtt_client.disconnect()

    log.info("Served esp32 client, shutting down")
    sys.exit(0)


if __name__ == "__main__":
    main()
