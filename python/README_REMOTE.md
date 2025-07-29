# Jentic SDK – Remote Execution 🚀 *(WORK IN PROGRESS)*
[![PyPI](https://img.shields.io/pypi/v/jentic.svg)](https://pypi.org/project/jentic/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)

**Jentic** is a powerful, flexible SDK and runtime for secure remote code execution and automation. It enables developers and teams to orchestrate, execute, and manage complex workflows across distributed systems, with a focus on reliability, extensibility, and developer experience. Whether you're building intelligent agents, integrating APIs, or running code in the cloud, Jentic provides a unified interface and robust toolkit to accelerate your development.

---

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Authentication](#authentication)
- [Quick Start](#quick-start)
- [Contributing](#contributing)
- [License](#license)

---

## Overview
A minimal guide to installing the Jentic Python SDK and executing code on a remote Jentic runtime.

## Prerequisites
- Python 3.11+
- A valid Jentic API key

## Installation

```bash
pip install jentic
```

## Authentication

> **Note:**
> The client looks for an explicit `api_key` argument or the environment variable `JENTIC_AGENT_API_KEY`.

```bash
export JENTIC_AGENT_API_KEY="your-key-here"
```

## Quick Start

### Async Usage

```python
import jentic

apis = await jentic.list_apis()
print(apis)

results = await jentic.search("discord search message")
print(results)

resp = await jentic.execute(
    jentic.ExecutionRequest(
        execution_type="operation",
        uuid="operation_id",
        inputs={"arg1": "value1"}
    )
)
print(resp)
```

### Sync Context

If running in a sync context, you can use `asyncio.run()`:

```python
import asyncio
import jentic

apis = asyncio.run(jentic.list_apis())
print(apis)
```

---

## Contributing
Pull requests are welcome! See [`CONTRIBUTING.md`](CONTRIBUTING.md) for guidelines.

## License
Distributed under the MIT license. See [`LICENSE`](../LICENSE) for details.
