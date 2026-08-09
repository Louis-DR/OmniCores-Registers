# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     OmniCores-Registers                                          ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Utility functions.                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



def next_power_of_two(value):
  """Return the smallest power of two greater than or equal to value."""
  if value <= 1:
    return 1
  pow2 = 1
  while pow2 < value:
    pow2 <<= 1
  return pow2
