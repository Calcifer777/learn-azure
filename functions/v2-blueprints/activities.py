import asyncio
import logging

import azure.durable_functions as df
import aiohttp

from models import *


bp = df.Blueprint()

_session_mutex = asyncio.Lock()
http_client = None


async def create_session_if_required():
    # https://stackoverflow.com/a/66197605
    global http_client
    if http_client is None:
        async with _session_mutex:
            if http_client is None:
                http_client = aiohttp.ClientSession()


@bp.activity_trigger(input_name="name")
async def get_geocoding(name: str) -> GeocodingOut:
    try:
        await create_session_if_required()
        async with http_client.get(url="https://geocode.maps.co/search", params=dict(city=name)) as rsp:
            rsp.raise_for_status()
            rsp_payload = await rsp.json()
    except aiohttp.ClientConnectionError as e:
        logging.error(f"ClientConnectionError: {e}")
        raise e
    if len(rsp_payload) == 0:
        raise RuntimeError(f"Could not fetch geocoding for {name}")
    resp = rsp_payload[0]
    logging.warning(f"{name} geocoding: {resp}")
    return GeocodingOut.model_validate(resp)
    

@bp.activity_trigger(input_name="latlon")
async def get_city_weather(latlon: dict) -> WeatherOut:
    latlon = WeatherIn.model_validate(latlon)
    query_params = dict(
        latitude=round(float(latlon.lat), 3),
        longitude=round(float(latlon.lon), 3),
        current="temperature",
    )
    try:
        await create_session_if_required()
        async with http_client.get(url="https://api.open-meteo.com/v1/forecast", params=query_params) as rsp:
            rsp.raise_for_status()
            rsp_content = await rsp.json()
    except aiohttp.ClientConnectionError as e:
        logging.error(f"ClientConnectionError: {e}")
        raise e
    logging.warning(f"Weather: {rsp_content}")
    out = WeatherOut.model_validate(rsp_content)
    return out


@bp.activity_trigger(input_name="req")
async def ask_for_feedback(req: dict) -> bool:
    req = FeedbackReq.model_validate(req)
    logging.warning(f"Asking for feedback for instance_id: {req}")
    return "ok"
