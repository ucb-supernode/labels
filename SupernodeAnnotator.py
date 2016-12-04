import argparse
import csv

import ast

from annotators import *

def DescAnnotator():
  def annotate_fn(row_dict):
    parametrics = ast.literal_eval(row_dict['parametrics'])

    if 'Description' in parametrics:
      return {'desc' : parametrics['Description']}
    else:
      return {}

  return AnnotateFn(['desc'], annotate_fn)

def LabelBackgroundAnnotator():
  def annotate_fn(row_dict):
    parametrics = ast.literal_eval(row_dict['parametrics'])

    if row_dict['cost']:
      return {'bg_color' : '#FFC0C0'}
    if 'Mounting Type' in parametrics:
      if parametrics['Mounting Type'].find('Through Hole') >= 0:
        return {'bg_color' : '#C0FFC0'}

    return {'bg_color' : '#FFFFFF'}

  return AnnotateFn(['bg_color'], annotate_fn)

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

def DigikeyResistorColorAnnotator():
  def annotate_fn(row_dict):
    parametrics = ast.literal_eval(row_dict['parametrics'])
    if parametrics['Family'] != "Through Hole Resistors":
      return {}
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
    else:
      val2_code = 0

    return {
      'res_color1': resistor_colors[val1_code],
      'res_color2': resistor_colors[val2_code],
      'res_color3': resistor_colors[mult_code],
     }

  return AnnotateFn(['res_color1', 'res_color2', 'res_color3'], annotate_fn)

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="Label dataset annotator")
  parser.add_argument('--input', '-i', required=True,
                      help="Input CSV file with Digikey parametrics")
  parser.add_argument('--output', '-o', required=True,
                      help="Output CSV file")
  args = parser.parse_args()

  with open(args.input, 'r', encoding='utf-8') as infile:
    input_rows = list(csv.reader(infile, delimiter=','))

  output_rows = annotate(input_rows, None, [
    LabelBackgroundAnnotator(),
    DescAnnotator(),
    DigikeyResistorColorAnnotator()
  ])

  with open(args.output, 'w', newline='', encoding='utf-8') as outfile:
    output_writer = csv.writer(outfile, delimiter=',')
    for output_row in output_rows:
      output_row = output_row
      output_writer.writerow(output_row)
