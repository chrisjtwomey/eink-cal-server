import os
import logging
import datetime as dt
from time import sleep
from PIL import Image
from pytz import timezone
from airium import Airium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException


class Homepage:
    def __init__(
        self,
        width,
        height,
    ):
        self.name = "homepage"
        self.log = logging.getLogger(self.name)
        self.image_width = width
        self.image_height = height

        self.airium = Airium()

    def generate(
        self,
        weather_service,
        maps_service,
        location
    ):
        a = self.airium

        now = dt.datetime.now()
        self.log.info("Time synchronised to %s", now)
        now_date = now.date()

        current = weather_service.current_forecast()
        forecasts = weather_service.three_hour_daily_forecast()
        map_url = maps_service.get_url(location)

        a("<!DOCTYPE html>")
        with a.html(lang="en"):
            with a.head():
                a.meta(charset="utf-8", name="viewport", content="width=device-width, initial-scale=1")
                a.title(_t="Calendar")
                a.link(rel="stylesheet", href="assets/styles.css")

            with a.body():
                with a.div(klass="bg-container"):
                    with a.div(id="top-banner", klass="container"):
                        with a.div():
                            a.h3(
                                id="date", 
                                klass="numcircle text-center",
                                _t=now_date.day,
                            )

                            a.h3(
                                id="month",
                                klass="month text-center text-uppercase",
                                _t=now_date.strftime("%B"),
                            )

                        a.h4(
                                id="temp",
                                klass="numcircle text-center",
                                _t=str(forecasts[0]["temp"]["real"]) + current["temp"]["unit"],
                            )

                with a.div(id="map-container"):
                    a.img(src=map_url, id="map")

                with a.div(klass="bg-container"):
                    with a.div(id="bottom-banner", klass="container"):
                        with a.div(id="hourly-forecasts"):
                            with a.table():
                                with a.thead(klass="forecast-hour"):
                                    with a.tr():
                                        for forecast in forecasts:
                                            with a.td(klass="hour"):
                                                hour = ""
                                                try:
                                                    hour = forecast["dt"].strftime("%-I")
                                                except ValueError as ve:
                                                    # platform-specific formatting error
                                                    self.log.warning(str(ve))
                                                    hour = forecast["dt"].strftime("%I")

                                                a(hour + forecast["dt"].strftime("%p").lower())

                                with a.tbody(klass="hourly-forecasts-forecast"):
                                    with a.tr():
                                        for forecast in forecasts:
                                            with a.td():
                                                with a.div(klass="hourly-forecast-icon fc-icon"):
                                                    a.img(src=forecast["icon"])
                                    with a.tr():
                                        for forecast in forecasts:
                                            with a.td():
                                                with a.div(klass="fc-icon-stat"):
                                                    with a.div(klass="fc-icon"):
                                                        a.img(src="assets/icon/thermometer.png")
                                                    with a.div(klass="fc-stat"):
                                                        a.p(_t=str(forecast["temp"]["real"]) + forecast["temp"]["unit"])
                                    with a.tr():
                                        for forecast in forecasts:
                                            with a.td():
                                                with a.div(klass="fc-icon-stat"):
                                                    with a.div(klass="fc-icon"):
                                                        a.img( src="assets/icon/precip.png")
                                                    with a.div(klass="fc-stat"):
                                                        a.p(_t=str(forecast["precip_percentage"]) + "%")

                

    def save(self):
        cwd = os.path.dirname(os.path.realpath(__file__))
        html_fp = os.path.join("views", "html", self.name + ".html")
        abs_html_fp = "file://" + os.path.join(cwd, "html", self.name + ".html")
        png_fp = os.path.join(cwd, "png", self.name + ".png")

        with open(html_fp, "wb") as f:
            f.write(bytes(self.airium))
            f.close()

        driver = self._get_chromedriver()
        driver.get(abs_html_fp)
        sleep(1)
        driver.get_screenshot_as_file(png_fp)
        driver.quit()

        img = Image.open(png_fp)
        img.save(png_fp, format="png", optimize=True, quality=25)

        self.log.info("Screenshot captured and saved to file.")

    def _get_chromedriver(self):
        opts = Options()
        opts.add_argument("--headless")
        opts.add_argument("--hide-scrollbars")
        opts.add_argument("--window-size={},{}".format(self.image_width, self.image_height))
        opts.add_argument("--force-device-scale-factor=1")

        driver = None
        try:
            driver = webdriver.Chrome(ChromeDriverManager().install(), options=opts)
        except Exception as e:
            self.log.warning(e)
            try:
                driver = webdriver.Chrome(options=opts)
            except WebDriverException as wde:
                raise wde 

        driver.set_window_rect(width=self.image_width, height=self.image_height)

        return driver
