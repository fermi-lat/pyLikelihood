# -*- python -*-
#
# $Id: SConscript,v 1.71 2010/07/09 15:36:27 jchiang Exp $
# Authors: James Chiang <jchiang@slac.stanford.edu>
# Version: pyLikelihood-01-24-02

Import('baseEnv')
Import('listFiles')
progEnv = baseEnv.Clone()
libEnv = baseEnv.Clone()

libEnv.Tool('pyLikelihoodLib', depsOnly = 1)
pyLikelihoodSharedLib = libEnv.SwigLibrary('_pyLikelihood', 
                                           'src/pyLikelihood.i')

progEnv.Tool('registerTargets', package = 'pyLikelihood', 
             swigLibraryCxts = [[pyLikelihoodSharedLib, libEnv]], 
             includes = listFiles(['pyLikelihood/*.h']),
             python = listFiles(['python/*.py']) + ['src/pyLikelihood.py'])

