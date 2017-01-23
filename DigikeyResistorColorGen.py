import ast

from labelannotator import *

resistor_colors = {
  -1: '#CFB53B',  # gold
  -2: '#C0C0C0',  # silver
  0: '#000000',   # black
  1: '#964B00',   # brown
  2: '#FF0000',   # red
  3: '#FFA500',   # orange
  4: '#FFFF00',   # yellow
  5: '#9ACD32',   # green
  6: '#6495ED',   # blue
  7: '#EE82EE',   # violet
  8: '#A0A0A0',   # grey
  9: '#FFFFFF',   # white
}

# maps from percent tolerance to colors
resistor_tolerance_colors = {
  1: '#964B00',   # brown
  2: '#FF0000',   # red
  0.5: '#9ACD32',   # green
  0.25: '#6495ED',   # blue
  0.1: '#EE82EE',   # violet
  0.05: '#A0A0A0',   # grey
  5: '#CFB53B',   # gold
  10: '#C0C0C0',   # silver
}

resistance_multiplier = {
  'k': 3,
  'M': 6,
  'G': 9,
}

def ResistorColor(row_dict):
  print("Generating colors for digikey_pn='%s'" % row_dict['digikey_pn'])

  parametrics = ast.literal_eval(row_dict['parametrics'])

  if parametrics['Categories'] != "Through Hole Resistors":
    return {
      'res_color1': '',
      'res_color2': '',
      'res_color3': '',
    }
  assert "Resistance (Ohms)" in parametrics, "Resistor without resistance"
  res_str = parametrics["Resistance (Ohms)"]

  # Do calculations with string manipulation to avoid floating-point loss of
  # precision and things like 4.6999999999k.

  if res_str[-1].isalpha():
    mult_str = res_str[-1]
    res_nopow_str = res_str[:-1]
    assert mult_str in resistance_multiplier, "Unknown multiplier '%s'" % mult_str
    mult_pow = resistance_multiplier[mult_str]
  else:
    mult_pow = 0
    res_nopow_str = res_str

  dot_point = res_nopow_str.find('.')
  if dot_point > 0:
    assert not (dot_point == 1 and res_nopow_str[0] == '0'), "TODO: handle <1ohm codes"
    mult_code = dot_point - 2 + mult_pow
    nodot_str = res_nopow_str[0:dot_point] + res_nopow_str[dot_point+1:]
  else:
    mult_code = len(res_nopow_str) - 2 + mult_pow

    nodot_str = res_nopow_str

  val1_code = int(nodot_str[0])
  if len(nodot_str) > 1:
    val2_code = int(nodot_str[1])
    assert nodot_str[2:] == '0'*(len(nodot_str) - 2)
  else:
    val2_code = 0

  return {
    'res_color1': resistor_colors[val1_code],
    'res_color2': resistor_colors[val2_code],
    'res_color3': resistor_colors[mult_code],
  }

load().map_append(ResistorColor) \
    .write()
