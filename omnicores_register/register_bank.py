# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     OmniCores-Registers                                          ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Register bank object class. This is the core class of the    ║
# ║              tool, the root of the register bank data structure, and the  ║
# ║              object on which elaboration and generation are run.          ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



from omnicores_register.register import Register
from omnicores_register.elaborate import elaborate
from omnicores_register.generate import generate



class RegisterBank:
  """Core class and root of the data structure describing the generated register bank."""
  # Constructor
  def __init__(self, name:str):
    self.name = name
    self.registers = []

  # Methods to add components
  def add_register(self, register:Register):
    self.registers.append(register)

  # Import the methods from their dedicated files
  elaborate = elaborate
  generate  = generate
