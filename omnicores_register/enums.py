# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     OmniCores-Registers                                          ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Enumerated values for the API.                               ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



from enum import Enum, Flag, auto



# Sentinel for unspecified settings
UNSPECIFIED = object()



class SoftwareAccessType(Enum):
  """Software access."""
  NONE            = auto()
  READ_ONLY       = auto()
  WRITE_ONLY      = auto()
  WRITE_ONCE      = auto()
  READ_WRITE      = auto()
  READ_WRITE_ONCE = auto()
  def __repr__(self):
    return self.name.replace('_', '-').title()



class HardwareAccessType(Enum):
  """Hardware access."""
  NONE       = auto()
  READ_ONLY  = auto()
  WRITE_ONLY = auto()
  READ_WRITE = auto()
  def __repr__(self):
    return self.name.replace('_', '-').title()



class HardwareWriteOptions(Flag):
  """Hardware write interface options. Multiple flags can be combined."""
  ENABLE      = auto()  # Normal write with data and write enable port
  CONTINUOUS  = auto()  # Continuous write without enable, sample every cycle
  SET_MASK    = auto()  # Mask with individual set-to-1 signal per-bit
  SET_ALL     = auto()  # Single signal to set whole register or field to 1s
  CLEAR_MASK  = auto()  # Mask with individual clear-to-0 signal per-bit
  CLEAR_ALL   = auto()  # Single signal to clear whole register or field to 0s
  RESET       = auto()  # Reset the register of field to its reset value
  INCREMENT   = auto()  # Increment register of field by one
  DECREMENT   = auto()  # Decrement register of field by one
  def __repr__(self):
    names = [flag.name for flag in type(self) if flag in self and flag.value]
    return ", ".join(name.replace('_', '-').title() for name in names) if names else "None"



class HardwareReadOptions(Flag):
  """Hardware read interface options. Multiple flags can be combined."""
  DATA   = auto()  # Normal data output port
  ANDED  = auto()  # AND-reduction output
  ORED   = auto()  # OR-reduction output
  XORED  = auto()  # XOR-reduction output
  def __repr__(self):
    names = [flag.name for flag in type(self) if flag in self and flag.value]
    return ", ".join(name.replace('_', '-').title() for name in names) if names else "None"



class SoftwareWriteBehavior(Enum):
  """Behavior governing how software write data affects the storage value."""
  NORMAL             = auto()  # Write data directly stored
  WRITE_ONE_SETS     = auto()  # Writing mask of 1s sets the corresponding bits
  WRITE_ONE_CLEARS   = auto()  # Writing mask of 1s clears the corresponding bits
  WRITE_ONE_TOGGLES  = auto()  # Writing mask of 1s toggles the corresponding bits
  WRITE_ZERO_SETS    = auto()  # Writing mask of 0s sets the corresponding bits
  WRITE_ZERO_CLEARS  = auto()  # Writing mask of 0s clears the corresponding bits
  WRITE_ZERO_TOGGLES = auto()  # Writing mask of 0s toggles the corresponding bits
  def __repr__(self):
    return self.name.replace('_', '-').title()



class SoftwareReadBehavior(Enum):
  """Behavior governing side-effects after a software read operation."""
  NORMAL      = auto()  # No side-effect (default)
  READ_CLEARS = auto()  # Reading the register or field clears it
  READ_SETS   = auto()  # Reading the register or field sets it
  READ_RESETS = auto()  # Reading the register or field resets it
  def __repr__(self):
    return self.name.replace('_', '-').title()



# Defaults
register_default_software_access = SoftwareAccessType.READ_WRITE
register_default_hardware_access = HardwareAccessType.READ_ONLY
field_default_software_access    = SoftwareAccessType.READ_WRITE
field_default_hardware_access    = HardwareAccessType.READ_ONLY

register_default_hw_write_options  = HardwareWriteOptions.ENABLE
register_default_hw_read_options   = HardwareReadOptions.DATA
register_default_sw_write_behavior = SoftwareWriteBehavior.NORMAL
register_default_sw_read_behavior  = SoftwareReadBehavior.NORMAL

field_default_hw_write_options  = HardwareWriteOptions.ENABLE
field_default_hw_read_options   = HardwareReadOptions.DATA
field_default_sw_write_behavior = SoftwareWriteBehavior.NORMAL
field_default_sw_read_behavior  = SoftwareReadBehavior.NORMAL



class PackingPolicy(Enum):
  """Controls register file address resolution and padding."""
  DENSE        = auto()
  POWER_OF_TWO = auto()
  def __repr__(self):
    return self.name.replace('_', '-').title()
