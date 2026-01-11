from typing import Optional

from pysysinfo.models.component_model import ComponentInfo

class BaseboardInfo(ComponentInfo):
    """Baseboard (Motherboard) information model."""

    # Manufacturer of the baseboard
    manufacturer: Optional[str] = None

    # Model of the baseboard
    model: Optional[str] = None

    # Chassis type of the baseboard
    chassis_type: Optional[str] = None

    # CPU socket type on the baseboard
    cpu_socket: Optional[str] = None