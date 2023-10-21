import asyncio
from datetime import timedelta
import json
import logging
import random
from typing import Optional, Tuple

import azure.functions as func
import azure.durable_functions as df

app = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="workflow/{functionName}")
@app.durable_client_input(client_name="client")
async def http_start(req: func.HttpRequest, client: df.DurableOrchestrationClient):
    function_name = req.route_params.get('functionName')
    client_input: dict = req.get_json()
    instance_id = await client.start_new(function_name, client_input=client_input)
    response = client.create_check_status_response(req, instance_id)
    return response


### Hello world ###
@app.orchestration_trigger(context_name="context")
def hello_world(context: df.DurableOrchestrationContext):
    names = context.get_input()
    tasks = [context.call_activity("greet", n) for n in names]
    results = yield context.task_all(tasks)
    return results


@app.activity_trigger(input_name="name")
async def greet(name: str):
    sleep_time = random.random()*3
    logging.info(f"Sleeping for {sleep_time:.2f}s")
    await asyncio.sleep(sleep_time)
    return "Hello " + name


### Sub-Orchestrator ###
@app.orchestration_trigger(context_name="context")
def get_weather(context: df.DurableOrchestrationContext):
    """ 
    geocoding API: https://geocode.maps.co/
    temperature API: https://open-meteo.com/
    """
    logging.warning(f"Received input: {context.get_input()}")
    name = context.get_input()["name"]
    logging.warning(f"{name}: fetching geocoding")
    geocoding_response: dict = yield context.call_http(
        method="GET", 
        uri="https://geocode.maps.co/search?city="+"+".join(name.split()),
    )
    if geocoding_response["statusCode"]< 200 or geocoding_response["statusCode"] >= 300:
        raise ConnectionError(f"{name}: could not fetch geocoding")
    geocoding_payload = json.loads(geocoding_response["content"])
    geocoding_details = geocoding_payload[0]
    logging.warning(f"{name} - geocoding details: {geocoding_details}")
    lat, long = geocoding_details.get("lat"), geocoding_details.get("lon")
    logging.warning(f"{name} - fetching weather")
    weather_response: func.HttpResponse = yield context.call_http(
        method="GET", 
        uri=f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={long}&current=temperature",
    )
    if weather_response["statusCode"] < 200 or weather_response["statusCode"] >= 300:
        raise ConnectionError(f"{name}: could not fetch weather info")
    weather_response_payload = json.loads(weather_response["content"])
    logging.warning(f"{name} - weather: {weather_response_payload}")
    temp_value = weather_response_payload["current"]["temperature"]
    temp_unit = weather_response_payload["current_units"]["temperature"]
    return f"Hi from {name} (lat: {lat}, long: {long}), it's {temp_value}{temp_unit} here!"


@app.orchestration_trigger(context_name="context")
def weather(context: df.DurableOrchestrationContext):
    names = context.get_input()
    tasks = [context.call_sub_orchestrator(name="get_weather", input_={"name": n}) for n in names]
    results = yield context.task_all(tasks)
    return results

  
### External Feedback
import httpx
from pydantic import BaseModel


@app.activity_trigger(input_name="name")
async def get_geocoding(name: str):
    async with httpx.AsyncClient(base_url="https://geocode.maps.co") as client:
      rsp = await client.get(url=f"/search", params=dict(city=name))
    if rsp.status_code < 200 or rsp.status_code >= 300:
        raise ConnectionError(f"Could not fetch geocoding info")
    weather_response_payload = json.loads(rsp.content)
    if len(weather_response_payload) == 0:
        raise RuntimeError("Could not fetch geocoding for {}")
    resp = weather_response_payload[0]
    logging.warning(f"Weather: {resp}")
    return resp


class WeatherInput(BaseModel):
    lat: str
    lon: str


@app.activity_trigger(input_name="latlon")
async def get_city_weather(latlon: dict):
    weather_input = WeatherInput.model_validate(latlon)
    query_params = dict(
        latitude=round(float(weather_input.lat), 3),
        longitude=round(float(weather_input.lon), 3),
        current="temperature"
    )
    async with httpx.AsyncClient(base_url="https://api.open-meteo.com") as client:
      rsp = await client.get(url="/v1/forecast", params=query_params)
    if rsp.status_code < 200 or rsp.status_code >= 300:
        raise ConnectionError(f"Could not fetch weather info")
    weather_response_payload = json.loads(rsp.content)
    logging.warning(f"Weather: {weather_response_payload}")
    return weather_response_payload


@app.activity_trigger(input_name="req")
async def ask_for_feedback(req: dict) -> bool:
    logging.warning(f"Asking for feedback for instance_id: {req['workflow_id']}")
    return "ok"

class TripPlanningResponse(BaseModel):
    destination: str
    current_temp: float
    status: Optional[str] = None


@app.orchestration_trigger(context_name="context")
def trip(context: df.DurableOrchestrationContext):
    destination = context.get_input()["destination"]
    if context.is_replaying is False:
      logging.warning(f"Planning trip to: {destination}")
    # city_geocoding = yield context.call_activity(name="get_geocoding", input_=str(destination))
    # in_weather = WeatherInput(lat=city_geocoding["lat"], lon=city_geocoding["lon"])
    # weather = yield context.call_activity(name="get_city_weather", input_=in_weather.model_dump())
    # temp = float(weather["current"]["temperature"])
    feedback_req = dict(
        # temp=temp,
        workflow_id=context.instance_id,
    )
    yield context.call_activity(name="ask_for_feedback", input_=feedback_req)
    rsp = TripPlanningResponse(
      destination=destination,
      current_temp=10.,
      # current_temp=temp,
    )
    timer = context.create_timer(context.current_utc_datetime + timedelta(minutes=5))
    approval = context.wait_for_external_event("Approval")
    feedback = yield context.task_any([approval, timer])
    if feedback == timer:
      rsp.status = "cancelled"
    else:
      timer.cancel()  # important
      rsp.status = "planned"
    return rsp.model_dump()
