from typing import Optional, List

from pydantic import BaseModel, Field

from pysysinfo.models.component_model import ComponentInfo
from pysysinfo.models.status_models import Status


class ResolutionInfo(BaseModel):
    """Resolution information for a Display."""

    #: Horizontal resolution in pixels.
    width: Optional[int] = None
    #: Vertical resolution in pixels.
    height: Optional[int] = None
    #: Refresh rate in Hz.
    refresh_rate: Optional[float] = None
    #: Bit depth in bits per pixel.
    bit_depth: Optional[int] = None


class DisplayModuleInfo(BaseModel):
    """Information for one Display is stored here"""
    status: Status = Field(default_factory=Status)

    name: Optional[str] = None

    #: Year it was manufactured / designed.
    year: Optional[int] = None

    #: ACPI path of the display device.
    acpi_path: Optional[str] = None

    #: Parent GPU driving this display
    gpu_name: Optional[str] = None

    resolution: Optional[ResolutionInfo] = None

    # Diagonal size in inches
    inches: Optional[int] = None

    # Orientation (landscape/portrait) (includes FLIPPED)
    orientation: Optional[str] = None

    # Display Interface (HDMI, DP, VGA, etc) - enum: DISPLAY_CON_TYPE
    interface: Optional[str] = None

    # Serial Number
    serial_number: Optional[str] = None

    #: Three-letter code assigned to each manufacturer.
    manufacturer_code: Optional[str] = None


class DisplayInfo(ComponentInfo):
    """Contains a list of ``DisplayModuleInfo`` objects."""

    #: List of GPU modules present in the system.
    modules: List[DisplayModuleInfo] = Field(default_factory=list)
