# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     OmniCores-Registers                                          ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Tree traversal functions for collecting registers, files,    ║
# ║              and arrays from the component hierarchy. Separated from      ║
# ║              ComponentContainer to break circular import dependencies.    ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



from omnicores_register.register import Register
from omnicores_register.register_file import RegisterFile
from omnicores_register.component_array import ComponentArray



def collect_files_deep(container):
  """Collect all RegisterFile objects from the hierarchy in DFS insertion order."""
  collected = []
  for component in container.components:
    if isinstance(component, ComponentArray):
      collected.extend(component.get_files_deep())
    elif isinstance(component, RegisterFile):
      collected.append(component)
      collected.extend(collect_files_deep(component))
  return collected



def collect_registers_deep(container):
  """Collect all Register objects from the hierarchy in DFS insertion order."""
  collected = []
  for component in container.components:
    if isinstance(component, ComponentArray):
      collected.extend(component.get_registers_deep())
    elif isinstance(component, Register):
      collected.append(component)
    elif isinstance(component, RegisterFile):
      collected.extend(collect_registers_deep(component))
  return collected



def collect_files_postorder(container):
  """Collect all RegisterFile objects in bottom-up order (deepest first)."""
  collected = []
  for component in container.components:
    if isinstance(component, ComponentArray):
      collected.extend(component.get_files_postorder())
    elif isinstance(component, RegisterFile):
      collected.extend(collect_files_postorder(component))
      collected.append(component)
  return collected



def collect_components_deep(container):
  """Collect all registers and files in DFS insertion order."""
  collected = []
  for component in container.components:
    if isinstance(component, ComponentArray):
      collected.extend(component.get_components_deep())
    else:
      collected.append(component)
      if isinstance(component, RegisterFile):
        collected.extend(collect_components_deep(component))
  return collected



def collect_array_prototype_registers(container):
  """Collect unique register prototypes from array wrappers in the hierarchy."""
  collected = []
  for component in container.components:
    if isinstance(component, ComponentArray):
      if isinstance(component.prototype, Register):
        collected.append(component.prototype)
      elif isinstance(component.prototype, RegisterFile):
        collected.extend(collect_array_prototype_registers(component.prototype))
    elif isinstance(component, RegisterFile):
      collected.extend(collect_array_prototype_registers(component))
  return collected



def collect_array_prototype_files(container):
  """Collect unique register file prototypes from array wrappers in the hierarchy."""
  collected = []
  for component in container.components:
    if isinstance(component, ComponentArray):
      if isinstance(component.prototype, RegisterFile):
        collected.append(component.prototype)
        collected.extend(collect_array_prototype_files(component.prototype))
    elif isinstance(component, RegisterFile):
      collected.extend(collect_array_prototype_files(component))
  return collected



def collect_arrays_deep(container):
  """Collect all ComponentArray wrappers from the hierarchy in DFS order."""
  collected = []
  for component in container.components:
    if isinstance(component, ComponentArray):
      collected.append(component)
      if isinstance(component.prototype, RegisterFile):
        collected.extend(collect_arrays_deep(component.prototype))
    elif isinstance(component, RegisterFile):
      collected.extend(collect_arrays_deep(component))
  return collected



def collect_register_macros_ordered(container):
  """Return ordered list of (kind, data) tuples for macro emission with array metadata interleaved."""
  items = []
  for component in container.components:
    if isinstance(component, ComponentArray):
      items.append(('array_meta', component))
      if isinstance(component.prototype, Register):
        for clone in component.get_expanded_registers():
          items.append(('register', clone))
      elif isinstance(component.prototype, RegisterFile):
        for clone in component.get_expanded_files():
          items.extend(collect_register_macros_ordered(clone))
    elif isinstance(component, Register):
      items.append(('register', component))
    elif isinstance(component, RegisterFile):
      items.extend(collect_register_macros_ordered(component))
  return items
