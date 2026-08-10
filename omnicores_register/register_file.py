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
from j2gpp.filters import humanize_title
from omnicores_register.component_container import ComponentContainer
from omnicores_register.enums import PackingPolicy, UNSPECIFIED



class RegisterFile(ComponentContainer):
  def __init__(
      self,
      name        : str,
      title       : Optional[str] = None,
      description : Optional[str] = "",
      offset      : Optional[int] = None,
      align       : Optional[int] = None,
      packing     : PackingPolicy = UNSPECIFIED,
    ):
    super().__init__(name, packing=packing)
    self.offset  = offset # Relative byte offset to the parent container (None for automatic)
    self.align   = align  # Align address to granularity
    self.address = None   # Absolute byte address, computed during elaboration
    self.size    = None   # Total byte size of the region, computed during elaboration

    # Human-readable documentation attributes
    self.title       = title or humanize_title(name)
    self.description = description or ""

    # Full hierarchical name including ancestor file names (computed during elaboration)
    self.hierarchical_name = None

    # Whether the file and all its descendants contain no software-visible components
    self.sw_struct_empty = False

    # Padding with previous register in the firmware struct header
    self.sw_struct_padding = 0

    # Trailing padding to fill power-of-two file structs
    self.sw_struct_tail_padding = 0

    # Whether this file is part of an array (set during elaboration)
    self.is_array_element = False
    # Array element index (set during elaboration)
    self.array_index = None

  def as_array(self, length:int, stride:int=None):
    """Create a ComponentArray for replication of this register file."""
    from omnicores_register.component_array import ComponentArray
    return ComponentArray(self, length=length, stride=stride)

  def get_breadcrumbs(self):
    """Return list for dotted breadcrumb navigation in HTML."""
    parts = self.hierarchical_name.split('__')
    breadcrumbs = []
    for index in range(len(parts)):
      prefix = '__'.join(parts[:index + 1])
      part_name = parts[index]
      if '_' in part_name:
        base, _, suffix = part_name.rpartition('_')
        if suffix.isdigit():
          part_name = f"{base}[{suffix}]"
      if index < len(parts) - 1:
        breadcrumbs.append({'name': part_name, 'anchor': '#file-' + prefix})
      else:
        breadcrumbs.append({'name': part_name, 'anchor': None})
    return breadcrumbs
