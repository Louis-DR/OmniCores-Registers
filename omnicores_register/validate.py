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



def validate(self) -> int:
  """Validate the data structure after elaboration and before generation, optional but highly recommended."""
  error_count  = 0
  error_count += _validate_symbol_conflicts(self)
  error_count += _validate_address_conflicts(self)
  error_count += _validate_address_alignments(self)
  error_count += _validate_reset_access_behaviors(self)
  return error_count