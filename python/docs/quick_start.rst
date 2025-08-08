Quick Start
===========

Welcome to the Jentic Python SDK! This guide will get you up and running in minutes.

1. Get Your Agent API Key
-------------------------
- Sign up or log in at https://jentic.com
- Go to your dashboard and copy your **Agent API Key** (starts with `ak_...`).
- This key is used to authenticate your requests to the Jentic API, so keep it secret.


2. Install the SDK
------------------
Install via pip:

.. code-block:: bash

   pip install jentic

Or with PDM:

.. code-block:: bash

   pdm add jentic

3. Search, Load and Execute
-------------------------------------------
.. note::
   Set your API key as an environment variable before running:

   .. code-block:: bash

      export JENTIC_AGENT_API_KEY=ak_...

.. code-block:: python

   import asyncio
   from jentic import Jentic, SearchRequest, LoadRequest, ExecutionRequest

   async def main():

       # Search for a restaurant in Dublin
       search = await jentic.search(SearchRequest(query="Find me a restaurant in Dublin"))

       # Choose the first result, and load it
       op_id = search.results[0].id
       load_result = await jentic.load(LoadRequest(ids=[op_id]))

       # Check inputs required to execute
       print(load_result.tool_info[op_id].inputs)

       # Execute the operation
       result = await jentic.execute(ExecutionRequest(id=op_id, inputs={"area": "D2"}))

       # Print the result
       print(result.output)

   asyncio.run(main())


4. What’s Next?
---------------
- Explore the :doc:`API Reference <api_reference>` for all available methods and advanced usage.
- Join our `Discord <https://discord.com/jentic>`_ or email `support@jentic.com <mailto:support@jentic.com>`_ for help.