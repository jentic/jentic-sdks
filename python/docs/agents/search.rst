Search
======

Discover available APIs, operations, and workflows using natural language or keywords. This is the first step in the agent workflow.

Why Search?
-----------
- Find the right operation or workflow for your use case.
- Explore capabilities your agent can access with its API key.

How to Use Search
-----------------

.. code-block:: python

   import jentic
   import asyncio

   async def main():
       search = await jentic.search("Find me top articles on AI")
       print(search.results)

   asyncio.run(main())

Advanced usage
--------------

You can use the `SearchRequest` model to customize your search, providing more control over the results.

.. code-block:: python

   from jentic import Jentic, SearchRequest
   import asyncio

   async def main():
       jentic = Jentic()
       search = await jentic.search(
            SearchRequest(
                query="Find me a restaurant in Dublin",
                limit=10,
                apis=["yelp.com"], # Only search for operations in the Yelp API
                keywords=["restaurant", "food"], # Boost results that contain these keywords
                filter_by_credentials=False, # Include all results (even if the agent doesn't have credentials for them)
            )
        )
       print(search.results)

   asyncio.run(main())


Once you have found the operation you want to use, the next step is to load the operation.


:doc:`Next: Load <load>` | :doc:`Back to Agents <index>` | :doc:`Quick Start <../quick_start>` | :doc:`API Reference <../api_reference>`