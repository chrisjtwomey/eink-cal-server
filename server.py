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
from flask import Flask, send_file, request, abort
from werkzeug.serving import make_server
from pytz import timezone
from views.homepage import Homepage
from weather.weather import WeatherService

app = Flask(__name__)
has_served = False
client_user_agent = "tinys3"

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
def serve_cal_png():
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


def main():
    # Basic configuration settings (user replaceable)
    configFile = open(os.path.join(cwd, "config.json"))
    config = json.load(configFile)

    displayTZ = timezone(
        config["timezone"]
    )  # list of timezones - print(pytz.all_timezones)
    weekStartDay = config["weekStartDay"]  # Monday = 0, Sunday = 6
    imageWidth = config["imageWidth"]  # Width of image to be generated for display.
    imageHeight = config["imageHeight"]  # Height of image to be generated for display.
    rotateAngle = config[
        "rotateAngle"
    ]  # If image is rendered in portrait orientation, angle to rotate to fit screen
    client_user_agent = config["clientUserAgent"]
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

    log.info("Served esp32 client, shutting down")
    sys.exit(0)


if __name__ == "__main__":
    main()
