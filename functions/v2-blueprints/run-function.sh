#!/bin/bash

### External Feedback
curl -o - --request POST http://localhost:7071/api/workflow/trip --data '{"destination":"Chicago"}' | jq ".statusQueryGetUri"

#### Feedback
# Use the callback uri from the get_feedback logging
callback_uri="http://localhost:7071/runtime/webhooks/durabletask/instances/4f286578-70b8-11ee-958c-d79b55559e5f/raiseEvent/Approval?taskHub=green&connection=Storage&code=R5wrKj6nfulNeamkBgAKAAhhq2cvQ_nz5eMOg57pShvxAzFuSsmdgQ=="
curl -o - --location --request POST ${callback_uri}  \
  --header 'Content-Type: application/json' \
  --data-raw '{
      "feedback": "ok",
  }'