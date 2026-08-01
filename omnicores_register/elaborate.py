# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     OmniCores-Registers                                          ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Elaboration method of the register bank. It checks and       ║
# ║              computes attributes of the data structure before generation. ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



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

  # Padding before each register for firmware struct header
  previous_address = -4
  for register in self.registers:
    if register.is_software_readable() or register.is_software_writable():
      register.sw_struct_padding = (register.address - previous_address - 4) // 4
      previous_address = register.address
