# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     OmniCores-Registers                                          ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Elaboration method of the register bank. It checks and       ║
# ║              computes attributes of the data structure before generation. ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



from omnicores_register.register_file import RegisterFile
from omnicores_register.register import Register
from omnicores_register.enums import (
  SoftwareAccessType,
  HardwareAccessType,
  register_default_software_access,
  register_default_hardware_access,
  field_default_software_access,
  field_default_hardware_access,
)



def _elaborate_addresses(container, container_base):
  """Recursively resolve absolute addresses of registers and files within a container."""
  running_offset = 0
  # Iterate over components of this container
  for component in container.components:
    # If the designer specified an explicit offset for this component,
    # jump the running offset to that position within the parent container.
    if component.offset is not None:
      running_offset = component.offset
    # The absolute address is the container base plus the relative offset
    component.address = container_base + running_offset
    # Recursively resolve the addresses for sub-files
    if isinstance(component, RegisterFile):
      # The sub-file components offsets are relative to this file's base address
      end_address = _elaborate_addresses(component, component.address)
      # The file region size is the bounding box of its children
      component.size = end_address - component.address
      running_offset += component.size
    # Each register occupies 4 bytes (32-bit word alignment)
    elif isinstance(component, Register):
      running_offset += 4
  return container_base + running_offset



def _elaborate_hierarchical_names(container, parent_prefix):
  """Recursively compute hierarchical names for all registers and files."""
  for component in container.components:
    if isinstance(component, RegisterFile):
      prefix = f"{parent_prefix}__{component.name}" if parent_prefix else component.name
      component.hierarchical_name = prefix
      _elaborate_hierarchical_names(component, prefix)
    elif isinstance(component, Register):
      component.hierarchical_name = f"{parent_prefix}__{component.name}" if parent_prefix else component.name



def _elaborate_file_emptiness(container):
  """Recursively determine which register files are empty in the firmware struct.

  A file is empty if none of its direct children are software-visible:
  registers must pass is_software_accessible(), and sub-files must not be
  empty themselves. Uses post-order so children are evaluated first.
  """
  for component in container.components:
    if isinstance(component, RegisterFile):
      _elaborate_file_emptiness(component)

      has_visible_child = False
      for child in component.components:
        if isinstance(child, Register):
          if child.is_software_accessible():
            has_visible_child = True
            break
        elif isinstance(child, RegisterFile):
          if not child.sw_struct_empty:
            has_visible_child = True
            break
      component.sw_struct_empty = not has_visible_child



def _elaborate_struct_padding(container, container_address):
  """Recursively compute firmware struct padding for software-visible components."""
  # List components that appear in the C header struct (accessible by software)
  fw_components = []
  for component in container.components:
    if isinstance(component, Register):
      if component.is_software_accessible():
        fw_components.append(component)
    elif isinstance(component, RegisterFile):
      _elaborate_struct_padding(component, component.address)
      if not component.sw_struct_empty:
        fw_components.append(component)

  # Sort by address
  fw_components.sort(key=lambda component: component.address)

  # Compute the padding
  previous_end_address = container_address
  for component in fw_components:
    component.sw_struct_padding = (component.address - previous_end_address) // 4
    if isinstance(component, RegisterFile):
      previous_end_address = component.address + component.size
    else:
      previous_end_address = component.address + 4



def elaborate(self):
  """Elaborate the data structure after configuration and before generation."""
  # Resolve addresses recursively
  _elaborate_addresses(self, 0)

  # Resolve hierarchical names recursively
  _elaborate_hierarchical_names(self, "")

  # Separate registers and files recursively
  self.registers = self.get_registers_deep()
  self.files     = self.get_files_deep()

  # Bit offset and padding of each register field
  for register in self.registers:
    if register.fields:
      running_offset = 0
      for field in register.fields:
        if field.offset is None:
          field.offset = running_offset
        else:
          running_offset = field.offset
        running_offset += field.width

  # Access policy between fields and registers
  for register in self.registers:
    # If the register has fields, for fields that do have a specified access policy,
    # they take the policy of their register, or the default if the register also
    # doesn't have an explicit policy.
    if register.fields:
      for field in register.fields:
        field.software_access = field.software_access or register.software_access or field_default_software_access
        field.hardware_access = field.hardware_access or register.hardware_access or field_default_hardware_access
    register.software_access = register.software_access or register_default_software_access
    register.hardware_access = register.hardware_access or register_default_hardware_access
    # Upgrade register access policies according to its fields
    if register.fields:
      for field in register.fields:
        if field.is_software_writable():
          register.software_access = {
            SoftwareAccessType.NONE       : SoftwareAccessType.WRITE_ONLY,
            SoftwareAccessType.READ_ONLY  : SoftwareAccessType.READ_WRITE,
            SoftwareAccessType.WRITE_ONLY : SoftwareAccessType.WRITE_ONLY,
            SoftwareAccessType.READ_WRITE : SoftwareAccessType.READ_WRITE,
          }[register.software_access]
        if field.is_software_readable():
          register.software_access = {
            SoftwareAccessType.NONE       : SoftwareAccessType.READ_ONLY,
            SoftwareAccessType.READ_ONLY  : SoftwareAccessType.READ_ONLY,
            SoftwareAccessType.WRITE_ONLY : SoftwareAccessType.READ_WRITE,
            SoftwareAccessType.READ_WRITE : SoftwareAccessType.READ_WRITE,
          }[register.software_access]
        if field.is_hardware_writable():
          register.hardware_access = {
            HardwareAccessType.NONE       : HardwareAccessType.WRITE_ONLY,
            HardwareAccessType.READ_ONLY  : HardwareAccessType.READ_WRITE,
            HardwareAccessType.WRITE_ONLY : HardwareAccessType.WRITE_ONLY,
            HardwareAccessType.READ_WRITE : HardwareAccessType.READ_WRITE,
          }[register.hardware_access]
        if field.is_hardware_readable():
          register.hardware_access = {
            HardwareAccessType.NONE       : HardwareAccessType.READ_ONLY,
            HardwareAccessType.READ_ONLY  : HardwareAccessType.READ_ONLY,
            HardwareAccessType.WRITE_ONLY : HardwareAccessType.READ_WRITE,
            HardwareAccessType.READ_WRITE : HardwareAccessType.READ_WRITE,
          }[register.hardware_access]

  # Compute which register files are empty in the firmware struct
  _elaborate_file_emptiness(self)

  # Padding before each register and file for the firmware struct header.
  # Computed recursively per container : only direct children appear
  # in a container's struct, and sub-files are recursed into for their own
  # internal padding.
  _elaborate_struct_padding(self, 0)

  # Padding before each field for the firmware bitfield struct
  for register in self.registers:
    if register.fields:
      previous_offset = 0
      for field in register.fields:
        if field.is_software_readable() or field.is_software_writable():
          field.sw_struct_padding = field.offset - previous_offset
          previous_offset = field.offset + field.width
      register.sw_struct_fields_padding = 32 - previous_offset
