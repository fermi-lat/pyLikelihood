# -*- python -*-
#
# $Id: SConscript,v 1.52 2009/11/13 16:27:05 jchiang Exp $
# Authors: James Chiang <jchiang@slac.stanford.edu>
# Version: pyLikelihood-01-18-02

Import('baseEnv')
Import('listFiles')
progEnv = baseEnv.Clone()
libEnv = baseEnv.Clone()

libEnv.Tool('pyLikelihoodLib', depsOnly = 1)
pyLikelihoodSharedLib = libEnv.LoadableModule('_pyLikelihood', 
                                              'src/pyLikelihood.i')

progEnv.Tool('registerTargets', package = 'pyLikelihood', 
             swigLibraryCxts = [[pyLikelihoodSharedLib, libEnv]], 
             includes = listFiles(['pyLikelihood/*.h']),
             python = listFiles(['python/*.py']) + ['src/pyLikelihood.py'])

