import asyncio
from datetime import timedelta
import json
import logging
import random
from typing import Dict
from uuid import uuid1

import azure.functions as func
import azure.durable_functions as df

app = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="workflow/{functionName}")
@app.durable_client_input(client_name="client")
async def http_start(req: func.HttpRequest, client: df.DurableOrchestrationClient):
    function_name = req.route_params.get("functionName")
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
    sleep_time = random.random() * 3
    logging.info(f"Sleeping for {sleep_time:.2f}s")
    await asyncio.sleep(sleep_time)
    return "Hello " + name


### Sub-Orchestrator with managed HTTP calls ###
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
        uri="https://geocode.maps.co/search?city=" + "+".join(name.split()),
    )
    if (
        geocoding_response["statusCode"] < 200
        or geocoding_response["statusCode"] >= 300
    ):
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
    return (
        f"Hi from {name} (lat: {lat}, long: {long}), it's {temp_value}{temp_unit} here!"
    )


@app.orchestration_trigger(context_name="context")
def weather(context: df.DurableOrchestrationContext):
    names = context.get_input()
    tasks = [
        context.call_sub_orchestrator(name="get_weather", input_={"name": n})
        for n in names
    ]
    results = yield context.task_all(tasks)
    return results


### Handle Feedback
import httpx
from pydantic import BaseModel

#### Serializable Payloads
class JsonSerializable(BaseModel):
        
    def to_json(self):
        return self.model_dump_json()


class OrchestratorIn(JsonSerializable):
    workflow_mgmt: Dict[str, str]
    client_input: dict

    @staticmethod
    def from_json(obj: str):
        return OrchestratorIn.model_validate_json(obj)


class WeatherIn(JsonSerializable):
    lat: str
    lon: str

    @staticmethod
    def from_json(obj: str):
        return WeatherIn.model_validate_json(obj)


class FeedbackReq(JsonSerializable):
    output: dict
    callback_uri: str

    @staticmethod
    def from_json(obj: str):
        return FeedbackReq.model_validate_json(obj)


class FeedbackRsp(JsonSerializable):
    status: str

    @staticmethod
    def from_json(obj: str):
        return FeedbackRsp.model_validate_json(obj)


class WorkflowOut(JsonSerializable):
    destination: str
    lat: str
    lon: str
    current_temp: float

    @staticmethod
    def from_json(obj: str):
        return WorkflowOut.model_validate_json(obj)


class OrchesratorOut(JsonSerializable):
    workflow: WorkflowOut
    feedback: FeedbackRsp

    @staticmethod
    def from_json(obj: str):
        return OrchesratorOut.model_validate_json(obj)

    def to_json(self):
        logging.warning(f"Trying to dump {self}")
        return self.model_dump()


@app.route(route="workflow-with-feedback/{workflow_name}")
@app.durable_client_input(client_name="client")
async def http_start_with_feedback(
    req: func.HttpRequest, client: df.DurableOrchestrationClient
):
    wf_name = req.route_params.get("workflow_name")
    client_input: dict = req.get_json()
    instance_id = str(uuid1())
    resp = client.create_http_management_payload(instance_id=instance_id)
    input_ = OrchestratorIn(
        workflow_mgmt=resp,
        client_input=client_input,
    )
    await client.start_new(wf_name, client_input=input_, instance_id=instance_id)
    rsp = client.create_check_status_response(req, instance_id)
    return rsp


@app.orchestration_trigger(context_name="context")
def trip(context: df.DurableOrchestrationContext) -> WorkflowOut:
    input: OrchestratorIn = context.get_input()
    destination = input.client_input["destination"]
    if context.is_replaying is False:
        logging.warning(f"Planning to: {destination}")
    city_geocoding = yield context.call_activity(
        name="get_geocoding", input_=str(destination)
    )
    in_weather = WeatherIn(lat=city_geocoding["lat"], lon=city_geocoding["lon"])
    weather = yield context.call_activity(
        name="get_city_weather", input_=in_weather.model_dump()
    )
    wf_out = WorkflowOut(
        destination=destination,
        lat=city_geocoding["lat"],
        lon=city_geocoding["lon"],
        current_temp=str(weather["current"]["temperature"]),
    )
    # Send feedback request
    fb_event_name = "Approval"
    fb_req = FeedbackReq(
        output=wf_out.model_dump(),
        callback_uri=input.workflow_mgmt["sendEventPostUri"].format(eventName=fb_event_name),
    )
    yield context.call_activity(name="ask_for_feedback", input_=fb_req)
    timer_task = context.create_timer(
        context.current_utc_datetime + timedelta(seconds=5)
    )
    approval_task = context.wait_for_external_event(fb_event_name)
    winner_task = yield context.task_any([approval_task, timer_task])
    if winner_task == timer_task:
        fb_rsp = FeedbackRsp(status="timeout")
    elif winner_task == approval_task:
        logging.warning(f"Got feedback with result {approval_task.result}")
        timer_task.cancel()  # important
        fb_rsp = FeedbackRsp(status=("completed" if approval_task.result["feedback"] in ("ok", None) else "rejected"))
    out = OrchesratorOut(
        workflow=wf_out,
        feedback=fb_rsp,
    )
    if context.is_replaying is False:
        logging.warning(f"Destination details: {out}")
    return out.model_dump()


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
    logging.warning(f"{name} geocoding: {resp}")
    return resp
    

@app.activity_trigger(input_name="latlon")
async def get_city_weather(latlon: dict):
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
    weather_response_payload = json.loads(rsp.content)
    logging.warning(f"Weather: {weather_response_payload}")
    return weather_response_payload


@app.activity_trigger(input_name="req")
async def ask_for_feedback(req: dict) -> bool:
    req = FeedbackReq.model_validate(req)
    logging.warning(f"Asking for feedback for instance_id: {req}")
    return "ok"

