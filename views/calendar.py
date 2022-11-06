import datetime as dt
from .page import Page


class CalendarPage(Page):
    def __init__(
        self,
        width,
        height,
    ):
        super().__init__("calendar", width, height)

    def template(
        self,
        **kwargs,
    ):
        map_url = kwargs["map_url"]
        current_forecast = kwargs["current_forecast"]
        hourly_forecasts = kwargs["hourly_forecasts"]

        a = self.airium
        now = dt.datetime.now()
        self.log.info("Time synchronised to %s", now)
        now_date = now.date()

        a("<!DOCTYPE html>")
        with a.html(lang="en"):
            with a.head():
                a.meta(
                    charset="utf-8",
                    name="viewport",
                    content="width=device-width, initial-scale=1",
                )
                a.title(_t="Calendar")
                a.link(rel="stylesheet", href="styles.css")

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
                            _t=str(hourly_forecasts[0]["temp"]["real"])
                            + current_forecast["temp"]["unit"],
                        )

                        with a.div(id="icon-container", klass="numcircle"):
                            a.img(src=current_forecast["icon"])

                with a.div(id="map-container"):
                    a.img(src=map_url, id="map")

                with a.div(klass="bg-container"):
                    with a.div(id="bottom-banner", klass="container"):
                        with a.div(id="hourly-forecasts"):
                            with a.table():
                                with a.thead(klass="forecast-hour"):
                                    with a.tr():
                                        for forecast in hourly_forecasts:
                                            with a.td(klass="hour"):
                                                hour = ""
                                                try:
                                                    hour = forecast["dt"].strftime(
                                                        "%-I"
                                                    )
                                                except ValueError as ve:
                                                    # platform-specific formatting error
                                                    self.log.warning(str(ve))
                                                    hour = forecast["dt"].strftime("%I")

                                                a(
                                                    hour
                                                    + forecast["dt"]
                                                    .strftime("%p")
                                                    .lower()
                                                )

                                with a.tbody(klass="hourly-forecasts-forecast"):
                                    with a.tr():
                                        for forecast in hourly_forecasts:
                                            with a.td():
                                                with a.div(
                                                    klass="hourly-forecast-icon fc-icon"
                                                ):
                                                    a.img(src=forecast["icon"])
                                    with a.tr():
                                        for forecast in hourly_forecasts:
                                            with a.td():
                                                with a.div(klass="fc-icon-stat"):
                                                    with a.div(klass="fc-icon"):
                                                        a.img(
                                                            src="icon/thermometer.png"
                                                        )
                                                    with a.div(klass="fc-stat"):
                                                        a.p(
                                                            _t=str(
                                                                forecast["temp"]["real"]
                                                            )
                                                            + forecast["temp"]["unit"]
                                                        )
                                    with a.tr():
                                        for forecast in hourly_forecasts:
                                            with a.td():
                                                with a.div(klass="fc-icon-stat"):
                                                    with a.div(klass="fc-icon"):
                                                        a.img(src="icon/precip.png")
                                                    with a.div(klass="fc-stat"):
                                                        a.p(
                                                            _t=str(
                                                                forecast[
                                                                    "precip_percentage"
                                                                ]
                                                            )
                                                            + "%"
                                                        )
