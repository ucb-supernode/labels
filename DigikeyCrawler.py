import argparse
import collections
import csv
import re

from urllib.parse import quote
import httplib2
from bs4 import BeautifulSoup

from annotators import *

URL_PREFIX = 'http://search.digikey.com/scripts/DkSearch/dksus.dll?Detail?name='
h = httplib2.Http('.cache')
PARAMETRICS_BLACKLIST = ['Quantity Available']

def parse_digikey_table(soup_table):
  elements = collections.OrderedDict()
  for row in soup_table.findChildren('tr'):
    header = row.find('th')
    value = row.find('td')
    if (header is not None) and (value is not None):
      if header.get_text().strip() not in PARAMETRICS_BLACKLIST:
        elements[header.get_text().strip()] = value.get_text().strip()
  return elements

def digikey_fn(row_dict):
  resp_headers, content = h.request(URL_PREFIX + quote(row_dict['digikey_pn']))
  content = content.decode('utf-8')
  
  # The part attributes table has a hanging </a> tag. Fail...
  content = re.sub(r'</a>', '', content)
  content = re.sub(r'<a[^>]*>', '', content)
  content = content.replace('&nbsp;', '')
  content = content.replace('\n', '')
  content = content.replace('\t', '')

  soup = BeautifulSoup(content, 'html.parser')
  
  parametrics = collections.OrderedDict()
  parametrics.update(parse_digikey_table(soup.find('table', id='product-details')))
  parametrics.update(parse_digikey_table(soup.find('table', 'attributes-table-main')))
  
  return str(parametrics)

DigiKeyAnnotator = AnnotateFn("parametrics", digikey_fn)

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="Pulls part parametric data from DigiKey")
  parser.add_argument('--input', '-i', required=True,
                      type=argparse.FileType('r'),
                      help="Input CSV file")
  parser.add_argument('--output', '-o', required=True,
                      type=argparse.FileType('w'),
                      help="Output CSV file")
  args = parser.parse_args()
  
  input_rows = list(csv.reader(args.input, delimiter=','))
  output_rows = annotate(input_rows, None, [DigiKeyAnnotator])
  
  output_writer = csv.writer(args.output, delimiter=',')
  for output_row in output_rows:
    output_writer.writerow(output_row)
    