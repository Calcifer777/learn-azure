import json
import logging

import azure.durable_functions as df
import httpx

from models import *


bp = df.Blueprint()


@bp.activity_trigger(input_name="name")
async def get_geocoding(name: str):
    async with httpx.AsyncClient(base_url="https://geocode.maps.co") as client:
        rsp = await client.get(url=f"/search", params=dict(city=name))
    if rsp.status_code < 200 or rsp.status_code >= 300:
        raise ConnectionError(f"Could not fetch geocoding info")
    weather_response_payload = json.loads(rsp.content)
    if len(weather_response_payload) == 0:
        raise RuntimeError(f"Could not fetch geocoding for {name}")
    resp = weather_response_payload[0]
    logging.warning(f"{name} geocoding: {resp}")
    return resp
    

@bp.activity_trigger(input_name="latlon")
async def get_city_weather(latlon: dict) -> WeatherOut:
    latlon = WeatherIn.model_validate(latlon)
    query_params = dict(
        latitude=round(float(latlon.lat), 3),
        longitude=round(float(latlon.lon), 3),
        current="temperature",
    )
    async with httpx.AsyncClient(base_url="https://api.open-meteo.com") as client:
        rsp = await client.get(url="/v1/forecast", params=query_params)
    if rsp.status_code < 200 or rsp.status_code >= 300:
        raise ConnectionError(f"Could not fetch weather info")
    out = WeatherOut.model_validate_json(rsp.content)
    logging.warning(f"Weather: {out}")
    return out


@bp.activity_trigger(input_name="req")
async def ask_for_feedback(req: dict) -> bool:
    req = FeedbackReq.model_validate(req)
    logging.warning(f"Asking for feedback for instance_id: {req}")
    return "ok"
