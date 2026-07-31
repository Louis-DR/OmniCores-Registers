# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     OmniCores-Registers                                          ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Register object class.                                       ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



class Register:
  def __init__(self, name:str, width:int=32):
    self.name    = name
    self.width   = width
    self.address = None
