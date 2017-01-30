import ast

from labelannotator import *
import re

def GroupFn(row_dict):
  return row_dict['gridid']

def aggregate(key, dicts):
  val = dicts[0][key]
  for dict in dicts:
    assert dict[key] == val
  return val

def CombineFn(group_name, row_dicts):
  print("Combining group '%s'" % group_name)

  mapped_row_dicts = []
  for row_dict in row_dicts:
    mapped_row_dict = {
      'val': row_dict['val'],
      'res_color1': row_dict['res_color1'],
      'res_color2': row_dict['res_color2'],
      'res_color3': row_dict['res_color3'],
      'res_stroke': '#000000',
      }
    mapped_row_dicts.append(mapped_row_dict)

  dummy_dict = {
    'val': '',
    'res_color1': '#FFFFFF',
    'res_color2': '#FFFFFF',
    'res_color3': '#FFFFFF',
    'res_stroke': '#FFFFFF',
    }

  subdict = {}
  if len(mapped_row_dicts) == 1:
    subdict.update( {k + '_2': v for (k, v) in mapped_row_dicts[0].items()} )
    subdict.update( {k + '_1': v for (k, v) in dummy_dict.items()} )
    subdict.update( {k + '_3': v for (k, v) in dummy_dict.items()} )
  elif len(mapped_row_dicts) == 2:
    subdict.update( {k + '_1': v for (k, v) in mapped_row_dicts[0].items()} )
    subdict.update( {k + '_3': v for (k, v) in mapped_row_dicts[1].items()} )
    subdict.update( {k + '_2': v for (k, v) in dummy_dict.items()} )
  elif len(mapped_row_dicts) == 3:
    subdict.update( {k + '_1': v for (k, v) in mapped_row_dicts[0].items()} )
    subdict.update( {k + '_2': v for (k, v) in mapped_row_dicts[1].items()} )
    subdict.update( {k + '_3': v for (k, v) in mapped_row_dicts[2].items()} )
  else:
      assert False, "Unexpected #rows %s in group %s" % (len(mapped_row_dicts), group_name)

  retval = {'title': 'Resistor',
          'quickdesc': aggregate('quickdesc', row_dicts),
          'pack': aggregate('pack', row_dicts),
		  'dippack': aggregate('dippack', row_dicts),
          'cost': aggregate('cost', row_dicts),
          'bg_color': aggregate('bg_color', row_dicts),
          'gridid': aggregate('gridid', row_dicts),
          }
  retval.update(subdict)

  return [retval]

load() \
    .groupby(GroupFn) \
    .group_map(CombineFn) \
    .write()
