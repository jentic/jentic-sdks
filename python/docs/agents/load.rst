Load
====

Fetch schemas and authentication requirements for the operations or workflows you found with Search. This prepares your agent to execute them safely and correctly.

Why Load?
---------
- Get input/output schemas for validation and UI generation.
- Discover required authentication (API keys, OAuth, etc.).

How to Use Load
---------------

.. code-block:: python

   from jentic import Jentic, LoadRequest
   import asyncio

   async def main():
       ... search result already found ...
       
       # Load the operation, and get tool_info for the operation
       op_id = results[0].id
       load_result = await jentic.load(LoadRequest(ids=[op_id]))
       tool_info = load_result.tool_info[op_id]

       # Print the inputs and outputs needed to execute the operation
       print(tool_info.inputs)
       print(tool_info.outputs)

   asyncio.run(main())


Once loaded, you can use the tool_info to execute the operation.


:doc:`Next: Execute <execute>` | :doc:`Back to Agents <index>` | :doc:`Quick Start <../quick_start>` | :doc:`API Reference <../api_reference>`