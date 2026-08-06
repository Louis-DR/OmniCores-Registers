# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     OmniCores-Registers                                          ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Register object class.                                       ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



from typing import Optional
from omnicores_register.enums import SoftwareAccessType, HardwareAccessType
from omnicores_register.field import Field



class Register:
  def __init__(
      self,
      name            : str,
      width           : int                          = 32,
      offset          : Optional[int]                = None,
      reset_value     : Optional[int]                = 0,
      software_access : Optional[SoftwareAccessType] = None, # Default defined in elaboration
      hardware_access : Optional[HardwareAccessType] = None, # Default defined in elaboration
      fields          : Optional[list[Field]]        = None,
    ):
    self.name              = name
    self.width             = width
    self.offset            = offset
    self.address           = None
    self.reset_value       = reset_value
    self.software_access   = software_access
    self.hardware_access   = hardware_access
    self.fields            = fields or []

    # Full hierarchical name including ancestor file names (computed during elaboration)
    self.hierarchical_name = None

    # Padding with previous register
    self.sw_struct_padding = 0
    # Padding after the last field to fill the register width
    self.sw_struct_fields_padding = 0

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

  def add_field(self, field:Field):
    self.fields.append(field)
