import argparse
import ast
import collections
import csv

from annotators import *

def DigikeyFieldAnnotator(out_name, field_name):
  def annotate_fn(row_dict):
    paramterics = ast.literal_eval(row_dict['parametrics'])
    return paramterics[field_name]
  return AnnotateFn(out_name, annotate_fn)

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="Generates label fields using Digikey parametrics")
  parser.add_argument('--input', '-i', required=True,
                      type=argparse.FileType('r'),
                      help="Input CSV file with Digikey parametrics")
  parser.add_argument('--output', '-o', required=True,
                      help="Output CSV file")
  args = parser.parse_args()
  
  input_rows = list(csv.reader(args.input, delimiter=','))
  output_rows = annotate(input_rows, None, [DigikeyFieldAnnotator('title', 'Manufacturer Part Number'),
                                            DigikeyFieldAnnotator('package', 'Package / Case'),
                                            DigikeyFieldAnnotator('quickdesc', 'Tolerance'),
                                            DigikeyFieldAnnotator('mfrpn', 'Manufacturer Part Number'),
                                            DigikeyFieldAnnotator('desc', 'Description'),
                                            DigikeyFieldAnnotator('code', 'Digi-Key Part Number'),
                                            ])
  
  with open(args.output, 'w', newline='', encoding='utf-8') as outfile:
    output_writer = csv.writer(outfile, delimiter=',')
    for output_row in output_rows:
      output_writer.writerow(output_row)
    