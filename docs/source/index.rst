.. PySysInfo documentation master file, created by
sphinx-quickstart on Wed Dec 31 19:12:18 2025.
You can adapt this file completely to your liking, but it should at least
contain the root `toctree` directive.

---------
PySysInfo
---------

PySysInfo is a Python library that gathers info about system components, such as the
CPU, memory, storage, and graphics, across Linux, macOS, and Windows.

========
Features
========

- Consistent structure on all platforms, using `Pydantic models <https://docs.pydantic.dev/latest/concepts/models/>`_.
- Usage stays the same everywhere, with no need for code changes across platforms.
- Supports data retrieval as Class objects, Python dictionaries, or JSON-parsable strings.
- For a list of supported hardware components, refer to :ref:`supported`.

------

To get started, refer to :ref:`quickstart`.

-------

========
Contents
========

.. toctree::
   :maxdepth: 2

   quickstart
   hardware_managers
   querying_info
   serialization
   supported
   theory
   models
