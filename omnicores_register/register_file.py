# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     OmniCores-Registers                                          ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Register file object class. A register file is a container   ║
# ║              for registers and sub-files, forming a hierarchical region   ║
# ║              within the register bank.                                    ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



from typing import Optional
from omnicores_register.component_container import ComponentContainer



class RegisterFile(ComponentContainer):
  def __init__(
      self,
      name   : str,
      offset : Optional[int] = None,
    ):
    super().__init__(name)
    self.offset  = offset # Relative byte offset to the parent container (None for automatic)
    self.address = None   # Absolute byte address, computed during elaboration
    self.size    = None   # Total byte size of the region, computed during elaboration

    # Padding with previous register in the firmware struct header
    self.sw_struct_padding = 0
