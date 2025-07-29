# Jentic SDK – Remote Execution 🚀 *(WORK IN PROGRESS)*
[![PyPI](https://img.shields.io/pypi/v/jentic.svg)](https://pypi.org/project/jentic/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)

**Jentic** is a powerful, flexible SDK and runtime for secure remote code execution and automation. It enables developers and teams to orchestrate, execute, and manage complex workflows across distributed systems, with a focus on reliability, extensibility, and developer experience. Whether you're building intelligent agents, integrating APIs, or running code in the cloud, Jentic provides a unified interface and robust toolkit to accelerate your development.

---

## 🚩 Features

- **Remote Code Execution**: Run code and workflows securely in the cloud.
- **Unified API**: Simple, consistent interface for all operations.
- **Secure**: Built-in authentication and sandboxing.
- **Async & Sync Support**: Use in any Python environment.

---

## 📖 Table of Contents

- [Overview](#overview)
- [Features](#-features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Authentication](#authentication)
- [Quick Start](#quick-start)
- [Contributing](#contributing)
- [Community & Support](#community--support)
- [License](#license)

---

## Overview

Jentic lets you execute code and automate workflows remotely, making it easy to build intelligent agents, integrate APIs, and manage distributed tasks.

<!-- Optionally add a diagram here -->

---

## Architecture

<!-- Add a simple diagram or bullet points explaining the architecture -->

- **Client SDK**: Python interface for interacting with the Jentic runtime.
- **Remote Runtime**: Secure environment for executing code and workflows.
- **API Gateway**: Handles authentication, routing, and orchestration.

---

## Prerequisites

- Python 3.11+
- A valid Jentic API key ([Get one here](https://your-signup-link))

---

## Installation

```bash
pip install jentic
```

## Authentication

 **Note:** The client looks for an explicit `api_key` argument or the environment variable `JENTIC_AGENT_API_KEY`.

Set your API key as an environment variable:

```bash
export JENTIC_AGENT_API_KEY="your-key-here"
```

Or pass it directly in code:

```python
import jentic
client = jentic.Jentic(jentic.AgentConfig(api_key="your-key-here"))
```

---

## Quick Start

### List APIs

```python
import jentic
apis = await jentic.list_apis()
print(apis)
```

### Search

```python
results = await jentic.search("send message to discord channel")
print(results)
```

### Execute an Operation

```python
resp = await jentic.execute(
    jentic.ExecutionRequest(
        execution_type="operation",
        uuid="operation_id",
        inputs={"arg1": "value1"}
    )
)
print(resp)
```

> **Note:** For sync code, use `asyncio.run()`:

```python
import asyncio
import jentic

apis = asyncio.run(jentic.list_apis())
print(apis)
```

---


## Contributing

Pull requests are welcome! See [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## Community & Support

- [GitHub Issues](https://github.com/your-repo/issues)
- [Discord](https://discord.gg/your-invite)
- [Discussions](https://github.com/your-repo/discussions)

---

## License

Distributed under the MIT license. See [`LICENSE`](../LICENSE) for details.
