Search
======

**What is Search?**

Search lets your agent discover available APIs, operations, and workflows using natural language or keywords. This is the first step in the agent workflow.

**Why Search?**
- Find the right operation or workflow for your use case.
- Explore capabilities your agent can access with its API key.

**How to Use Search**

.. code-block:: python

   from jentic import Jentic, SearchRequest
   import asyncio

   async def main():
       jentic = Jentic()
       search = await jentic.search(SearchRequest(query="Find me a restaurant in Dublin"))
       print(search.results)

   asyncio.run(main())

:doc:`Next: Load <load>` | :doc:`Back to Agents <index>` | :doc:`Quick Start <../quick_start>` | :doc:`API Reference <../api_reference>`