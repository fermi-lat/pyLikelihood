# -*- python -*-
#
# $Id: SConscript,v 1.151 2016/09/15 21:28:09 echarles Exp $
# Authors: James Chiang <jchiang@slac.stanford.edu>, Eric Charles <echarles@slac.stanford.edu>, Matthew Wood <mdwood@slac.stanford.edu> 
# Version: pyLikelihood-02-03-06

Import('baseEnv')
Import('listFiles')
progEnv = baseEnv.Clone()
libEnv = baseEnv.Clone()

if baseEnv['PLATFORM'] == "posix":
    progEnv.Append(CPPDEFINES = 'TRAP_FPE')
    libEnv.Append(CPPDEFINES = 'TRAP_FPE')

libEnv.Tool('pyLikelihoodLib', depsOnly = 1)
pyLikelihoodSharedLib = libEnv.SwigLibrary('_pyLikelihood', 
                                           'src/pyLikelihood.i')

progEnv.Tool('registerTargets', package = 'pyLikelihood', 
             swigLibraryCxts = [[pyLikelihoodSharedLib, libEnv]], 
             includes = listFiles(['pyLikelihood/*.h']),
             python = listFiles(['python/*.py']) + ['src/pyLikelihood.py'])

