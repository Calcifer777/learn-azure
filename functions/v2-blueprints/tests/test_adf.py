from azure import functions
import pytest

# from az_fun import activities
# from az_fun.app import df, logic, adf_app

from unittest.mock import AsyncMock, MagicMock, patch

# def mock_call_activity(fn: str, *args, **kwargs):
#   return getattr(activities, fn.removesuffix("_builder"))(*args, **kwargs)


@pytest.mark.skip
def test_logic():
  with patch(
    'azure.durable_functions.DurableOrchestrationContext',
    spec=df.DurableOrchestrationContext,
  ) as mock:
    mock.call_activity = mock_call_activity
    result = list(logic(mock))
    assert result == [
      "Hello Seattle",
      "Hello Tokyo",
      "Hello London",
    ]


@pytest.mark.skip
async def test_durablefunctionsorchestrator_trigger(self):
    function_name = 'DurableFunctionsOrchestrator'
    instance_id = 'f86a9f49-ae1c-4c66-a60e-991c4c764fe5'
    starter = MagicMock()

    mock_request = functions.HttpRequest(
        method='GET',
        body=None,
        url=f'http://localhost:7071/api/orchestrators{function_name}',
        route_params={'functionName': function_name},
        params={'name': 'Test'}
    )

    mock_response = functions.HttpResponse(
        body = None,
        status_code= 200,
        headers={
            "Retry-After": 10
        }
    )

    