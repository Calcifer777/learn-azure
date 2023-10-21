import logging
from pathlib import Path

from azure.durable_functions import DurableOrchestrationContext, Orchestrator


def orchestrator_function(context: DurableOrchestrationContext):
    logging.info(f"Orchestrator start ...")
    names = context.get_input()
    tasks = [context.call_activity("Hello", n) for n in names]
    results = yield context.task_all(tasks)
    logging.info(f"Orchestrator - End - Result: {results} from {Path.cwd()}")
    return results

main = Orchestrator.create(orchestrator_function)