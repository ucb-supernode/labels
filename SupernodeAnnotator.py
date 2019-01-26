import ast

from labelannotator import *
import re

def GrididExists(row_dict):
  if row_dict['gridid']:
    return True
  else:
    return False

def BackgroundColor(row_dict):
  if row_dict['cost']:
    return {'bg_color': '#FFC0C0'}
  return {'bg_color': '#FFFFFF'}

def ColoredPackage(row_dict):
  if not row_dict['parametrics']:
    return {'diptitle': '', 'packtitle': row_dict['title']}

  parametrics = ast.literal_eval(row_dict['parametrics'])
  if (('Mounting Type' in parametrics and parametrics['Mounting Type'].find('Through Hole') >= 0) or
      (re.match(".*DIP$", row_dict['package'])) or
  (re.match("Axial", row_dict['package']))):
    return {'diptitle': row_dict['title'], 'pack': ''}
  else:
    return {'diptitle': '', 'packtitle': row_dict['title']}

def CostPrefix(row_dict):
  if row_dict['cost']:
    return {'pcost': ' ' + row_dict['cost']}
  else:
    return {'pcost': ''}

load() \
    .filter(GrididExists) \
    .map_append(PriorityMap(['manual_title', 'dist_title'], 'title')) \
    .map_append(PriorityMap(['manual_package', 'dist_package'], 'package')) \
    .map_append(PriorityMap(['manual_quickdesc', 'dist_quickdesc'], 'quickdesc')) \
    .map_append(PriorityMap(['manual_mfrpn', 'dist_mfrpn'], 'mfrpn')) \
    .map_append(PriorityMap(['manual_desc', 'dist_desc'], 'desc')) \
    .map_append(BackgroundColor) \
    .map_append(ColoredPackage) \
    .map_append(CostPrefix) \
    .write()
