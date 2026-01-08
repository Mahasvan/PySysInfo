.. _querying-info:

=============
Querying Info
=============

Information about the computer can be queried on a per-component basis, or all components at once.

-----------------------
Complete Info Retrieval
-----------------------

In the following example, we query all available information from the system.

.. code-block:: python

    import pysysinfo
    from pysysinfo.models.info_models import HardwareInfo

    hm = pysysinfo.HardwareManager()
    info = hm.fetch_hardware_info()

    print(type(info))
    print(isinstance(info, HardwareInfo))

Output on a macOS machine:

.. code-block:: shell

    <class 'pysysinfo.models.info_models.MacHardwareInfo'>
    True

------------

``fetch_hardware_info()`` returns an instance of an OS-specific ``HardwareInfo`` class, which has the following structure.

.. autoclass:: pysysinfo.models.info_models.HardwareInfo
    :members:
    :exclude-members: __new__,__init__,model_config

------------

Depending on the OS, one of the following classes is returned.
Do note that the structure and usage remain the same.


.. autoclass:: pysysinfo.models.info_models.WindowsHardwareInfo
    :show-inheritance:
    :noindex:
    :exclude-members: __new__,__init__

.. autoclass:: pysysinfo.models.info_models.MacHardwareInfo
    :show-inheritance:
    :exclude-members: __new__,__init__
    :noindex:

.. autoclass:: pysysinfo.models.info_models.LinuxHardwareInfo
    :show-inheritance:
    :exclude-members: __new__,__init__
    :noindex:

-------------------------------
Single Component Retrieval
-------------------------------

In the following example, we query data for just the CPU.
The same structure can be followed for GPU, Memory, etc.

.. code-block:: python

    import pysysinfo

    hm = pysysinfo.HardwareManager()
    cpu_info = hm.fetch_cpu_info()

    print(type(cpu_info))
    print(cpu_info.name)

Output:

.. code-block:: shell

    <class 'pysysinfo.models.cpu_models.CPUInfo'>
    Apple M3

------------------------
Accessing Retrieved Data
------------------------

There are two ways to access the data retrieved from PySysInfo.

-------------

The first is to assign the output of ``fetch_hardware_info()``
or the other single-component methods into a variable.

.. code-block:: python

    import pysysinfo

    hm = pysysinfo.HardwareManager()
    info = hm.fetch_hardware_info()

    print(info.cpu.name)
    print(info.cpu.architecture)
    print(info.cpu.vendor)



Output:

.. code-block:: shell

    Apple M3
    ARM
    Apple


Here's another example:


.. code-block:: python

    import pysysinfo

    hm = pysysinfo.HardwareManager()

    storage = hm.fetch_storage_info()

    print("Found", len(storage.disks), "storage devices")
    print("==========")
    for disk in storage.disks:
        print("Name:", disk.model)
        print("Size:", disk.size.capacity, disk.size.unit)
        print("==========")

Output:

.. code-block:: shell

    Found 1 storage devices
    ==========
    Name: APPLE SSD AP0512Z
    Size: 477102 MB
    ==========

-------------

The second way is to use the ``info`` attribute of the
:class:`HardwareManager <pysysinfo.models.info_models.HardwareManagerInterface>`.
Querying any data automatically populates the ``info`` attribute,
meaning it can be accessed directly from the HardwareManager instance.

.. code-block:: python

    import pysysinfo

    hm = pysysinfo.HardwareManager()

    hm.fetch_cpu_info()
    print("CPU Name:", hm.info.cpu.name)

    hm.fetch_storage_info()
    print("Found", len(hm.info.storage.disks), "disks")

    # CPU data is still available at this point.
    print("CPU Manufacturer:", hm.info.cpu.vendor)

Output:

.. code-block:: shell

    CPU Name: Apple M3
    Found 1 disks
    CPU Manufacturer: Apple

This is possible because ``hm.info`` is an instance of the :class:`HardwareInfo <pysysinfo.models.info_models.HardwareInfo>` class.

The data returned from ``fetch_hardware_info()`` and ``hm.info`` are the exact same.

.. code-block:: python

    import pysysinfo

    hm = pysysinfo.HardwareManager()

    info = hm.fetch_hardware_info()
    print(hm.info == info)

    cpu_info = hm.fetch_cpu_info()
    print(hm.info.cpu == cpu_info)

Output:

.. code-block:: shell

    True
    True


.. _errors-during-hardware-discovery:

--------------------------------
Errors during Hardware Discovery
--------------------------------
Sometimes, errors may be encountered during hardware discovery
that partially or fatally affect the process.

When querying data, each component will have a ``status`` property.
this property contains info about whether any errors were encountered when fetching data.

When querying per-component information:

.. code-block:: python

    cpu_info = hm.fetch_cpu_info()
    print(cpu_info.status.type)

Output:

.. code-block:: shell

    StatusType.SUCCESS

When querying complete information:

.. code-block:: python

    import pysysinfo

    hm = pysysinfo.HardwareManager()

    hm.fetch_hardware_info()

    print("CPU:", hm.info.cpu.status.type)
    print("Graphics:", hm.info.graphics.status.type)
    print("Storage:", hm.info.storage.status.type)

Output:

.. code-block:: shell

    CPU: StatusType.SUCCESS
    Graphics: StatusType.SUCCESS
    Storage: StatusType.SUCCESS

-------

the ``status`` property follows the following structure:

.. autoclass:: pysysinfo.models.status_models.Status
    :members:
    :exclude-members: model_config
    :no-index:

--------

The ``type`` attribute is an Enum.
Depending on the errors encountered, it can be one of the following three values.

.. autoclass:: pysysinfo.models.status_models.StatusType
    :members:

-------

When using this library, the following example may be of use,
to handle partial and fatal errors.

.. code-block:: python

    import pysysinfo
    from pysysinfo.models.status_models import StatusType

    hm = pysysinfo.HardwareManager()

    cpu = hm.fetch_cpu_info()

    if cpu.status.type == StatusType.FAILED:
        print("Failed - Fatal issue(s) occurred:")
        for message in cpu.status.messages:
            print(message)

        exit(1) # Don't continue executing

    elif cpu.status.type == StatusType.PARTIAL:
        print("Partial Error - Issue(s) occurred:")
        for message in cpu.status.messages:
            print(message)

        # Continue executing
        print(cpu.name)

    else:
        # It is StatusType.SUCCESS
        print("Successfully retrieved info!")
        print(cpu.name)

Output:

.. code-block:: shell

    Successfully retrieved info!
    Apple M3

