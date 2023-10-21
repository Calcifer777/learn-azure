#!/bin/bash

set -x

### Hello world
curl --request POST http://localhost:7071/api/workflow/hello_world --data '{"names": ["Milan"]}' | jq ".statusQueryGetUri"

### Sub-orchestrator
curl --request POST http://localhost:7071/api/workflow/weather --data '{"names": ["New York", "Chicago"]}' | jq ".statusQueryGetUri"

### External Feedback
curl --request POST http://localhost:7071/api/workflow/trip --data '{"destination":"Chicago"}' | jq ".statusQueryGetUri"

# Feedback
export instance_id="8dbda36b6e0147bca0a307a2dab1cce9"
curl \
  --request POST  \
  --header "Content-Type: application/json"  \
  http://localhost:7071/runtime/webhooks/durabletask/instances/${instance_id}/raiseEvent/Approval&Code=XXX