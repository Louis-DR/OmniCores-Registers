# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     AnyV-Registers - Hardware register bank generator            ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ║ File:        __init__.py                                                  ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Entry point for the setuptools command line program.         ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



from anyv_registers.anyv_registers import main

if __name__ == '__main__':
  main()
