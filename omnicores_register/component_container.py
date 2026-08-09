# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     OmniCores-Registers                                          ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Component container base class. It is the parent of both     ║
# ║              RegisterBank and RegisterFile, providing the shared list of  ║
# ║              components that preserves user insertion order.              ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



from omnicores_register.register import Register
from omnicores_register.enums import PackingPolicy, UNSPECIFIED



class ComponentContainer:
  """Base class for register bank and register files which can both contain registers and sub-files."""

  def __init__(self, name:str, packing:PackingPolicy=UNSPECIFIED):
    self.name = name
    # Shared list before elaboration to preserve insertion order of registers and files
    self.components = []
    # Packing policy for this container and its children
    self.packing = packing

  def add_file(self, file):
    """Add a register file to this container."""
    self.components.append(file)

  def add_register(self, register):
    """Add a register to this container."""
    self.components.append(register)

  def get_files_deep(self):
    """Collect all RegisterFile objects from the container hierarchy in depth-first insertion order."""
    from omnicores_register.register_file import RegisterFile
    collected_files = []
    for component in self.components:
      if isinstance(component, RegisterFile):
        collected_files.append(component)
        collected_files.extend(component.get_files_deep())
    return collected_files

  def get_registers_deep(self):
    """Collect all Register objects from the container hierarchy in depth-first insertion order."""
    from omnicores_register.register_file import RegisterFile
    collected_registers = []
    for component in self.components:
      if isinstance(component, Register):
        collected_registers.append(component)
      elif isinstance(component, RegisterFile):
        collected_registers.extend(component.get_registers_deep())
    return collected_registers

  def get_files_postorder(self):
    """Collect all RegisterFile objects in bottom-up order (deepest files first)."""
    from omnicores_register.register_file import RegisterFile
    collected_files = []
    for component in self.components:
      if isinstance(component, RegisterFile):
        collected_files.extend(component.get_files_postorder())
        collected_files.append(component)
    return collected_files

  def get_components_deep(self):
    """Collect all registers and files in depth-first insertion order."""
    from omnicores_register.register_file import RegisterFile
    collected_components = []
    for component in self.components:
      collected_components.append(component)
      if isinstance(component, RegisterFile):
        collected_components.extend(component.get_components_deep())
    return collected_components
