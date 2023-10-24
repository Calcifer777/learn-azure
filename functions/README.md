# Local development with Azure functions

## Run locally

```bash
npm install -g azurite
npm install -g autorest
npm install -g azure-functions-core-tools
```

## Usage

### Packaging a function

Example:
```bash
./scripts/fn2zip.sh -e "tests/*" v2-blueprints
```

## Resources

### Azure Durable Functions

- https://github.com/Azure/azure-functions-durable-python/tree/dev
- https://github.com/kemurayama/durable-functions-for-python-unittest-sample

### Azurite: 
- https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite?tabs=npm#run-azurite
- https://github.com/MicrosoftDocs/azure-docs/blob/main/articles/storage/blobs/use-azurite-to-run-automated-tests.md

### Azure Functions Core Tools: 


### Handling SendEventPost

- https://stackoverflow.com/questions/67617410/azure-durable-function-send-eventposturi-by-mail

### Testing

https://medium.com/mesh-ai-technology-and-engineering/writing-and-testing-azure-functions-in-the-v2-python-programming-model-c391bd779ff6

### Deployment

Blue/Green: https://medium.com/@brentonlawson/azure-durable-functions-blue-green-deployment-701af5cdebaa
