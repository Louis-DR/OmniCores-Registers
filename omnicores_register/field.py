# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     OmniCores-Registers                                          ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Register field object class.                                 ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



from typing import Optional
from j2gpp.filters import humanize_title
from omnicores_register.enums import SoftwareAccessType, HardwareAccessType, HardwareWriteOptions, HardwareReadOptions, SoftwareWriteBehavior, SoftwareReadBehavior
from omnicores_register.accessible_component import AccessibleComponent



class Field(AccessibleComponent):
  def __init__(
      self,
      name              : str,
      title             : Optional[str]                   = None,
      description       : Optional[str]                   = "",
      width             : int                             = 1,
      offset            : Optional[int]                   = None,
      align             : Optional[int]                   = None,
      reset_value       : Optional[int]                   = 0,
      software_access   : Optional[SoftwareAccessType]    = None,  # Default defined in elaboration
      hardware_access   : Optional[HardwareAccessType]    = None,  # Default defined in elaboration
      hw_read_options   : Optional[HardwareReadOptions]   = None,  # Default defined in elaboration
      hw_write_options  : Optional[HardwareWriteOptions]  = None,  # Default defined in elaboration
      sw_write_behavior : Optional[SoftwareWriteBehavior] = None,  # Default defined in elaboration
      sw_read_behavior  : Optional[SoftwareReadBehavior]  = None,  # Default defined in elaboration
    ):
    AccessibleComponent.__init__(
      self,
      software_access   = software_access,
      hardware_access   = hardware_access,
      hw_write_options  = hw_write_options,
      hw_read_options   = hw_read_options,
      sw_write_behavior = sw_write_behavior,
      sw_read_behavior  = sw_read_behavior
    )
    self.name        = name
    self.width       = width
    self.offset      = offset
    self.align       = align # Align offset to granularity
    self.reset_value = reset_value

    # Human-readable documentation attributes
    self.title       = title or humanize_title(name)
    self.description = description or ""

    # Padding with previous field
    self.sw_struct_padding = 0
