# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     OmniCores-Registers                                          ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Utility functions.                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



import sys



def next_power_of_two(value):
  """Return the smallest power of two greater than or equal to value."""
  if value <= 1:
    return 1
  pow2 = 1
  while pow2 < value:
    pow2 <<= 1
  return pow2



# ANSI escape codes
ansi_codes = {
  'reset':      '\u001b[0m',
  'bold':       '\u001b[1m',
  'faint':      '\u001b[2m',
  'italic':     '\u001b[3m',
  'underline':  '\u001b[4m',
  'slowblink':  '\u001b[5m',
  'fastblink':  '\u001b[6m',
  'reversed':   '\u001b[7m',
  'concealed':  '\u001b[8m',
  'crossedout': '\u001b[9m',
  'black':      '\u001b[30m',
  'red':        '\u001b[31m',
  'green':      '\u001b[32m',
  'yellow':     '\u001b[33m',
  'blue':       '\u001b[34m',
  'magenta':    '\u001b[35m',
  'cyan':       '\u001b[36m',
  'white':      '\u001b[37m'
}



def throw_warning(text):
  print(ansi_codes['yellow']+ansi_codes['bold'], end='')
  print(f"WARNING:", text, end='')
  print(ansi_codes['reset'])

def throw_error(text):
  print(ansi_codes['red']+ansi_codes['bold'], end='', file=sys.stderr)
  print(f"ERROR:", text, file=sys.stderr, end='')
  print(ansi_codes['reset'], file=sys.stderr)
