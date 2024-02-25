# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     AnyV-Registers - Hardware register bank generator            ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ║ File:        anyv_registers.py                                            ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Template-based hardware register bank generator.             ║
# ║              For information about the usage of this tool, please refer   ║
# ║              to the README or run "anyv_register --help".                 ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



import os
import argparse
import xmltodict

from jinja2 import Environment, FileSystemLoader, StrictUndefined
import jinja2.exceptions as jinja2_exceptions

from j2gpp.filters import extra_filters as j2gpp_extra_filters
from j2gpp.tests import extra_tests as j2gpp_extra_tests
from j2gpp.utils import *

from anyv_registers.filters import extra_filters
from anyv_registers import templates
import importlib.resources

import pprint

def main():

  anyv_register_version = "0.1.0"

  # Default parameters
  default_registerWidth = 32

  # Print license
  def print_license():
    print("""AnyV-Registers is under MIT License

Copyright (c) 2024 Louis Duret-Robert

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.""")

  # Postprocessor for XML parser
  def xml_postprocessor(path, key, value):
    # Remove XML namespace
    key = key.removeprefix("ipxact:")
    # Convert attribute to child
    key = key.lstrip("@")
    # Prepare bool for auto-cast
    if value == "true":  value = "True"
    if value == "false": value = "False"
    # Prepare IPXACT hexadecimal values
    if isinstance(value,str) and value.startswith("'h"):
      value = f"0x{value[2:]}"
    # Auto-cast value
    value = auto_cast_str(value)
    return key, value

  # Load variables from XML file
  def load_xml(xml_file_path):
    component_descriptor = {}
    with open(xml_file_path) as var_file:
      try:
        component_descriptor = xmltodict.parse(var_file.read(), postprocessor=xml_postprocessor)
      except Exception as exc:
        throw_error(f"Exception occurred while loading '{xml_file_path}' : \n  {type(exc).__name__}\n{intend_text(exc)}")
    return component_descriptor

  # Postprocess the IPXACT register bank descriptor to facilitate its use in the templates
  def postprocess_ipxact(descriptor):

    # Fold the memoryMap list
    memoryMaps = []
    if isinstance(descriptor['component']['memoryMaps'], dict):
      memoryMaps = [descriptor['component']['memoryMaps']['memoryMap']]
    elif isinstance(descriptor['component']['memoryMaps'], list):
      memoryMaps = descriptor['component']['memoryMaps']
    else: raise Exception()
    descriptor['component']['memoryMaps'] = memoryMaps

    for memoryMap in descriptor['component']['memoryMaps']:

      # Fold the addressBlock list
      addressBlocks = []
      if isinstance(memoryMap['addressBlock'], dict):
        addressBlocks = [memoryMap['addressBlock']]
      elif isinstance(memoryMap['addressBlock'], list):
        addressBlocks = memoryMap['addressBlock']
      else: raise Exception()
      memoryMap['addressBlocks'] = addressBlocks
      del memoryMap['addressBlock']

      for addressBlock in memoryMap['addressBlocks']:

        # Fold the accessPolicy list
        accessPolicies = []
        if isinstance(addressBlock['accessPolicies'], dict):
          accessPolicies = [addressBlock['accessPolicies']['accessPolicy']]
        elif isinstance(addressBlock['accessPolicies'], list):
          accessPolicies = addressBlock['accessPolicies']
        else: raise Exception()
        addressBlock['accessPolicies'] = accessPolicies

        # Fold the register list
        registers = []
        if isinstance(addressBlock['register'], dict):
          registers = [addressBlock['register']]
        elif isinstance(addressBlock['register'], list):
          registers = addressBlock['register']
        else: raise Exception()
        addressBlock['registers'] = registers
        del addressBlock['register']

        for register in addressBlock['registers']:

          # Fold the field list
          if 'field' in register:
            fields = []
            if isinstance(register['field'], dict):
              fields = [register['field']]
            elif isinstance(register['field'], list):
              fields = register['field']
            else: raise Exception()
            register['fields'] = fields
            del register['field']

            for field in register['fields']:

              # Fold the reset list
              if 'resets' in field:
                resets = []
                if isinstance(field['resets'], dict):
                  resets = [field['resets']['reset']]
                elif isinstance(field['resets'], list):
                  resets = field['resets']
                else: raise Exception()
                field['resets'] = resets

              # Fold the fieldAccessPolicy list
              if 'fieldAccessPolicies' in field:
                fieldAccessPolicies = []
                if isinstance(field['fieldAccessPolicies'], dict):
                  fieldAccessPolicies = [field['fieldAccessPolicies']['fieldAccessPolicy']]
                elif isinstance(field['fieldAccessPolicies'], list):
                  fieldAccessPolicies = field['fieldAccessPolicies']
                else: raise Exception()
                field['fieldAccessPolicies'] = fieldAccessPolicies

              # Fold the enumeratedValue list
              if 'enumeratedValues' in field:
                enumeratedValues = []
                if isinstance(field['enumeratedValues'], dict):
                  enumeratedValues = [field['enumeratedValues']['enumeratedValue']]
                elif isinstance(field['enumeratedValues'], list):
                  enumeratedValues = field['enumeratedValues']
                else: raise Exception()
                field['enumeratedValues'] = enumeratedValues

    # Defaut register width in bits
    default_registerWidth = 32

    # Compute the offsets
    for memoryMap in descriptor['component']['memoryMaps']:
      memoryMap_baseAddress             = memoryMap['baseAddress'] if 'baseAddress' in memoryMap else 0x0
      addressBlock_baseAddress          = memoryMap_baseAddress
      register_address                  = addressBlock_baseAddress
      previous_addressBlock_baseAddress = addressBlock_baseAddress
      previous_addressBlock_range       = None

      memoryMap_registerWidth = memoryMap['width'] if 'width' in memoryMap else default_registerWidth

      if 'addressBlocks' in memoryMap:
        for addressBlock in memoryMap['addressBlocks']:

          block_registerWidth = addressBlock['width'] if 'width' in addressBlock else memoryMap_registerWidth

          # Address block base address
          if 'baseAddress' in addressBlock:
            # Explicitely base address
            addressBlock_baseAddress = memoryMap_baseAddress + addressBlock['baseAddress']
          elif 'baseAddressAlign' in addressBlock:
            # Align to boundary
            addressBlock_baseAddress = (addressBlock_baseAddress // addressBlock['baseAddressAlign'] + 1) * addressBlock['baseAddressAlign']
          elif previous_addressBlock_range != None:
            # Align to previous block range
            addressBlock_baseAddress = previous_addressBlock_baseAddress + previous_addressBlock_range
          elif addressBlock_baseAddress != memoryMap_baseAddress:
            # Fallback to last register offset
            addressBlock_baseAddress = register_address + block_registerWidth / 8
          addressBlock['baseAddress'] = addressBlock_baseAddress
          previous_addressBlock_baseAddress = addressBlock['baseAddress']
          previous_addressBlock_range       = addressBlock['range'] if 'range' in addressBlock else None

          if 'registers' in addressBlock:
            for register in addressBlock['registers']:
              # Register address
              if 'addressOffset' in register:
                # Explicit offset
                register_address = addressBlock_baseAddress + register['addressOffset']
              elif 'addressAlign' in register:
                # Align to boundary
                register_address = (register_address // register['addressAlign'] + 1) * register['addressAlign']
              elif register_address != addressBlock_baseAddress:
                # Successive to last register
                register_address = register_address + block_registerWidth / 8
              register['address'] = register_address

              # Field bit offset
              if 'fields' in register:
                field_bitOffset = 0x0
                previous_field_bitWidth = None
                for field in register['fields']:
                  if 'bitOffset' in field:
                    # Explicit offset
                    field_bitOffset = field['bitOffset']
                  elif 'bitAlign' in field:
                    # Align to boundary
                    field_bitOffset = (field_bitOffset // field['bitAlign'] + 1) * field['bitAlign']
                  elif field_bitOffset != 0x0:
                    # Successive to last field
                    field_bitOffset = field_bitOffset + previous_field_bitWidth
                  field['bitOffset'] = field_bitOffset
                  previous_field_bitWidth = field['bitWidth']

    return descriptor

  # Command line arguments
  argparser = argparse.ArgumentParser()
  argparser.add_argument("descriptor",                help="Register map descriptor",        nargs=1)
  argparser.add_argument("--output",  dest="output",  help="Output directory path",                               default="./" )
  argparser.add_argument("--version", dest="version", help="Print J2GPP version and quits",  action="store_true", default=False)
  argparser.add_argument("--license", dest="license", help="Print J2GPP license and quits",  action="store_true", default=False)
  args, args_unknown = argparser.parse_known_args()

  if args.version:
    print(anyv_register_version)
    exit()

  if args.license:
    print_license()
    exit()

  # Load the register bank descriptor
  component_descriptor = load_xml(args.descriptor[0])
  component_name = component_descriptor['component']['name']
  pprint.pprint(component_descriptor)
  component_descriptor = postprocess_ipxact(component_descriptor)
  pprint.pprint(component_descriptor)

  # Overload the join_path function such that the include statements are relative to the template
  class RelativeIncludeEnvironment(Environment):
    def join_path(self, template, parent):
      return os.path.join(os.path.dirname(parent), template)

  # Jinja2 environment
  env = RelativeIncludeEnvironment(
    loader=FileSystemLoader("./")
  )
  env.undefined = StrictUndefined
  env.add_extension('jinja2.ext.do')
  env.add_extension('jinja2.ext.debug')
  env.filters.update(extra_filters)
  env.filters.update(j2gpp_extra_filters)
  env.tests.update(j2gpp_extra_tests)

  # Create directories for output path
  output_directory = os.path.join(args.output, component_name)
  try:
    os.makedirs(output_directory, exist_ok=True)
  except OSError as exc:
      throw_error(f"Cannot create directory '{output_directory}'.")

  # Fetch templates from library archive
  templates_directory = importlib.resources.files(templates)

  # Render templates
  for template_file in templates_directory.iterdir():
    template_path = os.path.basename(template_file.__str__())
    if '.j2' in template_path:
      print(f"Rendering template '{template_path}'.")

      # Output file is the name of the component with the extension of the template
      extension   = template_path.split('.')[1].removesuffix('.j2')
      print(f"component_name = {component_name}")
      print(f"extension = {extension}")
      output_path = os.path.join(output_directory, f"{component_name}.{extension}")
      output_str  = ""

      # Render template to string
      try:
        output_str = env.from_string(template_file.read_text()).render(component_descriptor)
      except jinja2_exceptions.UndefinedError as exc:
        # Undefined object encountered during rendering
        traceback = jinja2_render_traceback(template_path)
        throw_error(f"Undefined object encountered while rendering '{template_path}' :\n{traceback}\n      {exc.message}")
      except jinja2_exceptions.TemplateSyntaxError as exc:
        # Syntax error encountered during rendering
        traceback = jinja2_render_traceback(template_path)
        throw_error(f"Syntax error encountered while rendering '{template_path}' :\n{traceback}\n      {exc.message}")
      except jinja2_exceptions.TemplateNotFound as exc:
        # Template not found
        traceback = jinja2_render_traceback(template_path)
        throw_error(f"Included template '{exc}' not found :\n{traceback}")
      except OSError as exc:
        # Catch file read exceptions
        if exc.errno == errno.ENOENT:
          throw_error(f"Cannot read '{template_path}' : file doesn't exist.")
        elif exc.errno == errno.EACCES:
          throw_error(f"Cannot read '{template_path}' : missing read permission.")
        else:
          throw_error(f"Cannot read '{template_path}'.")
      except Exception as exc:
        # Catch all other Python exceptions (in filter for example)
        traceback = jinja2_render_traceback(template_path, including_non_template=True)
        throw_error(f"Exception occurred while rendering '{template_path}' :\n{traceback}\n      {type(exc).__name__} - {exc}")

      # Write the rendered file
      try:
        with open(output_path,'w') as output_file:
          output_file.write(output_str)
      except OSError as exc:
        # Catch file write exceptions
        if exc.errno == errno.EISDIR:
          throw_error(f"Cannot write '{output_path}' : path is a directory.")
        elif exc.errno == errno.EACCES:
          throw_error(f"Cannot write '{output_path}' : missing write permission.")
        else:
          throw_error(f"Cannot write '{output_path}'.")
