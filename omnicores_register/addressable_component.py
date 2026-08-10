# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     OmniCores-Registers                                          ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Base class for register and register file, providing shared  ║
# ║              addressable attributes and breadcrumb navigation.            ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



from typing import Optional
from j2gpp.filters import humanize_title



class AddressableComponent:
  """Base class for addressable components like register and register file."""

  def __init__(
      self,
      name        : str,
      title       : Optional[str] = None,
      description : Optional[str] = "",
      offset      : Optional[int] = None,
      align       : Optional[int] = None,
    ):
    self.name              = name
    self.title             = title or humanize_title(name)
    self.description       = description or ""
    self.hierarchical_name = None

    self.offset            = offset
    self.align             = align
    self.address           = None

    self.sw_struct_padding = 0
    self.is_array_element  = False
    self.array_index       = None

  def get_breadcrumbs(self):
    """Return list for dotted breadcrumb navigation in HTML."""
    parts = self.hierarchical_name.split('__')
    breadcrumbs = []
    for index in range(len(parts)):
      prefix = '__'.join(parts[:index + 1])
      part_name = parts[index]
      # Convert underscore array-index suffix to bracket notation in all parts
      if '_' in part_name:
        base, _, suffix = part_name.rpartition('_')
        if suffix.isdigit():
          part_name = f"{base}[{suffix}]"
      if index < len(parts) - 1:
        breadcrumbs.append({'name': part_name, 'anchor': '#file-' + prefix})
      else:
        breadcrumbs.append({'name': part_name, 'anchor': None})
    return breadcrumbs
