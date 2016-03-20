from collections import namedtuple

"""
Annotation function, rules for adding new columns to a CSV based on input data.
out_names is a list of names of the new columns. Must not alias with any part
of the input.
fn is a function taking a dict from column names to row values and returning a
dict from new column names to new row values. An exception will be thrown if
the dict contains other keys, but empty values will be automatically inserted
if the dict is missing keys.
"""
AnnotateFn = namedtuple('AnnotateFn', ['out_names', 'fn'])

"""
Adds columns defined in col_fns to the csv defined by input_rows, returning
an array of rows.
input_rows must be the rows of the CSV, with the first element being the header.
existing_rows is optional, the rows of an existing output CSV for running
incremental updates.
col_fns is an array of AnnotateFns. They are executed in the order defined, so
a step may refer to previous elements.
"""
def annotate(input_rows, existing_rows, annotate_fns):
  assert existing_rows is None, "incremental not supported yet"
  input_header = input_rows[0]
  input_data = input_rows[1:]
  input_header_dict = {ind: val for (ind, val) in enumerate(input_header)}
  
  output_header = list(input_header)
  output_data = []
  for annotate_fn in annotate_fns:
    assert isinstance(annotate_fn.out_names, list) 
    assert set(annotate_fn.out_names).isdisjoint(output_header)
    
    output_header.extend(annotate_fn.out_names)
  
  for input_row in input_data:
    print("Processing %s=%s" % (input_header_dict[0], input_row[0]))
    row_dict = {input_header_dict[ind]: val for (ind, val) in enumerate(input_row)}
    output_row = list(input_row)
    for annotate_fn in annotate_fns:
      annotate_dict = annotate_fn.fn(row_dict)
      for out_name in annotate_fn.out_names:
        out_val = annotate_dict.get(out_name, '')
        output_row.append(out_val)
        row_dict[out_name] = out_val
    output_data.append(output_row)
  
  output_rows = [output_header]
  output_rows.extend(output_data)
  
  return output_rows