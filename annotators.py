from collections import namedtuple

"""
Annotation function, rules for adding a new column to a CSV.
out_name is the name of the new column. Must not alias with any part of the
input.
fn is a function taking a dict from column names to row values and returning a
string (the row contents).
"""
AnnotateFn = namedtuple('AnnotateFn', ['out_name', 'fn'])

"""
Adds columns defined in col_fns to the csv defined by input_rows, returning
an array of rows.
input_rows must be the rows of the CSV, with the first element being the header.
existing_rows is optional, the rows of an existing output CSV for running
incremental updates.
col_fns is an array of AnnotateFns. They are executed in the order defined, so
a step may refer to previous elements.
"""
def annotate(input_rows, existing_rows, col_fns):
  assert existing_rows is None, "incremental not supported yet"
  input_header = input_rows[0]
  input_data = input_rows[1:]
  input_header_dict = {ind: val for (ind, val) in enumerate(input_header)}
  
  output_header = list(input_header)
  output_data = []
  for col_fn in col_fns:
    assert col_fn.out_name not in output_header
    output_header.append(col_fn.out_name)
  
  for input_row in input_data:
    print("Processing %s=%s" % (input_header_dict[0], input_row[0]))
    row_dict = {input_header_dict[ind]: val for (ind, val) in enumerate(input_row)}
    output_row = list(input_row)
    for col_fn in col_fns:
      col_fn_val = col_fn.fn(row_dict)
      output_row.append(col_fn_val)
      row_dict[col_fn.out_name] = col_fn_val
    output_data.append(output_row)
  
  output_rows = [output_header]
  output_rows.extend(output_data)
  
  return output_rows