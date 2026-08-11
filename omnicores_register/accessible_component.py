# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     OmniCores-Registers                                          ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Base class providing software and hardware access policy     ║
# ║              attributes and check methods for register and field.         ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



from typing import Optional
from omnicores_register.enums import (
  SoftwareAccessType,
  HardwareAccessType,
  HardwareWriteOptions,
  HardwareReadOptions,
  SoftwareWriteBehavior,
  SoftwareReadBehavior,
)



class AccessibleComponent:
  """Base class holding software/hardware access attributes and associated methods."""

  def __init__(
      self,
      software_access   : Optional[SoftwareAccessType]    = None,  # Default defined in elaboration
      hardware_access   : Optional[HardwareAccessType]    = None,  # Default defined in elaboration
      hw_write_options  : Optional[HardwareWriteOptions]  = None,  # Default defined in elaboration
      hw_read_options   : Optional[HardwareReadOptions]   = None,  # Default defined in elaboration
      sw_write_behavior : Optional[SoftwareWriteBehavior] = None,  # Default defined in elaboration
      sw_read_behavior  : Optional[SoftwareReadBehavior]  = None,  # Default defined in elaboration
    ):
    self.software_access   = software_access
    self.hardware_access   = hardware_access
    self.hw_write_options  = hw_write_options
    self.hw_read_options   = hw_read_options
    self.sw_write_behavior = sw_write_behavior
    self.sw_read_behavior  = sw_read_behavior

  def is_software_readable(self) -> bool:
    return self.software_access in [SoftwareAccessType.READ_ONLY, SoftwareAccessType.READ_WRITE]

  def is_software_writable(self) -> bool:
    return self.software_access in [SoftwareAccessType.WRITE_ONLY, SoftwareAccessType.READ_WRITE]

  def is_software_accessible(self) -> bool:
    return self.is_software_readable() or self.is_software_writable()

  def is_hardware_readable(self) -> bool:
    return self.hardware_access in [HardwareAccessType.READ_ONLY, HardwareAccessType.READ_WRITE]

  def is_hardware_writable(self) -> bool:
    return self.hardware_access in [HardwareAccessType.WRITE_ONLY, HardwareAccessType.READ_WRITE]

  def is_hardware_accessible(self) -> bool:
    return self.is_hardware_readable() or self.is_hardware_writable()

  def has_hw_write_option(self, option:HardwareWriteOptions):
    """Return True if the given HardwareWriteOptions flag is set on this component."""
    return option in self.hw_write_options

  def has_hw_read_option(self, option:HardwareReadOptions):
    """Return True if the given HardwareReadOptions flag is set on this component."""
    return option in self.hw_read_options
