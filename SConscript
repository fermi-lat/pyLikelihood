# -*- python -*-
#
# $Id: SConscript,v 1.3 2008/02/22 00:28:36 golpa Exp $

Import('baseEnv')
Import('listFiles')
progEnv = baseEnv.Clone()
libEnv = baseEnv.Clone()

libEnv.Tool('pyLikelihoodLib', depsOnly = 1)
pyLikelihoodStaticLib = libEnv.StaticLibrary('lib_pyLikelihood', 
                                             'src/pyLikelihood.i')
pyLikelihoodSharedLib = libEnv.SharedLibrary('lib_pyLikelihood', 
                                             'src/pyLikelihood.i')

progEnv.Tool('registerObjects', package = 'pyLikelihood', 
             libraries = [pyLikelihoodStaticLib, pyLikelihoodSharedLib], 
             includes = listFiles(['pyLikelihoood/*.h']))
