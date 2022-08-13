import os
import calendar
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
        angle,
    ):
        self.name = "homepage"
        self.log = logging.getLogger(self.name)
        self.image_width = width
        self.image_height = height
        self.rotate_angle = angle

        self.airium = Airium()

    def generate(
        self,
        weather_service=None,
    ):
        a = self.airium

        now = dt.datetime.now()
        self.log.info("Time synchronised to %s", now)
        now_date = now.date()

        a("<!DOCTYPE html>")
        with a.html(lang="en"):
            with a.head():
                a.meta(charset="utf-8")
                a.title(_t="Calendar")
                a.link(rel="stylesheet", href="assets/bootstrap.min.css")
                a.link(rel="stylesheet", href="assets/styles.css")

            with a.body():
                with a.div(klass="container p-0 m-0"):
                    with a.div(klass="calendar bg-white p-3"):
                        with a.div(klass="align-items-center text-center"):
                            a.h3(
                                klass="month font-weight-bold text-uppercase datecircle",
                                _t=now_date.day,
                            )

                        a.h4(
                            klass="month-name text-center text-uppercase",
                            _t=now_date.strftime("%B"),
                        )
                if weather_service is not None:
                    current = weather_service.current_forecast()
                    forecasts = weather_service.three_hour_daily_forecast()

                    with a.div(klass="container fc-curr-container"):
                        with a.div(klass="fc-curr-main"):
                            with a.div(klass="fc-curr-icon"):
                                a.img(klass="fc-icon", src=current["icon"])
                            with a.div(klass="fc-curr-main-temp"):
                                a.p(_t=str(forecasts[0]["temp"]["real"]) + current["temp"]["unit"])

                        with a.div(klass="fc-curr-stats"):
                            with a.table():
                                with a.tr():
                                    with a.td():
                                        with a.div(klass="fc-curr-stats-icon"):
                                            a.img(klass="fc-icon", src="assets/012-rain.png")
                                        with a.div(klass="fc-curr-stats-stat"):
                                            a.p(_t=str(0) + "%")
                                    with a.td():
                                        with a.div(klass="fc-curr-stats-icon"):
                                            a.img(klass="fc-icon", src="assets/020-sunrise.png")
                                        with a.div(klass="fc-curr-stats-stat"):
                                            a.p(_t=current["sunrise"].strftime("%H:%M"))
                                with a.tr():
                                    with a.td():
                                        with a.div(klass="fc-curr-stats-icon"):
                                            a.img(klass="fc-icon", src="assets/029-windy.png")
                                        with a.div(klass="fc-curr-stats-stat"):
                                            a.p(_t=str(current["wind"]["real"]) + current["wind"]["unit"])
                                    with a.td():
                                        with a.div(klass="fc-curr-stats-icon"):
                                            a.img(klass="fc-icon", src="assets/021-sunset.png")
                                        with a.div(klass="fc-curr-stats-stat"):
                                            a.p(_t=current["sunset"].strftime("%H:%M"))

                    with a.div(klass="container"):
                        with a.table(klass="hourly-forecasts"):
                            with a.thead(klass="fc-hours"):
                                with a.tr():
                                    for forecast in forecasts:
                                        a.td(klass="fc-hour", _t=forecast["dt"].strftime("%H"))

                            with a.tbody(klass="fc-forecasts"):
                                with a.tr():
                                    for forecast in forecasts:
                                        with a.td():
                                            a.img(klass="fc-icon", src=forecast["icon"])
                                with a.tr():
                                    for forecast in forecasts:
                                        a.td(klass="fc-temp", _t=str(forecast["temp"]["real"]) + forecast["temp"]["unit"])

                                with a.tr():
                                    for forecast in forecasts:
                                        with a.td():
                                            with a.div(klass="fc-rain-perc"):
                                                a.p(_t=str(forecast["precip_percentage"]) + "%")
                                            with a.div(klass="fc-rain-icon"):
                                                a.img(klass="fc-icon", src="assets/012-rain.png")

                    


    def save(self):
        cwd = os.path.dirname(os.path.realpath(__file__))
        html_fp = os.path.join("views", "html", self.name + ".html")
        abs_html_fp = "file://" + os.path.join(cwd, "html", self.name + ".html")
        png_fp = os.path.join("views", "png", self.name + ".png")
        bmp_fp = os.path.join("views", "bmp", self.name + ".bmp")

        with open(html_fp, "wb") as f:
            f.write(bytes(self.airium))
            f.close()

        driver = self._get_chromedriver()
        driver.get(abs_html_fp)
        driver.execute_script("document.body.style.zoom='50%'")
        sleep(1)
        driver.get_screenshot_as_file(png_fp)
        driver.quit()

        # convert to bmp
        img = Image.open(png_fp)
        # img = img.rotate(self.rotate_angle, expand=True)
        img = img.convert("P", palette=Image.ADAPTIVE, colors=256)
        # reduce filesize as much as possible
        img.save(bmp_fp, format="bmp", optimize=True, quality=5)

        self.log.info("Screenshot captured and saved to file.")

    def _get_chromedriver(self):
        opts = Options()
        opts.add_argument("--headless")
        opts.add_argument("--hide-scrollbars")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--window-size=480,800")
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

        # Extract the current window size from the driver
        current_window_size = driver.get_window_size()

        # Extract the client window size from the html tag
        html = driver.find_element(By.TAG_NAME, "html")
        inner_width = int(html.get_attribute("clientWidth"))
        inner_height = int(html.get_attribute("clientHeight"))

        # "Internal width you want to set+Set "outer frame width" to window size
        target_width = self.image_width + (current_window_size["width"] - inner_width)
        target_height = self.image_height + (
            current_window_size["height"] - inner_height
        )

        # driver.set_window_rect(width=target_width, height=target_height)

        return driver
