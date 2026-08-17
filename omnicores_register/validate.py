# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     OmniCores-Registers                                          ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Validation method of the register bank. It checks that there ║
# ║              are no conflicts or incompatibilities in the data structure. ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



from omnicores_register.utils import throw_warning, throw_error
from omnicores_register.register_file import RegisterFile
from omnicores_register.register import Register
from omnicores_register.enums import (
  HardwareWriteOptions,
  HardwareReadOptions,
  SoftwareWriteBehavior,
  SoftwareReadBehavior,
)



def _validate_symbol_conflicts(self) -> int:
  """Check the absence of entities with conflicting symbol names."""
  error_count = 0
  symbols = set()
  # Internal function to check a symbol and add it to the set
  def check_add_symbol(symbol:str):
    nonlocal error_count
    if symbol in symbols:
      throw_error(f"Conflict with two entities having the same symbol '{symbol}'.")
      error_count += 1
    symbols.add(symbol)
  # Add the symbols from the APB interface
  check_add_symbol("control__pclock")
  check_add_symbol("control__preset_n")
  check_add_symbol("control__psel")
  check_add_symbol("control__penable")
  check_add_symbol("control__pready")
  check_add_symbol("control__paddr")
  check_add_symbol("control__pwrite")
  check_add_symbol("control__pwdata")
  check_add_symbol("control__prdata")
  # Symbols of the register bank itself
  check_add_symbol(self.name)
  check_add_symbol(self.name+"__register_bank")
  # Symbols of the registers and their fields
  for register in self.registers:
    check_add_symbol(register.hierarchical_name)
    if register.fields:
      for field in register.fields:
        check_add_symbol(register.hierarchical_name+"__"+field.name)
  # Symbols of the register files
  for file in self.files:
    check_add_symbol(file.hierarchical_name)
  return error_count



def _validate_address_conflicts(self) -> int:
  """Check the absence of registers with conflicting addresses."""
  error_count = 0
  register_addresses = {}
  for register in self.registers:
    if register.address in register_addresses:
      conflicting_register = register_addresses[register.address]
      throw_error(f"Conflict between registers '{conflicting_register}' and '{register.name}' at the same address '0x{hex(register.address)[2:].upper()}'.")
      error_count += 1
    else:
      register_addresses[register.address] = register.name
  return error_count



def _validate_address_alignments(self) -> int:
  """Check the absence of registers with unaligned addresses."""
  error_count = 0
  for register in self.registers:
    # TODO: when variable register width is implemented, this should be fixed
    if register.address % 4 != 0:
      throw_error(f"Unaligned address '0x{hex(register.address)[2:].upper()}' for register '{register.name}'.")
      error_count += 1
  return error_count



def _validate_reset_access_behaviors(self) -> int:
  """Check the absence of registers or fields with reset access behaviors but no reset value."""
  error_count = 0
  for register in self.registers:
    if register.fields:
      for field in register.fields:
        if field.reset_value is None:
          if field.has_hw_write_option(HardwareWriteOptions.RESET):
            throw_error(f"Field '{register.hierarchical_name}.{field.name}' has a dedicated hardware reset signal but no defined reset value.")
            error_count += 1
          if field.sw_read_behavior == SoftwareReadBehavior.READ_RESETS:
            throw_error(f"Field '{register.hierarchical_name}.{field.name}' has a read-resets software access behavior but no defined reset value.")
            error_count += 1
    else:
      if register.reset_value is None:
        if register.has_hw_write_option(HardwareWriteOptions.RESET):
          throw_error(f"Register '{register.hierarchical_name}' has a dedicated hardware reset signal but no defined reset value.")
          error_count += 1
        if register.sw_read_behavior == SoftwareReadBehavior.READ_RESETS:
          throw_error(f"Register '{register.hierarchical_name}' has a read-resets software access behavior but no defined reset value.")
          error_count += 1
  return error_count



def _validate_access_options(self) -> int:
  """Check the compatibility of the software and hardware access options and behaviors with the access types."""
  error_count = 0
  def _validate_component_access_options(component, label:str) -> int:
    nonlocal error_count
    if component.sw_write_behavior != SoftwareWriteBehavior.NORMAL and not component.is_software_writable():
      throw_error(f"{label} has software write behavior '{component.sw_write_behavior!r}' but is not software writable.")
      error_count += 1
    if component.sw_read_behavior != SoftwareReadBehavior.NORMAL and not component.is_software_readable():
      throw_error(f"{label} has software read behavior '{component.sw_read_behavior!r}' but is not software readable.")
      error_count += 1
    if component.hw_write_options and not component.is_hardware_writable():
      throw_error(f"{label} has hardware write options '{component.hw_write_options!r}' but is not hardware writable.")
      error_count += 1
    if component.hw_read_options and not component.is_hardware_readable():
      throw_error(f"{label} has hardware read options '{component.hw_read_options!r}' but is not hardware readable.")
      error_count += 1
    if HardwareWriteOptions.CONTINUOUS in component.hw_write_options and component.hw_write_options != HardwareWriteOptions.CONTINUOUS:
      throw_error(f"{label} combines the continuous write option with other hardware write options '{component.hw_write_options!r}'.")
      error_count += 1
  for register in self.registers:
    if register.fields:
      for field in register.fields:
        _validate_component_access_options(field, f"Field '{register.hierarchical_name}.{field.name}'")
    else:
      _validate_component_access_options(register, f"Register '{register.hierarchical_name}'")
  return error_count



def _validate_field_placements(self) -> int:
  """Check the absence of overlapping or out-of-range fields in registers and array prototypes."""
  error_count = 0
  def _validate_register_field_placements(register) -> int:
    nonlocal error_count
    previous_end = 0
    for field in register.fields:  # Fields are sorted by offset during elaboration
      if field.offset < previous_end:
        throw_error(f"Field '{register.hierarchical_name}.{field.name}' overlaps with a previous field.")
        error_count += 1
      if field.offset + field.width > register.width:
        throw_error(f"Field '{register.hierarchical_name}.{field.name}' extends beyond the {register.width}-bit register width.")
        error_count += 1
      previous_end = field.offset + field.width
  for register in self.registers:
    if not register.is_array_element:
      _validate_register_field_placements(register)
  for prototype in self.get_array_prototype_registers():
    _validate_register_field_placements(prototype)
  return error_count



def validate(self) -> int:
  """Validate the data structure after elaboration and before generation, optional but highly recommended."""
  error_count  = 0
  error_count += _validate_symbol_conflicts(self)
  error_count += _validate_address_conflicts(self)
  error_count += _validate_address_alignments(self)
  error_count += _validate_reset_access_behaviors(self)
  error_count += _validate_access_options(self)
  error_count += _validate_field_placements(self)
  return error_count