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
