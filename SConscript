# -*- python -*-
#
# $Id: SConscript,v 1.2 2007/12/11 19:37:49 jchiang Exp $

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
