# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     OmniCores-Registers                                          ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Elaboration method of the register bank. It checks and       ║
# ║              computes attributes of the data structure before generation. ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



from math import ceil, log2
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



def _resolve_field_offsets(register):
  """Compute offsets of the fields of a register and sort them by offset."""
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
    register.fields.sort(key=lambda field: field.offset)



def _elaborate_field_offsets(container):
  """Compute offsets of register fields for regular registers and array prototypes."""
  for register in container.registers:
    _resolve_field_offsets(register)
  for prototype in container.get_array_prototype_registers():
    _resolve_field_offsets(prototype)



def _resolve_sw_read_side_effect_init(component):
  """Return the initialization mechanism key used by the testbench to set a known value on a component before testing its software read side-effect."""
  if component.sw_read_behavior == SoftwareReadBehavior.READ_CLEARS:
    # Need to set all bits to 1
    if component.is_software_writable() and component.sw_write_behavior == SoftwareWriteBehavior.NORMAL:
      return 'sw_normal_write'
    if component.is_hardware_writable() and component.has_hw_write_option(HardwareWriteOptions.ENABLE):
      return 'hw_enable_write'
    if component.is_software_writable() and component.sw_write_behavior == SoftwareWriteBehavior.WRITE_ONE_SETS:
      return 'sw_write_one_sets'
    if component.is_software_writable() and component.sw_write_behavior == SoftwareWriteBehavior.WRITE_ZERO_SETS:
      return 'sw_write_zero_sets'
    if component.is_hardware_writable() and component.has_hw_write_option(HardwareWriteOptions.SET_ALL):
      return 'hw_set_all'
    if component.is_hardware_writable() and component.has_hw_write_option(HardwareWriteOptions.SET_MASK):
      return 'hw_set_mask'
  elif component.sw_read_behavior == SoftwareReadBehavior.READ_SETS:
    # Need to clear all bits to 0
    if component.is_software_writable() and component.sw_write_behavior == SoftwareWriteBehavior.NORMAL:
      return 'sw_normal_write'
    if component.is_hardware_writable() and component.has_hw_write_option(HardwareWriteOptions.ENABLE):
      return 'hw_enable_write'
    if component.is_software_writable() and component.sw_write_behavior == SoftwareWriteBehavior.WRITE_ONE_CLEARS:
      return 'sw_write_one_clears'
    if component.is_software_writable() and component.sw_write_behavior == SoftwareWriteBehavior.WRITE_ZERO_CLEARS:
      return 'sw_write_zero_clears'
    if component.is_hardware_writable() and component.has_hw_write_option(HardwareWriteOptions.CLEAR_ALL):
      return 'hw_clear_all'
    if component.is_hardware_writable() and component.has_hw_write_option(HardwareWriteOptions.CLEAR_MASK):
      return 'hw_clear_mask'
  elif component.sw_read_behavior == SoftwareReadBehavior.READ_RESETS:
    # Need to set a value different from the reset value
    if component.reset_value is None:
      return None
    if component.is_software_writable() and component.sw_write_behavior == SoftwareWriteBehavior.NORMAL:
      return 'sw_normal_write'
    if component.is_hardware_writable() and component.has_hw_write_option(HardwareWriteOptions.ENABLE):
      return 'hw_enable_write'
  return None



def _elaborate_sw_read_side_effects(bank):
  """Flag non-NORMAL software read behaviors and resolve the testbench initialization mechanism."""
  for register in bank.registers:
    if register.fields:
      for field in register.fields:
        if field.sw_read_behavior != SoftwareReadBehavior.NORMAL:
          register.has_sw_read_side_effect = True
          bank.has_sw_read_side_effect = True
          field.sw_read_side_effect_init = _resolve_sw_read_side_effect_init(field)
    elif register.sw_read_behavior != SoftwareReadBehavior.NORMAL:
      register.has_sw_read_side_effect = True
      bank.has_sw_read_side_effect = True
      register.sw_read_side_effect_init = _resolve_sw_read_side_effect_init(register)



def _elaborate_sw_write_once(bank):
  """Flag write-once software access to gate the dedicated RTL and testbench sections."""
  for register in bank.registers:
    if register.fields:
      for field in register.fields:
        if field.is_software_write_once():
          bank.has_sw_write_once = True
          return
    elif register.is_software_write_once():
      bank.has_sw_write_once = True
      return



def _resolve_register_access(register):
  """Resolve software and hardware access policies and options for a register and its fields."""
  if register.fields:
    for field in register.fields:
      field.software_access   = field.software_access   or register.software_access   or field_default_software_access
      field.hardware_access   = field.hardware_access   or register.hardware_access   or field_default_hardware_access
      field.hw_write_options  = field.hw_write_options  or register.hw_write_options  or (field_default_hw_write_options if field.is_hardware_writable() else HardwareWriteOptions(0))
      field.hw_read_options   = field.hw_read_options   or register.hw_read_options   or (field_default_hw_read_options  if field.is_hardware_readable()  else HardwareReadOptions(0))
      field.sw_write_behavior = field.sw_write_behavior or register.sw_write_behavior or field_default_sw_write_behavior
      field.sw_read_behavior  = field.sw_read_behavior  or register.sw_read_behavior  or field_default_sw_read_behavior
  register.software_access   = register.software_access   or register_default_software_access
  register.hardware_access   = register.hardware_access   or register_default_hardware_access
  if register.fields:
    _upgrade_register_access_from_fields(register)
  register.hw_write_options  = register.hw_write_options  or (register_default_hw_write_options if register.is_hardware_writable() else HardwareWriteOptions(0))
  register.hw_read_options   = register.hw_read_options   or (register_default_hw_read_options  if register.is_hardware_readable()  else HardwareReadOptions(0))
  register.sw_write_behavior = register.sw_write_behavior or register_default_sw_write_behavior
  register.sw_read_behavior  = register.sw_read_behavior  or register_default_sw_read_behavior



def _elaborate_access_policies(container):
  """Compute software and hardware access policies for registers, fields, and array prototypes."""
  for register in container.registers:
    _resolve_register_access(register)
  for prototype in container.get_array_prototype_registers():
    _resolve_register_access(prototype)



def _upgrade_register_access_from_fields(register):
  """Upgrade register access policies based on the access capabilities of its fields."""
  for field in register.fields:
    if field.is_software_writable():
      register.software_access = {
        SoftwareAccessType.NONE            : SoftwareAccessType.WRITE_ONLY,
        SoftwareAccessType.READ_ONLY       : SoftwareAccessType.READ_WRITE,
        SoftwareAccessType.WRITE_ONLY      : SoftwareAccessType.WRITE_ONLY,
        SoftwareAccessType.READ_WRITE      : SoftwareAccessType.READ_WRITE,
        SoftwareAccessType.WRITE_ONCE      : SoftwareAccessType.WRITE_ONCE,
        SoftwareAccessType.READ_WRITE_ONCE : SoftwareAccessType.READ_WRITE_ONCE,
      }[register.software_access]
    if field.is_software_readable():
      register.software_access = {
        SoftwareAccessType.NONE            : SoftwareAccessType.READ_ONLY,
        SoftwareAccessType.READ_ONLY       : SoftwareAccessType.READ_ONLY,
        SoftwareAccessType.WRITE_ONLY      : SoftwareAccessType.READ_WRITE,
        SoftwareAccessType.READ_WRITE      : SoftwareAccessType.READ_WRITE,
        SoftwareAccessType.WRITE_ONCE      : SoftwareAccessType.READ_WRITE_ONCE,
        SoftwareAccessType.READ_WRITE_ONCE : SoftwareAccessType.READ_WRITE_ONCE,
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



def _resolve_field_padding(register):
  """Compute firmware struct padding for the software-visible fields of a register."""
  if register.fields:
    previous_offset = 0
    for field in register.fields:
      if field.is_software_readable() or field.is_software_writable():
        field.sw_struct_padding = field.offset - previous_offset
        previous_offset = field.offset + field.width
    register.sw_struct_fields_padding = register.width - previous_offset



def _elaborate_field_padding(bank):
  """Compute firmware struct padding for software-visible fields of regular registers and array prototypes."""
  for register in bank.registers:
    _resolve_field_padding(register)
  for prototype in bank.get_array_prototype_registers():
    _resolve_field_padding(prototype)



def _elaborate_bank_address_width(bank):
  """Compute the bit width of the address signal."""
  last_address = max(bank.registers, key=lambda register : register.address).address
  last_address_pow2 = next_power_of_two(last_address)
  bank.address_width = int(log2(last_address_pow2))
  bank.address_width_nibbles = ceil(bank.address_width / 4)



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

  # Flag software read side effect behaviors
  _elaborate_sw_read_side_effects(self)

  # Flag write-once software access
  _elaborate_sw_write_once(self)

  # Compute which register files are empty in the firmware struct
  _elaborate_sw_struct_accessibility(self)

  # Padding before each register and file for the firmware struct header
  _elaborate_component_padding(self, 0)

  # Padding before each field for the firmware bitfield struct
  _elaborate_field_padding(self)

  # Bank address bus width
  _elaborate_bank_address_width(self)