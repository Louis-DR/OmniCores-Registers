# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     OmniCores-Registers                                          ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Elaboration method of the register bank. It checks and       ║
# ║              computes attributes of the data structure before generation. ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



from omnicores_register.enums import (
  SoftwareAccessType,
  HardwareAccessType,
  register_default_software_access,
  register_default_hardware_access,
  field_default_software_access,
  field_default_hardware_access,
)



def elaborate(self):
  """Elaborate the data structure after configuration and before generation."""
  # Address offset of each register
  running_address = 0
  for register in self.registers:
    if register.offset is None:
      register.address = running_address
    else:
      register.address = register.offset
      running_address  = register.offset
    running_address += 4

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

  # Padding before each register and fields for firmware struct header
  previous_address = -4
  for register in self.registers:
    if register.is_software_readable() or register.is_software_writable():
      register.sw_struct_padding = (register.address - previous_address - 4) // 4
      previous_address = register.address
    if register.fields:
      previous_offset = 0
      for field in register.fields:
        if field.is_software_readable() or field.is_software_writable():
          field.sw_struct_padding = field.offset - previous_offset
          previous_offset = field.offset + field.width
      register.sw_struct_fields_padding = 32 - previous_offset
