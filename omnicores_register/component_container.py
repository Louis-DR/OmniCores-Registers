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



from omnicores_register.enums import PackingPolicy, UNSPECIFIED



class ComponentContainer:
  """Base class for register bank and register files which can both contain registers and sub-files."""

  def __init__(self, name:str, packing:PackingPolicy=UNSPECIFIED):
    self.name = name
    # Shared list before elaboration to preserve insertion order of registers and files
    self.components = []
    # Packing policy for this container and its children
    self.packing = packing

  def add(self, component):
    """Add a Register, RegisterFile, or ComponentArray to this container."""
    self.components.append(component)

  # Tree traversal methods delegate to the standalone traversal module.
  # Local imports break the circular dependency: traversal imports RegisterFile
  # which imports ComponentContainer, which would otherwise form a cycle.

  def get_files_deep(self):
    from omnicores_register.traversal import collect_files_deep
    return collect_files_deep(self)

  def get_registers_deep(self):
    from omnicores_register.traversal import collect_registers_deep
    return collect_registers_deep(self)

  def get_files_postorder(self):
    from omnicores_register.traversal import collect_files_postorder
    return collect_files_postorder(self)

  def get_components_deep(self):
    from omnicores_register.traversal import collect_components_deep
    return collect_components_deep(self)

  def get_array_prototype_registers(self):
    from omnicores_register.traversal import collect_array_prototype_registers
    return collect_array_prototype_registers(self)

  def get_array_prototype_files(self):
    from omnicores_register.traversal import collect_array_prototype_files
    return collect_array_prototype_files(self)

  def get_arrays_deep(self):
    from omnicores_register.traversal import collect_arrays_deep
    return collect_arrays_deep(self)

  def get_register_macros_ordered(self):
    from omnicores_register.traversal import collect_register_macros_ordered
    return collect_register_macros_ordered(self)
