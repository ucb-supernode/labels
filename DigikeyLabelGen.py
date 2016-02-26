import argparse
import ast
import csv

from annotators import *

def DigikeyFieldAnnotator(out_name, field_name):
  def annotate_fn(row_dict):
    paramterics = ast.literal_eval(row_dict['parametrics'])
    return paramterics[field_name]
  return AnnotateFn(out_name, annotate_fn)

def DigikeyTitleAnnotator(out_name):
  def annotate_fn(row_dict):
    # Family to format string
    rules = {
      "Through Hole Resistors": u"Res, %(Resistance (Ohms))s\u03A9"
    }
    parametrics = ast.literal_eval(row_dict['parametrics'])
    family = parametrics['Family']
    assert family in rules, "Family '" + family + "' not in rules table"
    return rules[family] % parametrics
  return AnnotateFn(out_name, annotate_fn)

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="Generates label fields using Digikey parametrics")
  parser.add_argument('--input', '-i', required=True,
                      help="Input CSV file with Digikey parametrics")
  parser.add_argument('--output', '-o', required=True,
                      help="Output CSV file")
  args = parser.parse_args()
  
  with open(args.input, 'r', encoding='utf-8') as infile:
    input_rows = list(csv.reader(infile, delimiter=','))
    
  output_rows = annotate(input_rows, None, [DigikeyTitleAnnotator('title'),
                                            DigikeyFieldAnnotator('package', 'Package / Case'),
                                            DigikeyFieldAnnotator('quickdesc', 'Tolerance'),
                                            DigikeyFieldAnnotator('mfrpn', 'Manufacturer Part Number'),
                                            DigikeyFieldAnnotator('desc', 'Description'),
                                            DigikeyFieldAnnotator('code', 'Digi-Key Part Number'),
                                            ])
  
  with open(args.output, 'w', newline='', encoding='utf-8') as outfile:
    output_writer = csv.writer(outfile, delimiter=',')
    for output_row in output_rows:
      output_row = output_row
      output_writer.writerow(output_row)
    