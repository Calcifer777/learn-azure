#!/bin/bash

set -x

curl --request POST http://localhost:7071/api/orchestrators/orchestrator --data '{"names": ["Azure", "Rocks"]}' | jq