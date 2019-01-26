Import('env')

# A simple wrapper that invokes a Python script, passing an input file (-i) and
# an output filename (-o). Intended to do some transformation on a CSV file,
# like adding additional data / reformatting.
def Annotator(env, target, source, scripts):
  intermediate_target = source
  for i, script in enumerate(scripts):
    env = env.Clone()
    env['ANNOTATOR_SCRIPT'] = File(script)
    if i == len(scripts) - 1:
      new_target = target
    else:
      new_target = '%s_%s' % (target, i)

    env.Command(new_target, intermediate_target,
                "$PYTHON $ANNOTATOR_SCRIPT -i $SOURCE -o $TARGET")
    env.Depends(new_target, File(script))
    env.Depends(new_target, File('labelannotator.py'))
    intermediate_target = new_target
  return File(new_target)
env.AddMethod(Annotator)

# A labelmaker invocation, taking in the source CSV dataset and SVG template and
# generating a (set of) SVG labels.
def Labels(env, target, source_template, source_config, source_csv):
  env = env.Clone()
  env['LABELS_TEMPLATE'] = File(source_template)
  env['LABELS_CONFIG'] = File(source_config)
  env.Command(target, source_csv,
              '$PYTHON labelmaker/labelmaker.py $LABELS_TEMPLATE $LABELS_CONFIG $SOURCE $TARGET')
  env.Depends(target, File(source_template))
  env.Depends(target, File(source_config))
  env.Depends(target, Glob('labelmaker/*.py'))
  return File(target)
env.AddMethod(Labels)

resistors_front_csv = env.Annotator('resistors3x_color.csv',
                                    'data/resistors3x_data.csv',
                                    ['ResistorsColor.py'])
resistors_front_labels = env.Labels('resistors_front.svg',
                          'templates/template_resistors_3x.svg',
                          'templates/template_front.ini',
                          resistors_front_csv)

parts_sub_csv = env.Annotator('parts_sub.csv',
                          'data/parts_sub_digikey.csv',
                          ['DigikeyCrawler.py',
                           'DigikeyLabelGen.py',
                           'SupernodeAnnotator.py'])

parts_single_csv = env.Annotator('parts_single.csv',
                          'data/parts_single_digikey.csv',
                          ['DigikeyCrawler.py',
                           'DigikeyLabelGen.py',
                           'SupernodeAnnotator.py'])
parts_single_labels = env.Labels('parts_single.svg',
                          'templates/template_parts_single.svg',
                          'templates/template_front.ini',
                          parts_single_csv)
