import logging

import azure.durable_functions as df
import aiohttp

from models import *


bp = df.Blueprint()

http_client = aiohttp.ClientSession()


@bp.activity_trigger(input_name="name")
async def get_geocoding(name: str):
    try:
        async with http_client.get(url="https://geocode.maps.co/search", params=dict(city=name)) as rsp:
            weather_response_payload = await rsp.json()
    except aiohttp.ClientConnectionError as e:
        logging.error(f"ClientConnectionError: {e}")
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
    try:
        async with http_client.get(url="https://api.open-meteo.com/v1/forecast", params=query_params) as rsp:
            rsp_content = await rsp.json()
    except aiohttp.ClientConnectionError as e:
        logging.error(f"ClientConnectionError: {e}")
    out = WeatherOut.model_validate(rsp_content)
    logging.warning(f"Weather: {out}")
    return out


@bp.activity_trigger(input_name="req")
async def ask_for_feedback(req: dict) -> bool:
    req = FeedbackReq.model_validate(req)
    logging.warning(f"Asking for feedback for instance_id: {req}")
    return "ok"
