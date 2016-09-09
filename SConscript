# -*- python -*-
#
# $Id: SConscript,v 1.146 2016/09/09 21:26:02 echarles Exp $
# Authors: James Chiang <jchiang@slac.stanford.edu>
# Version: pyLikelihood-02-03-02

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

