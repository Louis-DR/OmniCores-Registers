# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     AnyV-Registers - Hardware register bank generator            ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ║ File:        setup.py                                                     ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Setuptools configuration to build the command line program.  ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



from setuptools import setup, find_packages

setup(name         = 'anyv_registers',
      version      = '0.1.0',
      description  = 'A template-based hardware register bank generator',
      keywords     = ['verilog', 'register', 'generator', 'fpga', 'asic', 'semiconductor', 'microelectronics', 'hardware', 'jinja2'],
      url          = 'https://github.com/Louis-DR/AnyV-Registers',
      author       = 'Louis Duret-Robert',
      author_email = 'louisduret@gmail.com',
      license      = 'MIT',
      license_file = 'LICENSE',

      long_description              = open('README.md').read(),
      long_description_content_type = 'text/markdown',

      packages     = find_packages(),
      entry_points = {
        'console_scripts': ['anyv_registers = anyv_registers:main']
      },
      install_requires = [
        'j2gpp',
        'xmltodict',
      ],

      include_package_data=True,
      package_data={
        "anyv_registers.templates": ["*"]
      },
)
