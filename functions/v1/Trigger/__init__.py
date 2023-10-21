import logging

import azure.durable_functions as df

import azure.functions as func


async def main(req: func.HttpRequest, starter: str) -> func.HttpResponse:
    client = df.DurableOrchestrationClient(starter)
    params = req.get_json()
    logging.warning(f"Trigger params: {params}")
    instance_id = await client.start_new(
        req.route_params["functionName"], 
        instance_id=None, 
        client_input=params.get("names", []),
    )
    logging.warning(f"Started orchestration with ID = '{instance_id}")
    return client.create_check_status_response(req, instance_id=instance_id)
