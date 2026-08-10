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
from omnicores_register.addressable_component import AddressableComponent
from omnicores_register.accessible_component import AccessibleComponent



class Register(AddressableComponent, AccessibleComponent):
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
    AddressableComponent.__init__(self, name=name, title=title, description=description, offset=offset, align=align)
    AccessibleComponent.__init__(self, software_access=software_access, hardware_access=hardware_access)
    self.width       = width
    self.reset_value = reset_value
    self.fields      = fields or []

    # Padding after the last field to fill the register width
    self.sw_struct_fields_padding = 0

  def as_array(self, length:int, stride:int=None):
    """Create a ComponentArray for replication of this register."""
    from omnicores_register.component_array import ComponentArray
    if stride is not None:
      raise ValueError("Register arrays do not support a custom stride. The stride is always 4 bytes.")
    return ComponentArray(self, length=length, stride=4)

  def add(self, field:Field):
    self.fields.append(field)

  def _build_field_bit_map(self):
    """Pre-compute a list mapping each bit index to its owning field or None."""
    bit_map = [None] * self.width
    for field in self.fields:
      for bit in range(field.offset, field.offset + field.width):
        bit_map[bit] = field
    return bit_map

  def get_bit_grid(self, bits_per_row=8):
    """Return a list of rows for a visual bit-grid table, MSB to LSB."""
    if self.fields:
      bit_map = self._build_field_bit_map()
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
          owning_field = bit_map[bit]
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
