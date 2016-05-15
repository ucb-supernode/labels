# labels
Labelmaker database and processing scripts

## Generating labels
Works best on Python 3.

[SCons](http://scons.org/) is used as a build system, which tracks dependencies (labelmaker sources, input data files) and does minimal incremental builds. To build all the labels, invoke `scons` inside the repository root.
