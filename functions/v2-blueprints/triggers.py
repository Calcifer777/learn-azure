from uuid import uuid1

import azure.functions as func
import azure.durable_functions as df

from models import OrchestratorIn


bp = df.Blueprint()


@bp.route(route="workflow/{workflow_name}")
@bp.durable_client_input(client_name="client")
async def http_trigger(
    req: func.HttpRequest, client: df.DurableOrchestrationClient
):
    wf_name = req.route_params.get("workflow_name")
    client_input: dict = req.get_json()
    instance_id = str(uuid1())
    wf_mgmt = client.create_http_management_payload(instance_id=instance_id)
    input_ = OrchestratorIn(
        callback_uri_template=wf_mgmt["sendEventPostUri"],
        client_input=client_input,
    )
    await client.start_new(wf_name, client_input=input_.model_dump(), instance_id=instance_id)
    rsp = client.create_check_status_response(req, instance_id)
    return rsp