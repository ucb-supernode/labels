import argparse
import csv

from collections import OrderedDict

# Provides a functional, lightweight abstraction over CSV files, allowing annotators to focus on
# the data processing instead of the plumbing.

# An immutable representation of a CSV file, providing functional abstractions for data processing.
class CsvRowCollection:
  def __init__(self, header, rows, outname):
    self.header = header
    self.rows = rows
    self.outname = outname

  # Writes data out to a CSV.
  def write(self):
    with open(self.outname, 'w', newline='', encoding='utf-8') as outfile:
      output_writer = csv.writer(outfile, delimiter=',')
      output_writer.writerow(self.header)
      for row in self.rows:
        output_writer.writerow(row)

  # Takes a function of row dict (column header -> value) that returns a row dict of elements to
  # append. Appended column headers may not overlap with existing column headers.
  # If a OrderedDict is passed in, the order of the new header elements will be according to dict
  # order (which must be consistent across all rows), otherwise it will be alphabetical.
  # Returns a new CsvRowCollection.
  def map_append(self, fn):
    append_keys = set()
    new_row_dicts = []
    for row in self.rows:
      row_dict = {k: v for (k, v) in zip(self.header, row)}
      append_dict = fn(row_dict)
      # TODO: support ordered dict
      assert not isinstance(append_dict, OrderedDict), "Ordering unsupported"
      assert set(row_dict.keys()).isdisjoint(append_dict.keys()), "overlap between row " + row_dict.keys() + " and append " + append_dict.keys()
      append_keys = append_keys | append_dict.keys()
      new_row_dicts.append(dict(row_dict, **append_dict))

    new_header = self.header + list(append_keys)
    new_rows = []
    for row_dict in new_row_dicts:
      new_row = [row_dict.get(key, "") for key in new_header]
      new_rows.append(new_row)

    return CsvRowCollection(new_header, new_rows, self.outname)

  # Takes a function of row dict (column header -> value) that returns a group key.
  # Returns a CsvGroupedRows object, which can map over groups.
  def groupby(self, fn):
    groups_dict = OrderedDict()
    for row in self.rows:
      row_dict = {k: v for (k, v) in zip(self.header, row)}
      row_group = fn(row_dict)
      if row_group not in groups_dict:
        groups_dict[row_group] = []
      groups_dict[row_group].append(row_dict)

    return CsvGroupedRows(groups_dict, self.outname)

  # Takes a function of row dict -> boolean. If false, the row is removed from the output.
  def filter(self, fn):
    filtered_rows = []
    for row in self.rows:
      row_dict = {k: v for (k, v) in zip(self.header, row)}
      if fn(row_dict):
        filtered_rows.append(row)

    return CsvRowCollection(self.header, filtered_rows, self.outname)

class CsvGroupedRows:
  def __init__(self, groups_dict, outname):
    self.groups_dict = groups_dict
    self.outname = outname

  # Takes a function of (group name, list[row_dict]) that returns a list of row dicts.
  # Returns a CsvRowCollection of the new rows.
  def group_map(self, fn):
    all_row_dicts = []
    for group_name, group_row_dicts in self.groups_dict.items():
      new_row_dicts = fn(group_name, group_row_dicts)
      all_row_dicts.extend(new_row_dicts)

    header_set = set()
    for row_dict in all_row_dicts:
      header_set.update(row_dict.keys())
    header = list(header_set)
    new_rows = []
    for row_dict in all_row_dicts:
      new_row = [row_dict.get(key, "") for key in header]
      new_rows.append(new_row)

    return CsvRowCollection(list(header_set), new_rows, self.outname)

# Loads and parses the input dataset, with filenames parsed from system arguments.
def load(desc="dataset annotator"):
  parser = argparse.ArgumentParser(description=desc)
  parser.add_argument('--input', '-i', required=True,
                      help="Input CSV file")
  parser.add_argument('--output', '-o', required=True,
                      help="Output CSV file")
  args = parser.parse_args()

  with open(args.input, 'r', encoding='utf-8') as infile:
    rows = list(csv.reader(infile, delimiter=','))

  return CsvRowCollection(rows[0], rows[1:], args.output)
