# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     OmniCores-Registers                                          ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Register object class.                                       ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



from typing import Optional
from j2gpp.filters import humanize_title
from omnicores_register.enums import SoftwareAccessType, HardwareAccessType
from omnicores_register.field import Field



class Register:
  def __init__(
      self,
      name            : str,
      title           : Optional[str]                = None,
      description     : Optional[str]                = "",
      width           : int                          = 32,
      offset          : Optional[int]                = None,
      align           : Optional[int]                = None,
      reset_value     : Optional[int]                = 0,
      software_access : Optional[SoftwareAccessType] = None, # Default defined in elaboration
      hardware_access : Optional[HardwareAccessType] = None, # Default defined in elaboration
      fields          : Optional[list[Field]]        = None,
    ):
    self.name              = name
    self.width             = width
    self.offset            = offset
    self.align             = align # Align address to granularity
    self.address           = None
    self.reset_value       = reset_value
    self.software_access   = software_access
    self.hardware_access   = hardware_access
    self.fields            = fields or []

    # Human-readable documentation attributes
    self.title       = title or humanize_title(name)
    self.description = description or ""

    # Full hierarchical name including ancestor file names (computed during elaboration)
    self.hierarchical_name = None

    # Padding with previous register
    self.sw_struct_padding = 0
    # Padding after the last field to fill the register width
    self.sw_struct_fields_padding = 0

    # Whether this register is part of an array (set during elaboration)
    self.is_array_element = False
    # Array element index (set during elaboration)
    self.array_index = None

  def as_array(self, length:int, stride:int=None):
    """Create a ComponentArray for replication of this register."""
    from omnicores_register.component_array import ComponentArray
    if stride is not None:
      raise ValueError("Register arrays do not support a custom stride. The stride is always 4 bytes.")
    return ComponentArray(self, length=length, stride=4)

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

  def get_bit_grid(self, bits_per_row=8):
    """Return a list of rows for a visual bit-grid table, MSB to LSB."""
    rows = []
    for row_start in range(self.width - 1, -1, -bits_per_row):
      if not self.fields:
        row = [{
          'name': self.name,
          'colspan': min(bits_per_row, row_start + 1),
          'is_field': True,
          'most_significant_bit': row_start,
          'least_significant_bit': max(row_start - bits_per_row + 1, 0),
        }]
      else:
        row = []
        for bit in range(row_start, max(row_start - bits_per_row, -1), -1):
          owning_field = None
          for candidate in self.fields:
            if candidate.offset <= bit < candidate.offset + candidate.width:
              owning_field = candidate
              break

          cell_name = owning_field.name if owning_field else ''

          if not row or row[-1]['name'] != cell_name:
            row.append({
              'name': cell_name,
              'colspan': 1,
              'is_field': owning_field is not None,
              'most_significant_bit': bit,
              'least_significant_bit': bit,
            })
          else:
            row[-1]['colspan'] += 1
            row[-1]['least_significant_bit'] = bit

      rows.append(row)

    return rows
