# labels
Labelmaker database and processing scripts

## Generating 3x labels
- CSV data generation: `python resistor3x_gen.py`
- Label generation: `python labelmaker/labelmaker.py template_pth3x.svg generated/resistors3x_data.csv generated/resistors3x.svg`

## Generating Digikey labels
- Fetch parametrics from Digikey: `python DigikeyCrawler.py -i resistors_digikey.csv -o resistors_digikey_ann.csv`
- Generate label fields: `python DigikeyLabelGen.py -i resistors_digikey_ann.csv -o resistors_digikey_label.csv`
- Label generation: `python labelmaker/labelmaker.py template_generic.svg resistors_digikey_label.csv generated/resistors_digikey.svg`