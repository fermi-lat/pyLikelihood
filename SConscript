# -*- python -*-
#
# $Id: SConscript,v 1.34 2009/06/08 23:31:04 glastrm Exp $
# Authors: James Chiang <jchiang@slac.stanford.edu>
# Version: pyLikelihood-01-14-01

Import('baseEnv')
Import('listFiles')
progEnv = baseEnv.Clone()
libEnv = baseEnv.Clone()

libEnv.Tool('pyLikelihoodLib', depsOnly = 1)
pyLikelihoodSharedLib = libEnv.SharedLibrary('_pyLikelihood', 
                                             'src/pyLikelihood.i')

progEnv.Tool('registerObjects', package = 'pyLikelihood', 
             libraries = [pyLikelihoodSharedLib], 
             includes = listFiles(['pyLikelihood/*.h']),
             python = listFiles(['python/*.py']))
