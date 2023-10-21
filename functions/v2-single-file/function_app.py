import asyncio
import json
import logging
import random

import azure.functions as func
import azure.durable_functions as df

app = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="workflow/{functionName}")
@app.durable_client_input(client_name="client")
async def http_start(req: func.HttpRequest, client: df.DurableOrchestrationClient):
    function_name = req.route_params.get('functionName')
    client_input: dict = req.get_json()
    names = client_input.get("names", [])
    instance_id = await client.start_new(function_name, client_input=names)
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