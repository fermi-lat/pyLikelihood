# -*- python -*-
#
# $Id$

import glob, os, platform

Import('baseEnv')
Import('listFiles')
progEnv = baseEnv.Clone()
libEnv = baseEnv.Clone()

pyLikelihoodStaticLib = libEnv.StaticLibrary('lib_pyLikelihood', 
                                             'src/pyLikelihood.i')
pyLikelihoodSharedLib = libEnv.SharedLibrary('lib_pyLikelihood', 
                                             'src/pyLikelihood.i')

progEnv.Tool('registerObjects', package = 'pyLikelihood', 
             libraries = [pyLikelihoodStaticLib, pyLikelihoodSharedLib], 
             includes = listFiles(['pyLikelihoood/*.h']))
