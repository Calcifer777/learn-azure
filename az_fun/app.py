import azure.functions as func
import azure.durable_functions as df
from azure.functions.decorators.function_app import FunctionBuilder

from az_fun.activities import activity
from az_fun.utils import compose


async def http_start(
    req: func.HttpRequest,
    client: df.DurableOrchestrationClient,
):
    function_name = req.route_params.get("functionName")
    instance_id = await client.start_new(function_name)
    response = client.create_check_status_response(req, instance_id)
    return response


def logic(context: df.DurableOrchestrationContext):
    result1 = yield context.call_activity("activity_builder", "Seattle")
    result2 = yield context.call_activity("activity_builder", "Tokyo")
    result3 = yield context.call_activity("activity_builder", "London")
    return [result1, result2, result3]


adf_app = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)
activity_builder: FunctionBuilder = adf_app.activity_trigger(input_name="city")(activity)

adf_logic = adf_app.orchestration_trigger(context_name="context")(logic)

adf_trigger = compose(
    adf_app.route(route="orchestrators/{functionName}"),
    adf_app.durable_client_input(client_name="client")
)(http_start)