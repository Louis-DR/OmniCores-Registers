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



from omnicores_register.component_container import ComponentContainer
from omnicores_register.elaborate import elaborate
from omnicores_register.generate import generate



class RegisterBank(ComponentContainer):
  """Core class and root of the data structure describing the generated register bank."""
  # Constructor
  def __init__(self, name:str):
    super().__init__(name)
    # Flat lists of all registers and files in the hierarchy, populated during elaboration
    self.registers = []
    self.files     = []

  # Import the methods from their dedicated files
  elaborate = elaborate
  generate  = generate
