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
  # Compute address offset of each register
  running_address = 0
  for register in self.registers:
    if register.offset is None:
      register.address = running_address
    else:
      register.address = register.offset
      running_address  = register.offset
    running_address += 4
