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
        week_start_day="Monday",
        tz=timezone("Europe/Dublin"),
    ):
        a = self.airium

        now = dt.datetime.now()
        self.log.info("Time synchronised to {}".format(now))
        now_date = now.date()

        week_start_idx = list(calendar.day_name).index(week_start_day)
        start_date = now_date - dt.timedelta(
            days=((now_date.weekday() + (7 - week_start_idx)) % 7)
        )
        end_date = start_date + dt.timedelta(days=(5 * 7 - 1))
        start_datetime = tz.localize(
            dt.datetime.combine(start_date, dt.datetime.min.time())
        )
        end_datetime = tz.localize(
            dt.datetime.combine(end_date, dt.datetime.max.time())
        )

        a("<!DOCTYPE html>")
        with a.html(lang="en"):
            with a.head():
                a.meta(charset="utf-8")
                a.title(_t="Calendar")
                a.link(rel="stylesheet", href="assets/bootstrap.min.css")
                a.link(rel="stylesheet", href="assets/styles.css")

            with a.body():
                with a.div(klass="container p-0 m-0"):
                    with a.div(klass="calendar shadow bg-white p-3"):
                        with a.div(klass="align-items-center text-center"):
                            a.h3(
                                klass="month font-weight-bold mb-0 text-uppercase datecircle",
                                _t=now_date.month,
                            )

                        a.h4(
                            klass="month-name text-center text-uppercase",
                            _t=now_date.strftime("%B"),
                        )
                if weather_service is not None:
                    weather = weather_service.three_hour_daily_forecast()
                    with a.table(klass="forecasts"):
                        with a.th(klass="fc-hours"):
                            with a.tr():
                                for forecast in weather["forecasts"]:
                                    a.td(klass="fc-hour", _t=forecast["dt"].strftime("%H"))

                        with a.tbody(klass="fc-forecasts"):
                            with a.tr():
                                for forecast in weather["forecasts"]:
                                    with a.td(klass="fc-fc"):
                                        a.img(klass="fc-icon", src=forecast["icon"])

                        # for forecast in weather["forecasts"]:
                        #     with a.li(klass="forecast"):
                        #         a.img(klass="fc-icon", src=forecast[])

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
        sleep(1)
        driver.get_screenshot_as_file(png_fp)
        driver.quit()

        # convert to bmp
        img = Image.open(png_fp)
        img = img.convert("P", palette=Image.ADAPTIVE, colors=256)
        # img = img.rotate(self.rotate_angle, expand=True)
        # reduce filesize as much as possible
        img.save(bmp_fp, format="bmp", optimize=True, quality=5)

        self.log.info("Screenshot captured and saved to file.")

    def _get_chromedriver(self):
        opts = Options()
        opts.add_argument("--headless")
        opts.add_argument("--hide-scrollbars")
        opts.add_argument("--force-device-scale-factor=1")
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=opts)

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

        driver.set_window_rect(width=target_width, height=target_height)

        return driver
