from azure.durable_functions import DurableOrchestrationContext, Orchestrator


def orchestrator_function(context: DurableOrchestrationContext):
    result1 = yield context.call_activity('Hello', "Tokyo")
    result2 = yield context.call_activity('Hello', "Seattle")
    result3 = yield context.call_activity('Hello', "London")
    return [result1, result2, result3]

main = Orchestrator.create(orchestrator_function)