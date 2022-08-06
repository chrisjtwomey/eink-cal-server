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
from flask import Flask, send_file, request
from werkzeug.serving import make_server
from pytz import timezone
from render.render import RenderHelper

app = Flask(__name__)
has_served = False

cwd = os.path.dirname(os.path.realpath(__file__))

# Create and configure logger
logging.config.fileConfig(os.path.join(cwd, "logging.dev.ini"))
log = logging.getLogger("server")

class ServerThread(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.server = make_server("0.0.0.0", 8080, app)
        self.ctx = app.app_context()
        self.ctx.push()
        self.has_served = False

    def run(self):
        log.info("starting http server")
        self.server.serve_forever()

    def shutdown(self):
        log.info("stopping http server")
        self.server.shutdown()

@app.route('/calendar.png')
def serve_cal_png():
    global has_served
    """
    Returns the calendar image directly through send_file
    """
    client = request.args.get("client")
    if client is not None and client == "esp32":
        has_served = True
    f = open(os.path.join(cwd, 'render/calendar.png'), "rb")
    stream = io.BytesIO(f.read())
    return send_file(
        stream, 
        mimetype='image/png',
        as_attachment=True,
        download_name="calendar.png"
    )

def main():
    # Basic configuration settings (user replaceable)
    configFile = open(os.path.join(cwd, 'config.json'))
    config = json.load(configFile)

    displayTZ = timezone(config['displayTZ']) # list of timezones - print(pytz.all_timezones)
    thresholdHours = config['thresholdHours']  # considers events updated within last 12 hours as recently updated
    maxEventsPerDay = config['maxEventsPerDay']  # limits number of events to display (remainder displayed as '+X more')
    weekStartDay = config['weekStartDay']  # Monday = 0, Sunday = 6
    dayOfWeekText = config['dayOfWeekText'] # Monday as first item in list
    screenWidth = config['screenWidth']  # Width of E-Ink display. Default is landscape. Need to rotate image to fit.
    screenHeight = config['screenHeight']  # Height of E-Ink display. Default is landscape. Need to rotate image to fit.
    imageWidth = config['imageWidth']  # Width of image to be generated for display.
    imageHeight = config['imageHeight'] # Height of image to be generated for display.
    rotateAngle = config['rotateAngle']  # If image is rendered in portrait orientation, angle to rotate to fit screen
    calendars = config['calendars']  # Google calendar ids
    is24hour = config['is24h']  # set 24 hour time
    use_server = config["useServer"]
    max_wait_serve_seconds = config["maxWaitServerMinutes"] * 60

    log.info("Starting daily calendar update")

    try:
        # Establish current date and time information
        # Note: For Python datetime.weekday() - Monday = 0, Sunday = 6
        # For this implementation, each week starts on a Sunday and the calendar begins on the nearest elapsed Sunday
        # The calendar will also display 5 weeks of events to cover the upcoming month, ending on a Saturday

        currDatetime = dt.datetime.now(displayTZ)
        log.info("Time synchronised to {}".format(currDatetime))
        currDate = currDatetime.date()
        calStartDate = currDate - dt.timedelta(days=((currDate.weekday() + (7 - weekStartDay)) % 7))
        calEndDate = calStartDate + dt.timedelta(days=(5 * 7 - 1))
        calStartDatetime = displayTZ.localize(dt.datetime.combine(calStartDate, dt.datetime.min.time()))
        calEndDatetime = displayTZ.localize(dt.datetime.combine(calEndDate, dt.datetime.max.time()))

        # Using Google Calendar to retrieve all events within start and end date (inclusive)
        start = dt.datetime.now()

        # Populate dictionary with information to be rendered on e-ink display
        calDict = {'calStartDate': calStartDate, 'today': currDate, 'lastRefresh': currDatetime,
                   'dayOfWeekText': dayOfWeekText, 'weekStartDay': weekStartDay, 'maxEventsPerDay': maxEventsPerDay,
                   'is24hour': is24hour}

        renderService = RenderHelper(imageWidth, imageHeight, rotateAngle)
        renderService.process_inputs(calDict)
    except Exception as e:
        log.error(e)

    log.info("Completed daily calendar update")

    if not use_server:
        sys.exit(0)

    log.info("Serving calendar image for esp32 client")

    http_server = ServerThread(app)
    http_server.start()

    log.info("Waiting {} seconds to serve esp32 client before shutdown".format(max_wait_serve_seconds))
    start_wait_dt = dt.datetime.now(displayTZ)
    diff = dt.datetime.now(displayTZ) - start_wait_dt
    while not has_served and diff.seconds < max_wait_serve_seconds:
        time.sleep(1)
        diff = dt.datetime.now(displayTZ) - start_wait_dt
    http_server.shutdown() 
    
    if not has_served:
        log.error("Timeout waiting to server esp32 client, exiting")
        sys.exit(1)

    log.info("Served esp32 client, shutting down")
    sys.exit(0)

if __name__ == "__main__":
    main()
