from datetime import timedelta
import logging

import azure.durable_functions as df

from models import *


bp = df.Blueprint()

@bp.orchestration_trigger(context_name="context")
def trip(context: df.DurableOrchestrationContext):
    input = OrchestratorIn.model_validate(context.get_input())
    destination = input.client_input["destination"]
    if context.is_replaying is False:
        logging.warning(f"Planning to: {destination}")
    city_geocoding: GeocodingOut = yield context.call_activity(
        name="get_geocoding", input_=str(destination)
    )
    get_weather_in = WeatherIn(lat=city_geocoding.lat, lon=city_geocoding.lon)
    get_weather_out: WeatherOut = yield context.call_activity(
        name="get_city_weather", input_=get_weather_in.model_dump()
    )
    wf_out = WorkflowOut(
        destination=destination,
        lat=city_geocoding.lat,
        lon=city_geocoding.lon,
        current_temp=str(get_weather_out.current.temperature),
    )
    # Send feedback request
    fb_event_name = "Approval"
    fb_req = FeedbackReq(
        output=wf_out.model_dump(),
        callback_uri=input.callback_uri_template.format(eventName=fb_event_name),
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
