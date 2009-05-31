# -*- python -*-
#
# $Id: SConscript,v 1.32 2009/05/31 04:31:47 glastrm Exp $
# Authors: James Chiang <jchiang@slac.stanford.edu>
# Version: pyLikelihood-01-13-00

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
