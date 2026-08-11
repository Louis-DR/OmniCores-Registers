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
from omnicores_register.component_array import ComponentArray
from omnicores_register.enums import (
  SoftwareAccessType,
  HardwareAccessType,
  HardwareWriteOptions,
  HardwareReadOptions,
  SoftwareWriteBehavior,
  SoftwareReadBehavior,
  PackingPolicy,
  UNSPECIFIED,
  register_default_software_access,
  register_default_hardware_access,
  field_default_software_access,
  field_default_hardware_access,
  register_default_hw_write_options,
  register_default_hw_read_options,
  register_default_sw_write_behavior,
  register_default_sw_read_behavior,
  field_default_hw_write_options,
  field_default_hw_read_options,
  field_default_sw_write_behavior,
  field_default_sw_read_behavior,
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
  # Iterate over sub-components
  for component in container.components:
    if isinstance(component, ComponentArray):
      # Resolve packing for the array prototype if it's a file
      if isinstance(component.prototype, RegisterFile):
        file_packing = component.prototype.packing
        if file_packing is UNSPECIFIED:
          file_packing = resolved
        if file_packing is UNSPECIFIED:
          file_packing = PackingPolicy.DENSE
        component.prototype.packing = file_packing
        _elaborate_inherited_settings(component.prototype, file_packing)
    elif isinstance(component, RegisterFile):
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
    # Handle array of registers or files
    if isinstance(component, ComponentArray):
      prototype = component.prototype
      if isinstance(prototype, RegisterFile):
        # Elaborate the prototype to determine its internal size
        end_address = _elaborate_addresses(prototype, component.address)
        dense_size = end_address - component.address
        if prototype.packing == PackingPolicy.POWER_OF_TWO:
          pow2_size = next_power_of_two(dense_size)
          prototype.size = pow2_size
          # Again we need to realign and therefore shift components
          misalignment = component.address % pow2_size
          if misalignment != 0:
            delta = pow2_size - misalignment
            component.address += delta
            _shift_addresses(prototype, delta)
            running_offset += delta
        else:
          prototype.size = dense_size
        # If stride not specified, default to the prototype size
        if component._stride is None:
          component._stride = prototype.size
        running_offset += component.region_size
      elif isinstance(prototype, Register):
        if component._stride is None:
          component._stride = 4
        running_offset += component.region_size
      # Sync prototype base address after any alignment shifts
      prototype.address = component.address
    # Recursively resolve the addresses for sub-files
    elif isinstance(component, RegisterFile):
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
    if isinstance(component, ComponentArray):
      prototype = component.prototype
      # Compute the base hierarchical name for the prototype
      prefix = f"{parent_prefix}__{prototype.name}" if parent_prefix else prototype.name
      prototype.hierarchical_name = prefix
      # If the prototype is a file, recurse into its children
      if isinstance(prototype, RegisterFile):
        _elaborate_hierarchical_names(prototype, prefix)
    elif isinstance(component, RegisterFile):
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
    if register.fields:
      for field in register.fields:
        field.software_access   = field.software_access   or register.software_access   or field_default_software_access
        field.hardware_access   = field.hardware_access   or register.hardware_access   or field_default_hardware_access
        field.hw_write_options  = field.hw_write_options  or register.hw_write_options  or field_default_hw_write_options
        field.hw_read_options   = field.hw_read_options   or register.hw_read_options   or field_default_hw_read_options
        field.sw_write_behavior = field.sw_write_behavior or register.sw_write_behavior or field_default_sw_write_behavior
        field.sw_read_behavior  = field.sw_read_behavior  or register.sw_read_behavior  or field_default_sw_read_behavior
    register.software_access   = register.software_access   or register_default_software_access
    register.hardware_access   = register.hardware_access   or register_default_hardware_access
    register.hw_write_options  = register.hw_write_options  or register_default_hw_write_options
    register.hw_read_options   = register.hw_read_options   or register_default_hw_read_options
    register.sw_write_behavior = register.sw_write_behavior or register_default_sw_write_behavior
    register.sw_read_behavior  = register.sw_read_behavior  or register_default_sw_read_behavior
    if register.fields:
      _upgrade_register_access_from_fields(register)
  _elaborate_array_prototype_access(container)



def _elaborate_array_prototype_access(container):
  """Resolve access policies on register prototypes inside ComponentArray wrappers."""
  for component in container.components:
    if isinstance(component, ComponentArray):
      prototype = component.prototype
      if isinstance(prototype, Register):
        prototype.software_access   = prototype.software_access   or register_default_software_access
        prototype.hardware_access   = prototype.hardware_access   or register_default_hardware_access
        prototype.hw_write_options  = prototype.hw_write_options  or register_default_hw_write_options
        prototype.hw_read_options   = prototype.hw_read_options   or register_default_hw_read_options
        prototype.sw_write_behavior = prototype.sw_write_behavior or register_default_sw_write_behavior
        prototype.sw_read_behavior  = prototype.sw_read_behavior  or register_default_sw_read_behavior
        if prototype.fields:
          for field in prototype.fields:
            field.software_access   = field.software_access   or prototype.software_access   or field_default_software_access
            field.hardware_access   = field.hardware_access   or prototype.hardware_access   or field_default_hardware_access
            field.hw_write_options  = field.hw_write_options  or prototype.hw_write_options  or field_default_hw_write_options
            field.hw_read_options   = field.hw_read_options   or prototype.hw_read_options   or field_default_hw_read_options
            field.sw_write_behavior = field.sw_write_behavior or prototype.sw_write_behavior or field_default_sw_write_behavior
            field.sw_read_behavior  = field.sw_read_behavior  or prototype.sw_read_behavior  or field_default_sw_read_behavior
          _upgrade_register_access_from_fields(prototype)
      elif isinstance(prototype, RegisterFile):
        _elaborate_array_prototype_access(prototype)
    elif isinstance(component, Register):
      component.software_access   = component.software_access   or register_default_software_access
      component.hardware_access   = component.hardware_access   or register_default_hardware_access
      component.hw_write_options  = component.hw_write_options  or register_default_hw_write_options
      component.hw_read_options   = component.hw_read_options   or register_default_hw_read_options
      component.sw_write_behavior = component.sw_write_behavior or register_default_sw_write_behavior
      component.sw_read_behavior  = component.sw_read_behavior  or register_default_sw_read_behavior
      if component.fields:
        for field in component.fields:
          field.software_access   = field.software_access   or component.software_access   or field_default_software_access
          field.hardware_access   = field.hardware_access   or component.hardware_access   or field_default_hardware_access
          field.hw_write_options  = field.hw_write_options  or component.hw_write_options  or field_default_hw_write_options
          field.hw_read_options   = field.hw_read_options   or component.hw_read_options   or field_default_hw_read_options
          field.sw_write_behavior = field.sw_write_behavior or component.sw_write_behavior or field_default_sw_write_behavior
          field.sw_read_behavior  = field.sw_read_behavior  or component.sw_read_behavior  or field_default_sw_read_behavior
        _upgrade_register_access_from_fields(component)
    elif isinstance(component, RegisterFile):
      _elaborate_array_prototype_access(component)



def _upgrade_register_access_from_fields(register):
  """Upgrade register access policies based on the access capabilities of its fields."""
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



def _has_visible_child(container):
  """Return True if the container has at least one software-visible direct child."""
  for child in container.components:
    if isinstance(child, ComponentArray):
      child_proto = child.prototype
      if isinstance(child_proto, Register):
        if child_proto.is_software_accessible():
          return True
      elif isinstance(child_proto, RegisterFile):
        if not child_proto.sw_struct_empty:
          return True
    elif isinstance(child, Register):
      if child.is_software_accessible():
        return True
    elif isinstance(child, RegisterFile):
      if not child.sw_struct_empty:
        return True
  return False



def _elaborate_sw_struct_accessibility(container):
  """Recursively determine which register files are empty in the firmware struct."""
  for component in container.components:
    if isinstance(component, ComponentArray):
      prototype = component.prototype
      if isinstance(prototype, RegisterFile):
        _elaborate_sw_struct_accessibility(prototype)
        prototype.sw_struct_empty = not _has_visible_child(prototype)
    elif isinstance(component, RegisterFile):
      _elaborate_sw_struct_accessibility(component)
      component.sw_struct_empty = not _has_visible_child(component)



def _elaborate_component_padding(container, container_address):
  """Recursively compute firmware struct padding for software-visible registers and files."""
  # List components that appear in the C header struct (accessible by software)
  fw_components = []
  for component in container.components:
    if isinstance(component, ComponentArray):
      prototype = component.prototype
      if isinstance(prototype, Register):
        if prototype.is_software_accessible():
          fw_components.append(component)
      elif isinstance(prototype, RegisterFile):
        _elaborate_component_padding(prototype, prototype.address)
        if not prototype.sw_struct_empty:
          fw_components.append(component)
    elif isinstance(component, Register):
      if component.is_software_accessible():
        fw_components.append(component)
    elif isinstance(component, RegisterFile):
      _elaborate_component_padding(component, component.address)
      if not component.sw_struct_empty:
        fw_components.append(component)
  # Compute the padding (components are already in address order from elaboration)
  previous_end_address = container_address
  for component in fw_components:
    component.sw_struct_padding = (component.address - previous_end_address) // 4
    if isinstance(component, ComponentArray):
      previous_end_address = component.address + component.region_size
    elif isinstance(component, RegisterFile):
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
  _elaborate_sw_struct_accessibility(self)

  # Padding before each register and file for the firmware struct header
  _elaborate_component_padding(self, 0)

  # Padding before each field for the firmware bitfield struct
  _elaborate_field_padding(self)
