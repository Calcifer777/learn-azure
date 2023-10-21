#!/bin/bash

set -x

### Hello world
curl --request POST http://localhost:7071/api/workflow/hello_world --data '{"names": ["Milan"]}' | jq ".statusQueryGetUri"

### Sub-orchestrator
curl --request POST http://localhost:7071/api/workflow/weather --data '{"names": ["New York", "Chicago"]}' | jq ".statusQueryGetUri"

### External Feedback
curl --request POST http://localhost:7071/api/workflow/trip --data '{"destination":"Chicago"}' | jq ".statusQueryGetUri"

# Feedback
export instance_id="ff294448f1d742508e0e442cc18dd06d"
export token="Xqs-H7pogf5EONFaIv6VzkkhUODCFCYffxrWiEdx8gHyAzFu9_-CTw=="

curl --location --request POST 'http://localhost:7071/runtime/webhooks/durabletask/instances/f74ef99261384693b7b8056d91530160/raiseEvent/Approval' \
--header 'Content-Type: application/json' \
--header "Authorization: Bearer ${token}" \
--data-raw '{
    "eventName": "Approval",
    "instanceID": "${instance_id}"
}'