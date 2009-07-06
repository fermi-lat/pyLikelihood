# -*- python -*-
#
# $Id: SConscript,v 1.37 2009/06/29 23:30:58 glastrm Exp $
# Authors: James Chiang <jchiang@slac.stanford.edu>
# Version: pyLikelihood-01-15-00

Import('baseEnv')
Import('listFiles')
progEnv = baseEnv.Clone()
libEnv = baseEnv.Clone()

libEnv.Tool('pyLikelihoodLib', depsOnly = 1)
pyLikelihoodSharedLib = libEnv.LoadableModule('_pyLikelihood', 
                                              'src/pyLikelihood.i')

progEnv.Tool('registerObjects', package = 'pyLikelihood', 
             libraries = [pyLikelihoodSharedLib], 
             includes = listFiles(['pyLikelihood/*.h']),
             python = listFiles(['python/*.py', 'src/pyLikelihood.py']))
