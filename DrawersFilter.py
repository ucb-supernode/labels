from labelannotator import *
import re

load() \
    .filter(FieldEquals('template', 'drawer')) \
    .write()
