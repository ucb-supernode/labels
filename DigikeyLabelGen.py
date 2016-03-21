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
    paramterics = ast.literal_eval(row_dict['parametrics'])
    return {out_name: paramterics[field_name]}
  return AnnotateFn([out_name], annotate_fn)

ParametricPreprocess = namedtuple('ParametricPreprocess', ['name', 'fn'])

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
def list_select_first_regex_match(matches, separator=','):
  match_progs = [re.compile(match) for match in matches]
  def fn(in_string):
    substrings = in_string.split(separator)
    substrings = [substr.strip() for substr in substrings]
    for match_prog in match_progs:
      for substr in substrings:
        if match_prog.match(substr):
          return substr
    # TODO: proper exception hierarchy
    raise Exception("Failed to match on '%s' with matchers %s" % (in_string, matches))
    
  return fn

QuickDescStruct = namedtuple('QuickDescStruct', ['preprocessors', 'title', 'quickdesc'])
quickdesc_rules = {
"Through Hole Resistors":
    QuickDescStruct([ParametricPreprocess("Power (Watts)", list_select_first_regex_match(["\d+/\d+W"
                                                                                          ".*"]))
                     ],
                    u"Res, %(Resistance (Ohms))s\u03A9",
                    "%(Tolerance)s, %(Power (Watts))s"
                    )
}

def DigikeyQuickDescAnnotator():
  def annotate_fn(row_dict):
    parametrics = ast.literal_eval(row_dict['parametrics'])
    family = parametrics['Family']
    assert family in quickdesc_rules, "no rule for part family '%s'" % family
    quickdesc_rule = quickdesc_rules[family] 
    for processor in quickdesc_rule.preprocessors:
      assert processor.name in parametrics, "Preprocessor for family '%s' needs pamametric '%s'" % (family, processor.name)
      parametrics[processor.name] = processor.fn(parametrics[processor.name])
    title = quickdesc_rule.title % parametrics
    package = parametrics['Package / Case']
    quickdesc = quickdesc_rule.quickdesc % parametrics
    return {'title': title,
            'package': package,
            'quickdesc': quickdesc}
    
  return AnnotateFn(['title', 'package', 'quickdesc'], annotate_fn)
  
if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="Generates label fields using Digikey parametrics")
  parser.add_argument('--input', '-i', required=True,
                      help="Input CSV file with Digikey parametrics")
  parser.add_argument('--output', '-o', required=True,
                      help="Output CSV file")
  args = parser.parse_args()
  
  with open(args.input, 'r', encoding='utf-8') as infile:
    input_rows = list(csv.reader(infile, delimiter=','))
    
  output_rows = annotate(input_rows, None, [DigikeyQuickDescAnnotator(),
                                            DigikeyFieldAnnotator('mfrpn', 'Manufacturer Part Number'),
                                            DigikeyFieldAnnotator('desc', 'Description'),
                                            DigikeyFieldAnnotator('code', 'Digi-Key Part Number'),
                                            ])
  
  with open(args.output, 'w', newline='', encoding='utf-8') as outfile:
    output_writer = csv.writer(outfile, delimiter=',')
    for output_row in output_rows:
      output_row = output_row
      output_writer.writerow(output_row)
    