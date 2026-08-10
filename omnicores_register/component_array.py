# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     OmniCores-Registers                                          ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Component array wrapper. Wraps a single register or register  ║
# ║              file prototype and expands it into N instances with computed  ║
# ║              addresses during elaboration.                                 ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



import copy
from omnicores_register.register import Register
from omnicores_register.register_file import RegisterFile



class ComponentArray:
  """Wraps a prototype component and expands it into an array of N instances."""

  def __init__(self, prototype, length:int, stride:int=None):
    self.prototype = prototype
    self.length     = length
    self._stride   = stride

    # Absolute byte address of the first element (set during elaboration)
    self.address = None

    # Firmware struct padding before the array
    self.sw_struct_padding = 0

    # Cached expanded clones (populated on first access after elaboration)
    self._expanded_registers = None
    self._expanded_files     = None

    # Whether this array uses a C struct wrapper (stride > element_size)
    self._needs_wrapper = None
    self._wrapper_pad_words = 0

  # Proxy attributes that elaboration reads from the component
  @property
  def offset(self):
    return self.prototype.offset

  @offset.setter
  def offset(self, value):
    self.prototype.offset = value

  @property
  def align(self):
    return self.prototype.align

  @align.setter
  def align(self, value):
    self.prototype.align = value

  def _is_register_array(self):
    return isinstance(self.prototype, Register)

  def _is_file_array(self):
    return isinstance(self.prototype, RegisterFile)

  @property
  def element_size(self):
    if self._is_register_array():
      return 4
    else:
      return self.prototype.size

  @property
  def stride(self):
    if self._stride is not None:
      return self._stride
    return self.element_size

  @property
  def region_size(self):
    return (self.length - 1) * self.stride + self.element_size

  @property
  def needs_wrapper(self):
    if self._needs_wrapper is None:
      self._needs_wrapper = self.stride > self.element_size
    return self._needs_wrapper

  @property
  def wrapper_pad_words(self):
    if self._wrapper_pad_words is None:
      self._wrapper_pad_words = (self.stride - self.element_size) // 4
    return self._wrapper_pad_words

  def _shift_subtree_addresses(self, component, delta):
    """Recursively add delta to every component's address in the subtree."""
    component.address += delta
    if isinstance(component, RegisterFile):
      for child in component.components:
        self._shift_subtree_addresses(child, delta)

  def _fixup_descendant_hierarchical_names(self, component, old_prefix, new_prefix):
    """Recursively replace the prototype name prefix with the clone name prefix in all descendants."""
    if isinstance(component, RegisterFile):
      for child in component.components:
        if child.hierarchical_name:
          child.hierarchical_name = child.hierarchical_name.replace(old_prefix, new_prefix, 1)
        self._fixup_descendant_hierarchical_names(child, old_prefix, new_prefix)

  def _create_and_get_expanded(self):
    """Create N clones of the prototype with computed addresses and hierarchical names."""
    if self._expanded_registers is not None:
      return self._expanded_registers, self._expanded_files

    expanded_registers = []
    expanded_files     = []

    for index in range(self.length):
      clone = copy.deepcopy(self.prototype)

      element_address = self.address + index * self.stride

      # Apply the array element address to the clone and shift its subtree
      offset_from_prototype = element_address - self.prototype.address
      self._shift_subtree_addresses(clone, offset_from_prototype)

      # The hierarchical name suffix uses underscore for array index
      if index == 0:
        index_suffix = "_0"
      else:
        index_suffix = f"_{index}"

      if isinstance(clone, Register):
        clone.is_array_element = True
        clone.array_index = index
        clone.hierarchical_name = self.prototype.hierarchical_name + index_suffix
        expanded_registers.append(clone)
      else:
        clone.is_array_element = True
        clone.array_index = index
        old_prefix = self.prototype.hierarchical_name
        clone.hierarchical_name = self.prototype.hierarchical_name + index_suffix
        self._fixup_descendant_hierarchical_names(clone, old_prefix, clone.hierarchical_name)
        expanded_files.append(clone)

    self._expanded_registers = expanded_registers
    self._expanded_files     = expanded_files
    return expanded_registers, expanded_files

  def get_expanded_registers(self):
    registered_list, _ = self._create_and_get_expanded()
    for register in registered_list:
      yield register

  def get_expanded_files(self):
    _, files_list = self._create_and_get_expanded()
    for file in files_list:
      yield file

  def get_files_deep(self):
    _, files_list = self._create_and_get_expanded()
    collected = []
    for file in files_list:
      collected.append(file)
      collected.extend(file.get_files_deep())
    return collected

  def get_registers_deep(self):
    registers_list, files_list = self._create_and_get_expanded()
    collected = []
    for register in registers_list:
      collected.append(register)
    for file in files_list:
      collected.extend(file.get_registers_deep())
    return collected

  def get_files_postorder(self):
    _, files_list = self._create_and_get_expanded()
    collected = []
    for file in files_list:
      collected.extend(file.get_files_postorder())
      collected.append(file)
    return collected

  def get_components_deep(self):
    registers_list, files_list = self._create_and_get_expanded()
    collected = []
    for component in registers_list:
      collected.append(component)
    for component in files_list:
      collected.append(component)
      collected.extend(component.get_components_deep())
    return collected
