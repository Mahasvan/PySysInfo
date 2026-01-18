.. _hardware-managers:

=================
Hardware Managers
=================

The first step to retrieving hardware information is to instantiate a ``HardwareManager``.

Depending on the OS present, PySysInfo can automatically load the appropriate Hardware Manager class.
The Hardware Manager classes implement the structure of :class:`HardwareManagerInterface <pysysinfo.models.info_models.HardwareManagerInterface>`.


--------------------------------
Instantiating a Hardware Manager
--------------------------------
Instantiating a hardware manager is the same regardless of the OS.
The following codeblock shows how a ``HardwareManager`` is instantiated.

.. code-block:: python

    import pysysinfo
    from pysysinfo.models.info_models import HardwareManagerInterface

    hm = pysysinfo.HardwareManager()

    print(type(hm))
    print(isinstance(hm, HardwareManagerInterface))


Output:

.. code-block:: shell

    <class 'pysysinfo.dumps.mac.mac_dump.MacHardwareManager'>
    True

The type of HardwareManager instantiated depends on the OS.
On macOS, as we can see, the ``MacHardwareManager`` was instantiated.

------------

Depending on your OS, when ``HardwareManager()`` is called, one of the following classes will be instantiated:

.. autoclass:: pysysinfo.dumps.windows.windows_dump.WindowsHardwareManager
    :exclude-members: __init__,__new__
    :noindex:

.. autoclass:: pysysinfo.dumps.mac.mac_dump.MacHardwareManager
    :exclude-members: __init__,__new__
    :noindex:

.. autoclass:: pysysinfo.dumps.linux.linux_dump.LinuxHardwareManager
    :exclude-members: __init__,__new__
    :noindex:

------------

All ``HardwareManager`` classes have the following property and methods:

.. autoclass:: pysysinfo.models.info_models.HardwareManagerInterface
    :members:
    :noindex:


------------

We can now use this knowledge to query information about the hardware.

.. code-block:: python

    import pysysinfo

    hm = pysysinfo.HardwareManager()

    info = hm.fetch_hardware_info()
    print(type(info))

Output on a macOS machine:

.. code-block:: shell

    <class 'pysysinfo.models.info_models.MacHardwareInfo'>

------------

Information can be queried all at once, or on a per-component basis.

:meth:`fetch_hardware_info() <pysysinfo.models.info_models.HardwareManagerInterface.fetch_hardware_info>` can be used to query all info.

The other methods in the
:class:`HardwareManagerInterface <pysysinfo.models.info_models.HardwareManagerInterface>`
class can be used to query each component.

We explore this in the :ref:`querying-info` section.