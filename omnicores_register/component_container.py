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
    """Add a register file or file array to this container."""
    self.components.append(file)

  def add_register(self, register):
    """Add a register or register array to this container."""
    self.components.append(register)

  def get_files_deep(self):
    """Collect all RegisterFile objects from the container hierarchy in depth-first insertion order."""
    from omnicores_register.register_file import RegisterFile
    from omnicores_register.component_array import ComponentArray
    collected_files = []
    for component in self.components:
      if isinstance(component, ComponentArray):
        collected_files.extend(component.get_files_deep())
      elif isinstance(component, RegisterFile):
        collected_files.append(component)
        collected_files.extend(component.get_files_deep())
    return collected_files

  def get_registers_deep(self):
    """Collect all Register objects from the container hierarchy in depth-first insertion order."""
    from omnicores_register.register_file import RegisterFile
    from omnicores_register.component_array import ComponentArray
    collected_registers = []
    for component in self.components:
      if isinstance(component, ComponentArray):
        collected_registers.extend(component.get_registers_deep())
      elif isinstance(component, Register):
        collected_registers.append(component)
      elif isinstance(component, RegisterFile):
        collected_registers.extend(component.get_registers_deep())
    return collected_registers

  def get_files_postorder(self):
    """Collect all RegisterFile objects in bottom-up order (deepest files first)."""
    from omnicores_register.register_file import RegisterFile
    from omnicores_register.component_array import ComponentArray
    collected_files = []
    for component in self.components:
      if isinstance(component, ComponentArray):
        collected_files.extend(component.get_files_postorder())
      elif isinstance(component, RegisterFile):
        collected_files.extend(component.get_files_postorder())
        collected_files.append(component)
    return collected_files

  def get_components_deep(self):
    """Collect all registers and files in depth-first insertion order."""
    from omnicores_register.register_file import RegisterFile
    from omnicores_register.component_array import ComponentArray
    collected_components = []
    for component in self.components:
      if isinstance(component, ComponentArray):
        collected_components.extend(component.get_components_deep())
      else:
        collected_components.append(component)
        if isinstance(component, RegisterFile):
          collected_components.extend(component.get_components_deep())
    return collected_components

  def get_array_prototype_registers(self):
    """Collect unique register prototypes from array wrappers in the hierarchy."""
    from omnicores_register.register_file import RegisterFile
    from omnicores_register.component_array import ComponentArray
    prototype_registers = []
    for component in self.components:
      if isinstance(component, ComponentArray):
        if isinstance(component.prototype, Register):
          prototype_registers.append(component.prototype)
        elif isinstance(component.prototype, RegisterFile):
          prototype_registers.extend(component.prototype.get_array_prototype_registers())
      elif isinstance(component, RegisterFile):
        prototype_registers.extend(component.get_array_prototype_registers())
    return prototype_registers

  def get_array_prototype_files(self):
    """Collect unique register file prototypes from array wrappers in the hierarchy."""
    from omnicores_register.register_file import RegisterFile
    from omnicores_register.component_array import ComponentArray
    prototype_files = []
    for component in self.components:
      if isinstance(component, ComponentArray):
        if isinstance(component.prototype, RegisterFile):
          prototype_files.append(component.prototype)
          prototype_files.extend(component.prototype.get_array_prototype_files())
      elif isinstance(component, RegisterFile):
        prototype_files.extend(component.get_array_prototype_files())
    return prototype_files

  def get_arrays_deep(self):
    """Collect all ComponentArray wrappers from the hierarchy in DFS order."""
    from omnicores_register.register_file import RegisterFile
    from omnicores_register.component_array import ComponentArray
    collected_arrays = []
    for component in self.components:
      if isinstance(component, ComponentArray):
        collected_arrays.append(component)
        if isinstance(component.prototype, RegisterFile):
          collected_arrays.extend(component.prototype.get_arrays_deep())
      elif isinstance(component, RegisterFile):
        collected_arrays.extend(component.get_arrays_deep())
    return collected_arrays

  def get_register_macros_ordered(self):
    """Return ordered list of (kind, data) tuples for macro emission with array metadata interleaved."""
    from omnicores_register.register_file import RegisterFile
    from omnicores_register.component_array import ComponentArray
    items = []
    for component in self.components:
      if isinstance(component, ComponentArray):
        items.append(('array_meta', component))
        if isinstance(component.prototype, Register):
          for clone in component.get_expanded_registers():
            items.append(('register', clone))
        elif isinstance(component.prototype, RegisterFile):
          for clone in component.get_expanded_files():
            items.extend(clone.get_register_macros_ordered())
      elif isinstance(component, Register):
        items.append(('register', component))
      elif isinstance(component, RegisterFile):
        items.extend(component.get_register_macros_ordered())
    return items
