# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     OmniCores-Registers                                          ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Elaboration method of the register bank. It checks and       ║
# ║              computes attributes of the data structure before generation. ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



from math import ceil
from omnicores_register.utils import next_power_of_two
from omnicores_register.register_file import RegisterFile
from omnicores_register.register import Register
from omnicores_register.enums import (
  SoftwareAccessType,
  HardwareAccessType,
  PackingPolicy,
  UNSPECIFIED,
  register_default_software_access,
  register_default_hardware_access,
  field_default_software_access,
  field_default_hardware_access,
)



def _elaborate_inherited_settings(container, inherited_packing):
  """Resolve the packing policy through the container hierarchy."""
  # Resolve this container's effective packing for its children
  resolved = container.packing
  if resolved is UNSPECIFIED:
    resolved = inherited_packing
  if resolved is UNSPECIFIED:
    resolved = PackingPolicy.DENSE

  # For RegisterFiles, set their own packing attribute
  if isinstance(container, RegisterFile):
    container.packing = resolved

  for component in container.components:
    if isinstance(component, RegisterFile):
      file_packing = component.packing
      if file_packing is UNSPECIFIED:
        file_packing = resolved
      if file_packing is UNSPECIFIED:
        file_packing = PackingPolicy.DENSE
      component.packing = file_packing
      _elaborate_inherited_settings(component, file_packing)



def _shift_addresses(container, delta):
  """Add delta to every component's absolute address in the subtree."""
  for component in container.components:
    component.address += delta
    if isinstance(component, RegisterFile):
      _shift_addresses(component, delta)



def _elaborate_addresses(container, container_base):
  """Recursively resolve absolute addresses of registers and files within a container."""
  running_offset = 0
  # Iterate over components of this container
  for component in container.components:
    # If the designer specified an explicit offset for this component,
    # jump the running offset to that position within the parent container.
    if component.offset is not None:
      running_offset = component.offset
    # The alignment modulo applies on the offset
    if component.align is not None:
      running_offset = ceil(running_offset / component.align) * component.align
    # The absolute address is the container base plus the relative offset
    component.address = container_base + running_offset
    # TODO: check that the address is aligned to the register width
    # Recursively resolve the addresses for sub-files
    if isinstance(component, RegisterFile):
      # The sub-file components offsets are relative to this file's base address
      end_address = _elaborate_addresses(component, component.address)
      # Compute the file region size based on the packing policy
      dense_size = end_address - component.address
      if component.packing == PackingPolicy.POWER_OF_TWO:
        pow2_size = next_power_of_two(dense_size)
        component.size = pow2_size
        # Align the file base address to its size
        # We need to resolve the children to know the size of the file for the
        # alignment, but then we need to go back to the children to shift their
        # addresses.
        misalignment = component.address % pow2_size
        if misalignment != 0:
          delta = pow2_size - misalignment
          component.address += delta
          _shift_addresses(component, delta)
          running_offset += delta
      else:
        component.size = dense_size
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



def _elaborate_field_offsets(container):
  """Compute offsets of register fields."""
  for register in container.registers:
      if register.fields:
        running_offset = 0
        for field in register.fields:
          if field.align is not None:
            running_offset = ceil(running_offset / field.align) * field.align
          if field.offset is None:
            field.offset = running_offset
          else:
            running_offset = field.offset
          running_offset += field.width



def _elaborate_access_policies(container):
  """Compute software and hardware access policies for registers and fields."""
  for register in container.registers:
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



def _elaborate_file_emptiness(container):
  """Recursively determine which register files are empty in the firmware struct."""
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



def _elaborate_component_padding(container, container_address):
  """Recursively compute firmware struct padding for software-visible registers and files."""
  # List components that appear in the C header struct (accessible by software)
  fw_components = []
  for component in container.components:
    if isinstance(component, Register):
      if component.is_software_accessible():
        fw_components.append(component)
    elif isinstance(component, RegisterFile):
      _elaborate_component_padding(component, component.address)
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
  # For power-of-two files, compute trailing reserved words to fill the struct
  if isinstance(container, RegisterFile) and container.packing == PackingPolicy.POWER_OF_TWO:
    file_end = container.address + container.size
    container.sw_struct_tail_padding = (file_end - previous_end_address) // 4



def _elaborate_field_padding(container):
  """Compute firmware struct padding for software-visible fields."""
  for register in container.registers:
    if register.fields:
      previous_offset = 0
      for field in register.fields:
        if field.is_software_readable() or field.is_software_writable():
          field.sw_struct_padding = field.offset - previous_offset
          previous_offset = field.offset + field.width
      register.sw_struct_fields_padding = 32 - previous_offset



def elaborate(self):
  """Elaborate the data structure after configuration and before generation."""

  # Resolve packing policies
  _elaborate_inherited_settings(self, UNSPECIFIED)

  # Resolve addresses recursively
  _elaborate_addresses(self, 0)

  # Resolve hierarchical names recursively
  _elaborate_hierarchical_names(self, "")

  # Separate registers and files recursively
  self.registers = self.get_registers_deep()
  self.files     = self.get_files_deep()

  # Bit offset and padding of each register field
  _elaborate_field_offsets(self)

  # Access policy between fields and registers
  _elaborate_access_policies(self)

  # Compute which register files are empty in the firmware struct
  _elaborate_file_emptiness(self)

  # Padding before each register and file for the firmware struct header
  _elaborate_component_padding(self, 0)

  # Padding before each field for the firmware bitfield struct
  _elaborate_field_padding(self)
