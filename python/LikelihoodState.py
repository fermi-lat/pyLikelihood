"""
@brief Classes to save the state of fit parameters.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/ScienceTools-scons/pyLikelihood/python/LikelihoodState.py,v 1.5 2012/11/20 16:49:52 jchiang Exp $
#
import pyLikelihood

#class _Parameter(object):
#    "Shadow class of the optimizers::Parameter class."
#    def __init__(self, par):
#        self.par = par
#        self.value = par.getValue()
#        self.minValue, self.maxValue = par.getBounds()
#        self.free = par.isFree()
#        self.scale = par.getScale()
#        self.error = par.error()
#        self.alwaysFixed = par.alwaysFixed()
#    def setDataMembers(self, par=None):
#        if par is None:
#            par = self.par
#        par.setValue(self.value)
#        par.setBounds(self.minValue, self.maxValue)
#        par.setFree(self.free)
#        par.setScale(self.scale)
#        par.setError(self.error)
#        par.setAlwaysFixed(self.alwaysFixed)

class _Parameter(object):
    """Thin wrapper around pyLikelihood.Parameter, temporarily, for
    refactoring purposes.  Eventually, should replace with 
    pyLikelihood.Parameter."""
    def __init__(self, par):
        self.par = pyLikelihood.Parameter(par.parameter)
    def setDataMembers(self, par=None):
        if par is None:
            par = self.par
            return
        par.setDataValues(self.par)


class LikelihoodState(object):
    """Save the parameter state of a pyLikelihood object and provide a
    method to restore everything or just a specific source."""
    def __init__(self, like, negLogLike=None):
        if negLogLike is None:
            self.negLogLike = like()
        else:
            self.negLogLike = negLogLike
        self.like = like
        self.pars = [_Parameter(par) for par in like.params()]
        self.covariance = like.covariance
        self.covar_is_current = like.covar_is_current 
    def restore(self, srcName=None):
        if srcName is None:
            for par, likePar in zip(self.pars, self.like.params()):
                par.setDataMembers(likePar)
            self.like.covariance = self.covariance
            self.like.covar_is_current = self.covar_is_current 
        else:
            parNames = pyLikelihood.StringVector()
            self.like[srcName].src.spectrum().getParamNames(parNames)
            for parName in parNames:
                indx = self.like.par_index(srcName, parName)
                likePar = self.like.params()[indx]
                self.pars[indx].setDataMembers(likePar)
        self.like.syncSrcParams()
