# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     OmniCores-Registers                                          ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Register field object class.                                 ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



from typing import Optional
from omnicores_register.enums import SoftwareAccessType, HardwareAccessType



class Field:
  def __init__(
      self,
      name            : str,
      width           : int                          = 1,
      offset          : Optional[int]                = None,
      reset_value     : Optional[int]                = 0,
      software_access : Optional[SoftwareAccessType] = None, # Default defined in elaboration
      hardware_access : Optional[HardwareAccessType] = None, # Default defined in elaboration
    ):
    self.name              = name
    self.width             = width
    self.offset            = offset
    self.reset_value       = reset_value
    self.software_access   = software_access
    self.hardware_access   = hardware_access

    # Padding with previous field
    self.sw_struct_padding = 0

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
