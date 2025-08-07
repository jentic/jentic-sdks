Agents
======

.. note::
   **What do we mean by 'agent'?**
   In Jentic, an *agent* is a logical entity (often a backend service or LLM-powered assistant) that can discover, load, and execute APIs and workflows via the Jentic platform. This is distinct from other uses of 'agent' (e.g., in AI, security, or infrastructure).

The agent workflow in Jentic follows a simple but powerful pattern:

- **Search:** Discover available APIs, operations, and workflows.
- **Load:** Fetch schemas and authentication requirements for selected operations.
- **Execute:** Run the operation or workflow with your inputs.

Click through the sections below to learn more about each step:

.. toctree::
   :maxdepth: 1

   search
   load
   execute

:doc:`Quick Start <../quick_start>` | :doc:`API Reference <../api_reference>`