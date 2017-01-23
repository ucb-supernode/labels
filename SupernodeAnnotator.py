import ast

from labelannotator import *

def Description(row_dict):
  # map description field
  parametrics = ast.literal_eval(row_dict['parametrics'])

  if 'Description' in parametrics:
    return {'desc' : parametrics['Description']}
  else:
    return {}

def BackgroundColor(row_dict):
  parametrics = ast.literal_eval(row_dict['parametrics'])

  if row_dict['cost']:
    return {'bg_color': '#FFC0C0'}
  elif 'Mounting Type' in parametrics:
    if parametrics['Mounting Type'].find('Through Hole') >= 0:
      return {'bg_color': '#C0FFC0'}
  return {'bg_color': '#FFFFFF'}

load().map_append(Description) \
    .map_append(BackgroundColor) \
    .write()
