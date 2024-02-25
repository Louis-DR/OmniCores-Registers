# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     AnyV-Registers - Hardware register bank generator            ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ║ File:        filters.py                                                   ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Additional Jinja2 filters.                                   ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



extra_filters = {}

def hexadecimal(value):
  return f"{value:X}"
extra_filters['hexadecimal'] = hexadecimal

def arrsize(size):
  """
  Generates the `[size-1:0]` signal array size definition if `size>1`,
  else it returns an empty string.
  """
  if size == 1:
    return ""
  else:
    return f"[{size-1}:0]"
extra_filters['arrsize'] = arrsize
