# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     OmniCores-Registers                                          ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Enumerated values for the API.                               ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



from enum import Enum, auto



class SoftwareAccessType(Enum):
  NONE       = auto()
  READ_ONLY  = auto()
  WRITE_ONLY = auto()
  READ_WRITE = auto()



class HardwareAccessType(Enum):
  NONE       = auto()
  READ_ONLY  = auto()
  WRITE_ONLY = auto()
  READ_WRITE = auto()



# Default access types
register_default_software_access = SoftwareAccessType.READ_WRITE
register_default_hardware_access = HardwareAccessType.READ_ONLY
field_default_software_access    = SoftwareAccessType.READ_WRITE
field_default_hardware_access    = HardwareAccessType.READ_ONLY
