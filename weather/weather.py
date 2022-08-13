import requests
from os.path import exists, abspath
from datetime import datetime


class WeatherService:
    def __init__(self, apikey, location="Cork,Ireland", metric=True):
        self.apikey = apikey
        self.units = "metric" if metric else "imperial"
        self.num_hours = 5
        self.baseurl = "https://api.openweathermap.org"

        self.lat, self.lon = self.get_coords(location)

    def get_icon(self, icon_id):
        local_path = "views/html/assets/{}@4x.png".format(icon_id)
        if not exists(local_path):
            return "https://openweathermap.org/img/wn/{}@4x.png".format(icon_id)

        return abspath(local_path)

    def current_forecast(self):
        res = requests.get(
            self.baseurl
            + "/data/2.5/weather?lat={}&lon={}&appid={}&units={}".format(
                self.lat, self.lon, self.apikey, self.units
            )
        )
        data = res.json()

        forecast = {
            "dt": datetime.fromtimestamp(data["dt"]),
            "icon": self.get_icon(data["weather"][0]["icon"]),
            "sunrise": datetime.fromtimestamp(data["sys"]["sunrise"]),
            "sunset": datetime.fromtimestamp(data["sys"]["sunset"]),
            "temp": {
                "unit": "\N{DEGREE SIGN}C"
                if self.units == "metric"
                else "\N{DEGREE SIGN}F",
                "high": round(data["main"]["temp_max"]),
                "low": round(data["main"]["temp_min"]),
                "real": round(data["main"]["temp"]),
                "feels_like": round(data["main"]["feels_like"]),
            },
            "wind": {
                "unit": "kmh" if self.units == "metric" else "mph",
                "real": data["wind"]["speed"],
            },
            "humidity_percentage": data["main"]["humidity"],
            "pressure_hpa": data["main"]["pressure"],
            "clouds_percentage": data["clouds"]["all"],
            # "precip_percentage": round(data["pop"]),
        }

        return forecast

    def three_hour_daily_forecast(self):
        res = requests.get(
            self.baseurl
            + "/data/2.5/forecast?cnt={}&lat={}&lon={}&appid={}&units={}".format(
                self.num_hours, self.lat, self.lon, self.apikey, self.units
            )
        )
        data = res.json()

        code = data["cod"]
        if int(code) != 200:
            raise ValueError("Non-200 response from weather api: {}".format(data))

        forecasts = []
        entries = data["list"]
        for entry in entries:
            forecasts.append(
                {
                    "dt": datetime.fromtimestamp(entry["dt"]),
                    "icon": self.get_icon(entry["weather"][0]["icon"]),
                    "temp": {
                        "unit": "\N{DEGREE SIGN}C"
                        if self.units == "metric"
                        else "\N{DEGREE SIGN}F",
                        "high": round(entry["main"]["temp_max"]),
                        "low": round(entry["main"]["temp_min"]),
                        "real": round(entry["main"]["temp"]),
                        "feels_like": round(entry["main"]["feels_like"]),
                    },
                    "wind": {
                        "unit": "kmh" if self.units == "metric" else "mph",
                        "real": entry["wind"]["speed"],
                    },
                    "humidity_percentage": entry["main"]["humidity"],
                    "pressure_hpa": entry["main"]["pressure"],
                    "clouds_percentage": entry["clouds"]["all"],
                    "precip_percentage": round(entry["pop"]),
                }
            )

        return forecasts

    def get_coords(self, location):
        res = requests.get(
            self.baseurl
            + "/geo/1.0/direct?q={}&limit=1&appid={}".format(location, self.apikey)
        )
        data = res.json()

        if len(data) == 0 or len(data) > 1:
            raise ValueError("Unexpected response from weather api: {}".format(data))

        data = data[0]
        lat = round(data["lat"])
        lon = round(data["lon"])

        return lat, lon
