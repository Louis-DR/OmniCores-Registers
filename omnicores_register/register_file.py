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
from omnicores_register.addressable_component import AddressableComponent
from omnicores_register.enums import PackingPolicy, UNSPECIFIED



class RegisterFile(ComponentContainer, AddressableComponent):
  def __init__(
      self,
      name        : str,
      title       : Optional[str] = None,
      description : Optional[str] = "",
      offset      : Optional[int] = None,
      align       : Optional[int] = None,
      packing     : PackingPolicy = UNSPECIFIED,
    ):
    ComponentContainer.__init__(self, name, packing=packing)
    AddressableComponent.__init__(self, name=name, title=title, description=description, offset=offset, align=align)

    # Total byte size of the region (computed during elaboration)
    self.size = None

    # Whether the file and all its descendants contain no software-visible components
    self.sw_struct_empty = False

    # Trailing padding to fill power-of-two file structs
    self.sw_struct_tail_padding = 0

  def as_array(self, length:int, stride:int=None):
    """Create a ComponentArray for replication of this register file."""
    from omnicores_register.component_array import ComponentArray
    return ComponentArray(self, length=length, stride=stride)
