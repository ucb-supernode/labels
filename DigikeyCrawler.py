import argparse
import csv
import re

from urllib.parse import quote
import httplib2
from bs4 import BeautifulSoup

from annotators import *

URL_PREFIX = 'http://search.digikey.com/scripts/DkSearch/dksus.dll?Detail?name='
h = httplib2.Http('.cache')
PARAMETRICS_BLACKLIST = ['Quantity Available']
HEADER_CONTINUE = ['Categories']

def parse_digikey_table(soup_table):
  elements = {}
  last_header = None
  for row in soup_table.findChildren('tr'):
    header = row.find('th')
    value = row.find('td')

    if value is None:
      continue

    if header is None and last_header in HEADER_CONTINUE:
      header = last_header
    elif header is not None:
      header = header.get_text().strip()
      last_header = header

    if header not in PARAMETRICS_BLACKLIST:
      elements[header] = value.get_text().strip()

  return elements

def digikey_fn(row_dict):
  if 'digikey_pn' in row_dict and row_dict['digikey_pn']:
    _, content = h.request(URL_PREFIX + quote(row_dict['digikey_pn']),
                           headers={'user-agent': '=)'})
    content = content.decode('utf-8')

    # The part attributes table has a hanging </a> tag. Fail...
    content = re.sub(r'</a>', '', content)
    content = re.sub(r'<a[^>]*>', '', content)
    content = content.replace('&nbsp;', '')
    content = content.replace('\n', '')
    content = content.replace('\t', '')

    soup = BeautifulSoup(content, 'html.parser')

    parametrics = {}
    parametrics.update(parse_digikey_table(soup.find('table', id='product-details')))
    parametrics.update(parse_digikey_table(soup.find('table', id='prod-att-table')))

    return {'parametrics': str(parametrics)}
  else:
    return {}

DigiKeyAnnotator = AnnotateFn(['parametrics'], digikey_fn)

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="Pulls part parametric data from DigiKey")
  parser.add_argument('--input', '-i', required=True,
                      help="Input CSV file")
  parser.add_argument('--output', '-o', required=True,
                      help="Output CSV file")
  args = parser.parse_args()

  with open(args.input, 'r', encoding='utf-8') as infile:
    input_rows = list(csv.reader(infile, delimiter=','))
  output_rows = annotate(input_rows, None, [DigiKeyAnnotator])

  with open(args.output, 'w', newline='', encoding='utf-8') as outfile:
    output_writer = csv.writer(outfile, delimiter=',')
    for output_row in output_rows:
      output_writer.writerow(output_row)
