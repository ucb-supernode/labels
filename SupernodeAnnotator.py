import ast

from labelannotator import *

def PriorityMap(in_fields, out_field):
  def annotate_fn(row_dict):
    for in_field in in_fields:
      if in_field in row_dict and row_dict[in_field]:
        return {out_field: row_dict[in_field]}
    return {}

  return annotate_fn

def BackgroundColor(row_dict):
  if not row_dict['parametrics']:
    return {}

  parametrics = ast.literal_eval(row_dict['parametrics'])

  if row_dict['cost']:
    return {'bg_color': '#FFC0C0'}
  elif 'Mounting Type' in parametrics:
    if parametrics['Mounting Type'].find('Through Hole') >= 0:
      return {'bg_color': '#C0FFC0'}
  return {'bg_color': '#FFFFFF'}

load().map_append(BackgroundColor) \
    .map_append(PriorityMap(['manual_title', 'dist_title'], 'title')) \
    .map_append(PriorityMap(['manual_package', 'dist_package'], 'package')) \
    .map_append(PriorityMap(['manual_quickdesc', 'dist_quickdesc'], 'quickdesc')) \
    .map_append(PriorityMap(['manual_mfrpn', 'dist_mfrpn'], 'mfrpn')) \
    .map_append(PriorityMap(['manual_desc', 'dist_desc'], 'desc')) \
    .write()
