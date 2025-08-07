Load
====

**What is Load?**

Load fetches the schemas and authentication requirements for the operations or workflows you found with Search. This prepares your agent to execute them safely and correctly.

**Why Load?**
- Get input/output schemas for validation and UI generation.
- Discover required authentication (API keys, OAuth, etc.).

**How to Use Load**

.. code-block:: python

   from jentic import Jentic, LoadRequest, SearchRequest
   import asyncio

   async def main():
       jentic = Jentic()
       search = await jentic.search(SearchRequest(query="Find me a restaurant in Dublin"))
       op_id = search.results[0].id
       load_result = await jentic.load(LoadRequest(ids=[op_id]))
       print(load_result.tool_info[op_id].inputs)

   asyncio.run(main())

:doc:`Next: Execute <execute>` | :doc:`Back to Agents <index>` | :doc:`Quick Start <../quick_start>` | :doc:`API Reference <../api_reference>`