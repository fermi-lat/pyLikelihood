# -*- python -*-
#
# $Id: SConscript,v 1.21 2009/02/23 01:31:43 glastrm Exp $
# Authors: James Chiang <jchiang@slac.stanford.edu>
# Version: pyLikelihood-01-10-01

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
