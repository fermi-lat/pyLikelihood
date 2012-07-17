# -*- python -*-
#
# $Id: SConscript,v 1.106 2012/06/14 05:29:27 jchiang Exp $
# Authors: James Chiang <jchiang@slac.stanford.edu>
# Version: pyLikelihood-01-30-02

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

