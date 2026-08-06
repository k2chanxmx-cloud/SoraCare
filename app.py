import json
import os
from datetime import datetime
from typing import Any

import requests
from flask import Flask, jsonify, render_template, send_from_directory
from openai import OpenAI

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

LOCATIONS = {
    "koto": {"name": "江東区", "lat": 35.6729, "lon": 139.8171, "icon": "🏠"},
    "maihama": {"name": "舞浜", "lat": 35.6361, "lon": 139.8837, "icon": "🏰"},
    "omotesando": {"name": "表参道", "lat": 35.6652, "lon": 139.7125, "icon": "✨"},
    "shibuya": {"name": "渋谷", "lat": 35.6595, "lon": 139.7005, "icon": "🚃"},
    "kokubunji": {"name": "国分寺", "lat": 35.7001, "lon": 139.4800, "icon": "❤️"},
}


WEATHER_LABELS = {
    0: ("晴れ", "☀️"), 1: ("ほぼ晴れ", "🌤️"), 2: ("一部くもり", "⛅"), 3: ("くもり", "☁️"),
    45: ("霧", "🌫️"), 48: ("霧", "🌫️"), 51: ("弱い霧雨", "🌦️"), 53: ("霧雨", "🌦️"),
    55: ("強い霧雨", "🌧️"), 61: ("弱い雨", "🌦️"), 63: ("雨", "🌧️"), 65: ("強い雨", "🌧️"),
    71: ("弱い雪", "🌨️"), 73: ("雪", "🌨️"), 75: ("強い雪", "❄️"), 80: ("にわか雨", "🌦️"),
    81: ("にわか雨", "🌧️"), 82: ("激しいにわか雨", "⛈️"), 95: ("雷雨", "⛈️"),
    96: ("雷雨・ひょう", "⛈️"), 99: ("激しい雷雨・ひょう", "⛈️"),
}


def _weather_label(code: int) -> tuple[str, str]:
    return WEATHER_LABELS.get(code, ("天気不明", "🌡️"))


def heat_level(apparent_temp: float, humidity: float) -> dict[str, str]:
    """Practical heat-risk estimate. Not a replacement for official WBGT measurements."""
    score = apparent_temp + max(0, humidity - 60) * 0.08
    if score >= 38:
        return {"label": "危険", "class": "danger", "advice": "屋外活動をできるだけ避けてください"}
    if score >= 34:
        return {"label": "厳重警戒", "class": "warning", "advice": "激しい運動を避け、頻繁に水分補給を"}
    if score >= 30:
        return {"label": "警戒", "class": "caution", "advice": "休憩と水分補給を意識してください"}
    if score >= 26:
        return {"label": "注意", "class": "notice", "advice": "長時間の屋外活動に注意してください"}
    return {"label": "ほぼ安全", "class": "safe", "advice": "通常どおり過ごせます"}


def pressure_status(pressures: list[float]) -> dict[str, Any]:
    if len(pressures) < 4:
        return {"label": "不明", "class": "safe", "arrow": "→", "delta3h": 0}
    delta = round(pressures[3] - pressures[0], 1)
    if delta <= -4:
        return {"label": "警戒", "class": "pressure-danger", "arrow": "↘", "delta3h": delta}
    if delta <= -2:
        return {"label": "注意", "class": "pressure-warning", "arrow": "↓", "delta3h": delta}
    if delta >= 3:
        return {"label": "上昇", "class": "notice", "arrow": "↗", "delta3h": delta}
    return {"label": "安定", "class": "safe", "arrow": "→", "delta3h": delta}


def fetch_weather(location_key: str) -> dict[str, Any]:
    loc = LOCATIONS.get(location_key, LOCATIONS["koto"])
    params = {
        "latitude": loc["lat"], "longitude": loc["lon"], "timezone": "Asia/Tokyo",
        "forecast_days": 2,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,surface_pressure",
        "hourly": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,weather_code,wind_speed_10m,surface_pressure,uv_index",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,uv_index_max,precipitation_probability_max,sunrise,sunset",
    }
    response = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=15)
    response.raise_for_status()
    raw = response.json()

    current_time = raw["current"]["time"]
    times = raw["hourly"]["time"]
    try:
        start = times.index(current_time)
    except ValueError:
        now = datetime.now().strftime("%Y-%m-%dT%H:00")
        start = min(range(len(times)), key=lambda i: abs(datetime.fromisoformat(times[i]).timestamp() - datetime.fromisoformat(now).timestamp()))

    hours = []
    for i in range(start, min(start + 24, len(times))):
        label, icon = _weather_label(int(raw["hourly"]["weather_code"][i]))
        hours.append({
            "time": times[i][11:16], "label": label, "icon": icon,
            "temperature": round(raw["hourly"]["temperature_2m"][i]),
            "humidity": round(raw["hourly"]["relative_humidity_2m"][i]),
            "apparent": round(raw["hourly"]["apparent_temperature"][i]),
            "rain": raw["hourly"]["precipitation_probability"][i] or 0,
            "wind": round(raw["hourly"]["wind_speed_10m"][i], 1),
            "pressure": round(raw["hourly"]["surface_pressure"][i], 1),
            "uv": round(raw["hourly"]["uv_index"][i], 1),
        })

    current_label, current_icon = _weather_label(int(raw["current"]["weather_code"]))
    pressure = pressure_status([h["pressure"] for h in hours[:4]])
    heat = heat_level(float(raw["current"]["apparent_temperature"]), float(raw["current"]["relative_humidity_2m"]))
    month = datetime.now().month
    min_temp = float(raw["daily"]["temperature_2m_min"][0])
    heatshock = {"label": "対象外", "class": "muted"}
    if month in (11, 12, 1, 2, 3):
        heatshock = {"label": "警戒" if min_temp <= 5 else "注意" if min_temp <= 10 else "低い", "class": "warning" if min_temp <= 5 else "notice"}

    return {
        "location": {"key": location_key, **loc},
        "updated_at": current_time.replace("T", " "),
        "current": {
            "temperature": round(raw["current"]["temperature_2m"]),
            "apparent": round(raw["current"]["apparent_temperature"]),
            "humidity": round(raw["current"]["relative_humidity_2m"]),
            "wind": round(raw["current"]["wind_speed_10m"], 1),
            "pressure": round(raw["current"]["surface_pressure"], 1),
            "weather": current_label, "icon": current_icon,
        },
        "daily": {
            "max": round(raw["daily"]["temperature_2m_max"][0]),
            "min": round(raw["daily"]["temperature_2m_min"][0]),
            "rain_max": raw["daily"]["precipitation_probability_max"][0] or 0,
            "uv_max": round(raw["daily"]["uv_index_max"][0], 1),
            "sunrise": raw["daily"]["sunrise"][0][11:16], "sunset": raw["daily"]["sunset"][0][11:16],
        },
        "pressure_status": pressure, "heat": heat, "heatshock": heatshock, "hours": hours,
        "pressure_source": "Open-Meteo（頭痛ーる連携へ差し替え可能）",
    }


def fallback_summary(data: dict[str, Any]) -> str:
    loc = data["location"]["name"]
    c, d, p, h = data["current"], data["daily"], data["pressure_status"], data["heat"]
    rain_note = "折りたたみ傘があると安心です。" if d["rain_max"] >= 40 else "雨の可能性は比較的低めです。"
    pressure_note = f"今後3時間で気圧が約{abs(p['delta3h'])}hPa下がる見込みのため、無理をせず休憩を取りましょう。" if p["delta3h"] <= -2 else "気圧は大きく崩れにくい見込みです。"
    return (f"今日の{loc}は{c['weather']}、最高{d['max']}℃・最低{d['min']}℃の予報です。"
            f"現在の体感温度は{c['apparent']}℃、湿度は{c['humidity']}％で、熱中症レベルは「{h['label']}」です。"
            f"{h['advice']}。{pressure_note}{rain_note} 外出前に最新情報も確認してください。")


def ai_summary(data: dict[str, Any]) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return fallback_summary(data)
    prompt_data = {
        "場所": data["location"]["name"], "天気": data["current"]["weather"],
        "現在気温": data["current"]["temperature"], "体感温度": data["current"]["apparent"],
        "最高気温": data["daily"]["max"], "最低気温": data["daily"]["min"],
        "湿度": data["current"]["humidity"], "降水確率最大": data["daily"]["rain_max"],
        "風速": data["current"]["wind"], "気圧": data["current"]["pressure"],
        "3時間気圧変化": data["pressure_status"]["delta3h"], "熱中症": data["heat"]["label"],
        "ヒートショック": data["heatshock"]["label"],
    }
    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
            instructions="あなたは生活者向け天気アシスタントです。与えられた数値だけを使い、日本語で220〜300字。簡潔で親しみやすく、天気、気圧、暑さ寒さ、外出時間、持ち物をまとめる。診断や断定はしない。",
            input=json.dumps(prompt_data, ensure_ascii=False),
        )
        return response.output_text.strip()[:330]
    except Exception:
        app.logger.exception("AI summary failed")
        return fallback_summary(data)


@app.get("/")
def index():
    return render_template("index.html", locations=LOCATIONS)


@app.get("/api/weather/<location_key>")
def weather_api(location_key: str):
    if location_key not in LOCATIONS:
        return jsonify({"error": "地域が見つかりません"}), 404
    try:
        data = fetch_weather(location_key)
        data["summary"] = ai_summary(data)
        return jsonify(data)
    except requests.RequestException:
        app.logger.exception("Weather API failed")
        return jsonify({"error": "天気情報を取得できませんでした。時間をおいて再読み込みしてください。"}), 502


@app.get("/manifest.json")
def manifest():
    return send_from_directory("static", "manifest.json", mimetype="application/manifest+json")


@app.get("/service-worker.js")
def service_worker():
    return send_from_directory("static", "service-worker.js", mimetype="application/javascript")


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")
