# -*- python -*-
#
# $Id: SConscript,v 1.35 2009/06/11 21:31:03 glastrm Exp $
# Authors: James Chiang <jchiang@slac.stanford.edu>
# Version: pyLikelihood-01-14-02

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
