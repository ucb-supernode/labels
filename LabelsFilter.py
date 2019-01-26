from labelannotator import *
import re

load() \
    .filter(FieldEquals('template', 'label')) \
    .write()
