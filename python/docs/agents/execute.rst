Execute
=======

Run the operation or workflow you loaded using the required inputs. This is where your agent performs the action you requested.

Why Execute?
------------
- Trigger real-world actions (send emails, fetch data, automate workflows).
- Get results from APIs and services.

How to Use Execute
------------------

.. code-block:: python

   import jentic
   import asyncio

   async def main():
       ... load result already found ...

       op_id = ...

       # Execute the operation
       result = await jentic.execute(ExecutionRequest(id=op_id, inputs={"area": "D2"}))

       # Print the result
       if result.success:
           print(result.output)
       else:
           print(result.error)

   asyncio.run(main())

:doc:`Back to Agents <index>` | :doc:`Quick Start <../quick_start>` | :doc:`API Reference <../api_reference>`