.. _hardware-managers:

=================
Hardware Managers
=================

The first step to retrieving hardware information is to instantiate a ``HardwareManager``.

Depending on the OS present, HWProbe can automatically load the appropriate Hardware Manager class.
The Hardware Manager classes implement the structure of :class:`HardwareManagerInterface <hwprobe.models.info_models.HardwareManagerInterface>`.


--------------------------------
Instantiating a Hardware Manager
--------------------------------
Instantiating a hardware manager is the same regardless of the OS.
The following codeblock shows how a ``HardwareManager`` is instantiated.

.. code-block:: python

    import hwprobe
    from hwprobe.models.info_models import HardwareManagerInterface

    hm = hwprobe.HardwareManager()

    print(type(hm))
    print(isinstance(hm, HardwareManagerInterface))


Output:

.. code-block:: shell

    <class 'hwprobe.core.mac.MacHardwareManager'>
    True

The type of HardwareManager instantiated depends on the OS.
On macOS, as we can see, the ``MacHardwareManager`` was instantiated.

------------

Depending on your OS, when ``HardwareManager()`` is called, one of the following classes will be instantiated:

.. autoclass:: hwprobe.core.windows.manager.WindowsHardwareManager
    :exclude-members: __init__,__new__
    :noindex:

.. autoclass:: hwprobe.core.mac.manager.MacHardwareManager
    :exclude-members: __init__,__new__
    :noindex:

.. autoclass:: hwprobe.core.linux.manager.LinuxHardwareManager
    :exclude-members: __init__,__new__
    :noindex:

------------

All ``HardwareManager`` classes have the following property and methods:

.. autoclass:: hwprobe.models.info_models.HardwareManagerInterface
    :members:
    :noindex:


------------

We can now use this knowledge to query information about the hardware.

.. code-block:: python

    import hwprobe

    hm = hwprobe.HardwareManager()

    info = hm.fetch_hardware_info()
    print(type(info))

Output on a macOS machine:

.. code-block:: shell

    <class 'hwprobe.models.info_models.MacHardwareInfo'>

------------

Information can be queried all at once, or on a per-component basis.

:meth:`fetch_hardware_info() <hwprobe.models.info_models.HardwareManagerInterface.fetch_hardware_info>` can be used to query all info.

The other methods in the
:class:`HardwareManagerInterface <hwprobe.models.info_models.HardwareManagerInterface>`
class can be used to query each component.

We explore this in the :ref:`querying-info` section.