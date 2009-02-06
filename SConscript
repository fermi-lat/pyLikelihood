# -*- python -*-
#
# $Id: SConscript,v 1.19 2009/01/27 01:31:25 glastrm Exp $
# Authors: James Chiang <jchiang@slac.stanford.edu>
# Version: pyLikelihood-01-09-06

Import('baseEnv')
Import('listFiles')
progEnv = baseEnv.Clone()
libEnv = baseEnv.Clone()

libEnv.Tool('pyLikelihoodLib', depsOnly = 1)
pyLikelihoodStaticLib = libEnv.StaticLibrary('_pyLikelihood', 
                                             'src/pyLikelihood.i', LIBPREFIX='')
pyLikelihoodSharedLib = libEnv.SharedLibrary('_pyLikelihood', 
                                             'src/pyLikelihood.i', SHLIBPREFIX='')

progEnv.Tool('registerObjects', package = 'pyLikelihood', 
             libraries = [pyLikelihoodStaticLib, pyLikelihoodSharedLib], 
             includes = listFiles(['pyLikelihoood/*.h']),
             python = listFiles(['python/*.py']))
