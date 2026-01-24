=================
Serialization
=================

All component models are `Pydantic models <https://docs.pydantic.dev/latest/concepts/models/>`_,
so they support ``.model_dump()`` for dictionaries and ``.model_dump_json()`` for JSON-ready strings.

Here is an example of using ``.model_dump()`` to output a Python dictionary:

.. code-block:: python

    import pysysinfo
    from pprint import pprint

    hm = pysysinfo.HardwareManager()

    cpu = hm.fetch_cpu_info()
    pprint(cpu.model_dump())


Output:

.. code-block:: shell

    {'arch_version': '8',
     'architecture': 'ARM',
     'bitness': 64,
     'cores': 8,
     'name': 'Apple M3',
     'sse_flags': [],
     'status': {'messages': [], 'string': 'success'},
     'threads': 8,
     'vendor': 'Apple'}

The same can be used for other components, and ``fetch_hardware_info()``.