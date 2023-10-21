#!/bin/bash

set -x

# Hello world
curl --request POST http://localhost:7071/api/workflow/hello_world --data '{"names": ["Milan"]}' | jq ".statusQueryGetUri"