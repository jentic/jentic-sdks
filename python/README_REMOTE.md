# Jentic SDK – Remote Execution  (WORK IN PROGRESS)

## Overview
A minimal guide to installing the Jentic Python SDK and executing code on a remote Jentic runtime.

## Prerequisites
* Python 3.11+
* A valid Jentic API key

## Installation
```bash
pip install jentic
```

## Authentication
The client looks for an explicit `api_key` argument or the environment variable `JENTIC_AGENT_API_KEY`.

```bash
export JENTIC_AGENT_API_KEY="your-key-here"
```

## Quick Start - Basic Usage
```python
import jentic

apis = jentic.list_apis()
print(apis)

results = jentic.search("discord search message")
print(results)

resp = jentic.execute(jentic.ExecutionRequest(operation_id="operation_id", args={"arg1": "value1"}))
print(resp)
```


## Contributing
Pull requests are welcome. See `CONTRIBUTING.md` for guidelines.

## License
Distributed under the MIT license. See `LICENSE` for details.
