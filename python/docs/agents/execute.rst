Execute
=======

**What is Execute?**

Execute runs the operation or workflow you loaded, using the required inputs. This is where your agent actually performs the action you requested.

**Why Execute?**
- Trigger real-world actions (send emails, fetch data, automate workflows).
- Get results from APIs and services.

**How to Use Execute**

.. code-block:: python

   from jentic import Jentic, SearchRequest, LoadRequest, ExecutionRequest
   import asyncio

   async def main():
       jentic = Jentic()
       search = await jentic.search(SearchRequest(query="Find me a restaurant in Dublin"))
       op_id = search.results[0].id
       await jentic.load(LoadRequest(ids=[op_id]))
       result = await jentic.execute(ExecutionRequest(id=op_id, inputs={"area": "D2"}))
       print(result.output)

   asyncio.run(main())

:doc:`Back to Agents <index>` | :doc:`Quick Start <../quick_start>` | :doc:`API Reference <../api_reference>`