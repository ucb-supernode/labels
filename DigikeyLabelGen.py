import argparse
import ast
import csv
from collections import namedtuple
import re

from labelannotator import *

# Simple annotator that adds a column whose value is the name of the specified
# parametrics field.
def RemapParametric(out_name, field_name):
  def annotate_fn(row_dict):
    parametrics_str = row_dict['parametrics']
    if not parametrics_str:
      return {}
    paramterics = ast.literal_eval(parametrics_str)
    return {out_name: paramterics[field_name]}
  return annotate_fn

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
"Through Hole Resistors":
    QuickDescStruct([ParametricPreprocess("Power (Watts)",
                                          regex_capture_map([(".*(\d+/\d+W).*", "%s"),
                                                            ], default=False)),
                    ],
                    "Resistor, %(Resistance (Ohms))s\ucea9",
                    "%(Tolerance)s, %(Power (Watts))s"
                   ),
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
                                          remap({'N-Channel': 'N-MOSFET',
                                                 'P-Channel': 'P-MOSFET',
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
"Logic - Translators, Level Shifters":
    QuickDescStruct([],
                    "IC, Level Shifter, %(Manufacturer Part Number)s",
                    ""
                   ),
"Logic - Buffers, Drivers, Receivers, Transceivers":
    QuickDescStruct([],
                    "IC, Transceiver, %(Manufacturer Part Number)s",
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
"Data Acquisition - Digital Potentiometers":
    QuickDescStruct([],
                    "IC, Digipot, %(Manufacturer Part Number)s",
                    "%(Resistance (Ohms))s\ucea9, %(Number of Taps)s taps"
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
"PMIC - Current Regulation/Management":
    QuickDescStruct([],
                    "IC, %(Function)s, %(Manufacturer Part Number)s",
                    ""
                   ),
"PMIC - V/F and F/V Converters":
    QuickDescStruct([],
                    "IC, %(Type)s, %(Manufacturer Part Number)s",
                    ""
                   ),
"PMIC - LED Drivers":
    QuickDescStruct([],
                    "IC, LED Driver, %(Manufacturer Part Number)s",
                    "%(Number of Outputs)sx, %(Current - Output / Channel)s"
                   ),
"PMIC - Full, Half-Bridge Drivers":
    QuickDescStruct([],
                    "IC, %(Output Configuration)s, %(Manufacturer Part Number)s",
                    "%(Voltage - Load)s, %(Current - Output / Channel)s/channel"
                   ),
"PMIC - Gate Drivers":
    QuickDescStruct([],
                    "IC, Gate Driver, %(Manufacturer Part Number)s",
                    "%(Number of Drivers)s drivers"
                   ),
"Clock/Timing - Real Time Clocks":
    QuickDescStruct([],
                    "IC, RTC, %(Manufacturer Part Number)s",
                    ""
                   ),
"Interface - Analog Switches, Multiplexers, Demultiplexers":  # TODO: make this better
    QuickDescStruct([],
                    "IC, Analog Switch, %(Manufacturer Part Number)s",
                    "%(Multiplexer/Demultiplexer Circuit)s"
                   ),
"Interface - I/O Expanders":
    QuickDescStruct([],
                    "IC, I/O Expander, %(Manufacturer Part Number)s",
                    "%(Interface)s, %(Number of I/O)s I/O"
                   ),
### ICs, Misc, Sensors
"Magnetic Sensors - Linear, Compass (ICs)":
    QuickDescStruct([],
                    "Sensor, Magnetic, %(Manufacturer Part Number)s",
                    "%(Axis)s axis, %(Bandwidth)s"
                   ),
"Optical Sensors - Photo Detectors - CdS Cells":
    QuickDescStruct([],
                    "CdS Photocell",
                    ""
                   ),
"Optical Sensors - Photodiodes":
    QuickDescStruct([],
                    "Photodiode",
                    ""
                   ),
"Optical Sensors - Reflective - Analog Output":
    QuickDescStruct([],
                    "Optical Reflective Sensor",
                    ""
                   ),
"Microphones":
    QuickDescStruct([],
                    "Microphone",
                    "%(Type)s"
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
  ('(D\u00B2?Pak)', '%s'),
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

def DigikeyQuickDesc(row_dict):
  print("Processing digikey_pn='%s'" % row_dict['digikey_pn'])

  parametrics_str = row_dict['parametrics']
  if not parametrics_str:
    return {}
  parametrics = ast.literal_eval(parametrics_str)
  family = parametrics['Categories']
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
  return {'dist_title': title,
          'dist_package': package,
          'dist_quickdesc': quickdesc}

load().map_append(DigikeyQuickDesc) \
    .map_append(RemapParametric('dist_mfrpn', 'Manufacturer Part Number')) \
    .map_append(RemapParametric('dist_desc', 'Description')) \
    .write()
