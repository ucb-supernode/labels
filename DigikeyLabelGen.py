import argparse
import ast
import csv
from collections import namedtuple
import re

from annotators import *

# Simple annotator that adds a column whose value is the name of the specified
# parametrics field.
def DigikeyFieldAnnotator(out_name, field_name):
  def annotate_fn(row_dict):
    parametrics_str = row_dict['parametrics']
    if not parametrics_str:
      return {}
    paramterics = ast.literal_eval(parametrics_str)
    return {out_name: paramterics[field_name]}
  return AnnotateFn([out_name], annotate_fn)

ParametricPreprocess = namedtuple('ParametricPreprocess', ['name', 'fn'])

"""
Return a function which takes a string (formatted as a list of sub-strings, with
the specified separator), and returns the truncated version, optionally with an
end part to indicate truncation.
"""
def list_truncate(num_elements, end="...", separator=', '):
  def fn(in_string):
    substrings = in_string.split(separator)
    if len(substrings) > num_elements:
      substrings = substrings[:num_elements]
      if end:
        substrings.append(end)
    return separator.join(substrings)
  return fn


"""
Returns a function that takes a string, looks up that string in a dict, and
returns the found value (or the input value, if no match and default is True).
Throws an exception if no match is found and default is False.
"""
def remap(remap_dict, default=True):
  def fn(in_string):
    if in_string in remap_dict:
      return remap_dict[in_string]
    else:
      if default:
        return in_string
      else:
        raise Exception("Failed to remap '%s' with dict %s" % (in_string, remap_dict))
  return fn

"""
Returns a function that takes a string and tries to match it against the
specified regexes (in sequence). If a match is found, the capture groups are
interpolated into the output string associated with the regex.
If no match is found, returns the input (if default is True) or throws an
exception (if default is False).
"""
def regex_capture_map(regex_output_pair_list, default=True):
  regex_output_pair_compiled_list = [(re.compile('^' + regex + '$'), output) for (regex, output) in regex_output_pair_list]
  def fn(in_string):
    for regex, output in regex_output_pair_compiled_list:
      match = regex.match(in_string)
      if match:
        return output % match.groups()
    if default:
      return in_string
    else:
      raise Exception("Failed to remap '%s' with regex list %s" % (in_string, regex_output_pair_list))
  return fn

QuickDescStruct = namedtuple('QuickDescStruct', ['preprocessors', 'title', 'quickdesc'])
quickdesc_rules = {
"Ceramic Capacitors":
    QuickDescStruct([],
                    "Capacitor, Ceramic, %(Capacitance)s",
                    "%(Voltage - Rated)s, %(Temperature Coefficient)s, %(Tolerance)s"
                   ),
"Aluminum Capacitors":
    QuickDescStruct([],
                    "Capacitor, Aluminum, %(Capacitance)s",
                    "%(Voltage Rating)s, %(Tolerance)s"
                   ),

### Electromechanical
"Slide Switches":
    QuickDescStruct([],
                    "Slide switch",
                    "%(Current Rating)s, %(Voltage Rating - DC)s"
                   ),
"Tactile Switches":
    QuickDescStruct([],
                    "Tactile switch",
                    "%(Operating Force)s"
                   ),

### Discrete Semiconductors
"Diodes - Rectifiers - Single":
    QuickDescStruct([ParametricPreprocess("Voltage - Forward (Vf) (Max) @ If",
                                          regex_capture_map([("(\d+.?\d*\w*V)\s*@.*", "%s"),
                                                            ], default=False)),
                    ],
                    "Diode, %(Voltage - DC Reverse (Vr) (Max))s %(Current - Average Rectified (Io))s",
                    "%(Diode Type)s, %(Voltage - Forward (Vf) (Max) @ If)s(f)"
                   ),
"Diodes - Zener - Single":
    QuickDescStruct([ParametricPreprocess("Voltage - Forward (Vf) (Max) @ If",
                                          regex_capture_map([("(\d+.?\d*\w*V)\s*@.*", "%s"),
                                                            ], default=False)),
                    ],
                    "Zener, %(Voltage - Zener (Nom) (Vz))s",
                    "%(Voltage - Forward (Vf) (Max) @ If)s(f)"
                   ),
"TVS - Diodes":
    QuickDescStruct([],
                    "TVS Diode, %(Voltage - Reverse Standoff (Typ))s",
                    "%(Applications)s"
                   ),

"Transistors - Bipolar (BJT) - Single":
    QuickDescStruct([],
                    "%(Transistor Type)s BJT",
                    "%(Voltage - Collector Emitter Breakdown (Max))s, %(Current - Collector (Ic) (Max))s",
                   ),
"Transistors - Bipolar (BJT) - Arrays":
    QuickDescStruct([],
                    "BJT Array",
                    "%(Voltage - Collector Emitter Breakdown (Max))s, %(Current - Collector (Ic) (Max))s",
                   ),
"Transistors - FETs, MOSFETs - Single":
    QuickDescStruct([ParametricPreprocess("FET Type", list_truncate(1, '')),  # take first element of list
                     ParametricPreprocess("FET Type",
                                          remap({'MOSFET N-Channel': 'N-MOSFET',
                                                 'MOSFET P-Channel': 'P-MOSFET',
                                                }, False)),
                    ],
                    "%(FET Type)s",
                    u"%(Drain to Source Voltage (Vdss))s, %(Current - Continuous Drain (Id) @ 25\u00B0C)s",
                   ),

### ICs, Power conversion
"PMIC - Voltage Regulators - Linear":
    QuickDescStruct([ParametricPreprocess("Voltage - Output",
                                          regex_capture_map([(".*~.*", "Adj"),
                                                             ("(\d+.?\d*\w*V)", "%s"),
                                                             (".*", ''),
                                                            ], default=False)),
                     ParametricPreprocess("Voltage - Dropout (Typical)",
                                          regex_capture_map([("(\d+.?\d*\w*V)\s*@.*", "%s"),
                                                             ("\?", "?"),
                                                            ], default=False)),
                    ],
                    "IC, LDO %(Voltage - Output)s",
                    "%(Current - Output)s, %(Voltage - Dropout (Typical))s(d)"
                   ),
"PMIC - Voltage Reference":
    QuickDescStruct([],
                    "IC, Vref %(Voltage - Output (Min/Fixed))s",
                    "%(Tolerance)s"
                   ),
"PMIC - Voltage Regulators - DC DC Switching Regulators":
    QuickDescStruct([ParametricPreprocess("Topology", list_truncate(2)),
                    ],
                    "IC, DC/DC",
                    "%(Frequency - Switching)s, (%(Topology)s)"
                   ),
"PMIC - Voltage Regulators - DC DC Switching Controllers":
    QuickDescStruct([ParametricPreprocess("Topology", list_truncate(2)),
                     ],
                    "IC, DC/DC",
                    "%(Frequency - Switching)s, (%(Topology)s)"
                   ),

### ICs, Logic
"Logic - Flip Flops":
    QuickDescStruct([],
                    "IC, Flip-flop, %(Manufacturer Part Number)s",
                    ""
                   ),
"Logic - Gates and Inverters":
    QuickDescStruct([],
                    "IC, %(Logic Type)s, %(Manufacturer Part Number)s",
                    ""
                   ),
"Logic - Shift Registers":
    QuickDescStruct([],
                    "IC, Shift Register, %(Manufacturer Part Number)s",
                    ""
                   ),

### ICs, Misc
"Linear - Amplifiers - Instrumentation, OP Amps, Buffer Amps":
    QuickDescStruct([],
                    "IC, Op-amp, %(Manufacturer Part Number)s",
                    "%(-3db Bandwidth)s (-3db), %(Slew Rate)s"
                   ),
"Linear - Amplifiers - Audio":
    QuickDescStruct([],
                    "IC, Audio Op-amp, %(Manufacturer Part Number)s",
                    "%(Type)s"
                   ),
"Linear - Comparators":
    QuickDescStruct([],
                    "IC, Comparator, %(Manufacturer Part Number)s",
                    ""
                   ),
"Data Acquisition - Analog to Digital Converters (ADC)":
    QuickDescStruct([],
                    "IC, ADC, %(Manufacturer Part Number)s",
                    "%(Number of Bits)sb, %(Sampling Rate (Per Second))ssps"
                   ),
"Data Acquisition - Digital to Analog Converters (DAC)":
    QuickDescStruct([],
                    "IC, DAC, %(Manufacturer Part Number)s",
                    "%(Number of Bits)sb, %(Settling Time)s"
                   ),
"Clock/Timing - Real Time Clocks":
    QuickDescStruct([],
                    "IC, RTC, %(Manufacturer Part Number)s",
                    ""
                   ),
"Clock/Timing - Programmable Timers and Oscillators":
    QuickDescStruct([],
                    "IC, Timer, %(Manufacturer Part Number)s",
                    ""
                   ),
"PMIC - LED Drivers":
    QuickDescStruct([],
                    "IC, LED Driver, %(Manufacturer Part Number)s",
                    "%(Number of Outputs)sx, %(Current - Output / Channel)s"
                   ),
"Clock/Timing - Real Time Clocks":
    QuickDescStruct([],
                    "IC, RTC, %(Manufacturer Part Number)s",
                    ""
                   ),

### ICs, Misc, Sensors
"Magnetic Sensors - Linear, Compass (ICs)":
    QuickDescStruct([],
                    "Sensor, Magnetic, %(Manufacturer Part Number)s",
                    "%(Axis)s axis, %(Bandwidth)s"
                   ),

### Misc
"Crystals":
    QuickDescStruct([],
                    "Crystal, %(Frequency)s",
                    "%(Frequency Tolerance)s, %(Load Capacitance)s"
                   ),
"PTC Resettable Fuses":
    QuickDescStruct([],
                    "PTC Fuse, %(Current - Hold (Ih) (Max))s(h)",
                    "%(Voltage - Max)s, %(Current - Trip (It))s(t)"
                   ),
"Temperature Sensors - NTC Thermistors":
    QuickDescStruct([],
                    "Thermistor, NTC, %(Resistance in Ohms @ 25\u00b0C)s",
                    ""
                   ),
}

"""
Return a function which takes a string (formatted as a list of sub-strings, with
the specified separator). Matches the sub-strings in the list against the regex
strings in matches (in order of matches), returning the first sub-string that
matches.
Intended use case is to pick a desired sub-string element by format (ranked in
matches).
Raises an exception if no match is found. Matches can include a wildcard as a
fallback, which will just return the first sub-string.
"""
def list_regex_map(matches, separator=', ', default=True):
  match_progs = [(re.compile('^' + elt[0] + '$'), elt[1]) for elt in matches]
  def fn(in_string):
    substrings = in_string.split(separator)
    substrings = [substr.strip() for substr in substrings]
    for match_prog, output in match_progs:
      for substr in substrings:
        match = match_prog.match(substr)
        if match:
          return output % match.groups()
    if default:
      return substrings[0]
    else:
      raise Exception("Failed to match on '%s' with matchers %s" % (in_string, matches))
  return fn


package_priority_map = {
  (u'(D\u00B2?Pak)', '%s'),
  ('(TO-220).*', '%s'),
  ('(TO-92).*', '%s'),
  ('(TO-\d+).*', '%s'),
  ('(SOT-23).*', '%s'),
  ('(SOT-\d+).*', '%s'),
  ('(SOD-\d+).*', '%s'),
  ('(DO-\d+)', '%s'),
  ('(\d+-TSSOP)', '%s'),
  ('SOT-753', 'SOT-23'),
  ('(Radial)', '%s'),
}

paren_removal_regex = re.compile("\s*\([^\(^\)]+\)\s*")

def DigikeyQuickDescAnnotator():
  def annotate_fn(row_dict):
    parametrics_str = row_dict['parametrics']
    if not parametrics_str:
      return {}
    parametrics = ast.literal_eval(parametrics_str)
    family = parametrics['Family']
    assert family in quickdesc_rules, "no rule for part family '%s'" % family

    # Do global pre-process
    for k, v in parametrics.items():
      # Eliminate supplemental information in parentheses
      v = re.sub(paren_removal_regex, '', v)
      if v == '-':
        v = '?'
      parametrics[k] = v

    # Global package preference selection
    if 'Package / Case' in parametrics:
      package = list_regex_map(package_priority_map)(parametrics['Package / Case'])
      parametrics['Package / Case'] = package

    quickdesc_rule = quickdesc_rules[family]
    for processor in quickdesc_rule.preprocessors:
      assert processor.name in parametrics, "Preprocessor for family '%s' needs pamametric '%s'" % (family, processor.name)
      parametrics[processor.name] = processor.fn(parametrics[processor.name])
    title = quickdesc_rule.title % parametrics
    if 'Package / Case' in parametrics:
      package = parametrics['Package / Case']
    else:
      package = ''
    quickdesc = quickdesc_rule.quickdesc % parametrics
    return {'title': title,
            'package': package,
            'quickdesc': quickdesc}

  return AnnotateFn(['title', 'package', 'quickdesc'], annotate_fn)

"""Simple annotator generator where the output field is mapped to value.
If the value is a string, the interpolation of that string with the row
dictionary is returned.
If the value is a function, it is called given the row dictionary, and the
result is returned.
"""
def MappingAnnotator(mapping):
  def annotate_fn(row_dict):
    output = {}
    for key, value in mapping.items():
      if isinstance(value, str):
        output[key] = value % row_dict
      elif callable(value):
        output[key] = value(row_dict)
      else:
        assert False, "Unknown mapping dict value %s" % value
    return output
  return AnnotateFn(mapping.keys(), annotate_fn)

def PriorityAnnotator(*elts):
  key_set = set(elts[0].out_names)

  def annotate_fn(row_dict):
    output = {}
    for elt in elts:
      update_dict = elt.fn(row_dict)
      for key, value in update_dict.items():
        if key not in output:
          output[key] = value
      if set(output.keys()) == key_set:
        return output
    return output
  for elt in elts:
    assert set(elt.out_names) == key_set, "inconsistent annotator output keys"

  return AnnotateFn(list(key_set), annotate_fn)

def title_fn(row_dict):
  if row_dict['generic_value']:
    return '%(generic_title)s, %(generic_value)s' % row_dict
  else:
    return '%(generic_title)s' % row_dict

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="Generates label fields using Digikey parametrics")
  parser.add_argument('--input', '-i', required=True,
                      help="Input CSV file with Digikey parametrics")
  parser.add_argument('--output', '-o', required=True,
                      help="Output CSV file")
  args = parser.parse_args()

  with open(args.input, 'r', encoding='utf-8') as infile:
    input_rows = list(csv.reader(infile, delimiter=','))

  output_rows = annotate(input_rows, None, [
    PriorityAnnotator(
      DigikeyQuickDescAnnotator(),
      MappingAnnotator({
        'title': title_fn,
        'package': '%(generic_package)s',
        'quickdesc': '%(generic_quickdesc)s',
      }),
    ),
    PriorityAnnotator(
      DigikeyFieldAnnotator('mfrpn', 'Manufacturer Part Number'),
      MappingAnnotator({'mfrpn': ''}),
    )
  ])

  with open(args.output, 'w', newline='', encoding='utf-8') as outfile:
    output_writer = csv.writer(outfile, delimiter=',')
    for output_row in output_rows:
      output_row = output_row
      output_writer.writerow(output_row)
