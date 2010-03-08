"""
@brief Classes to save the state of fit parameters.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/pyLikelihood/python/LikelihoodState.py,v 1.1 2009/09/21 18:28:03 jchiang Exp $
#
import pyLikelihood

class _Parameter(object):
    "Shadow class of the optimizers::Parameter class."
    def __init__(self, par):
        self.par = par
        self.value = par.getValue()
        self.minValue, self.maxValue = par.getBounds()
        self.free = par.isFree()
        self.scale = par.getScale()
        self.error = par.error()
        self.alwaysFixed = par.alwaysFixed()
    def setDataMembers(self, par=None):
        if par is None:
            par = self.par
        par.setValue(self.value)
        par.setBounds(self.minValue, self.maxValue)
        par.setFree(self.free)
        par.setScale(self.scale)
        par.setError(self.error)
        par.setAlwaysFixed(self.alwaysFixed)

class LikelihoodState(object):
    """Save the parameter state of a pyLikelihood object and provide a
    method to restore everything or just a specific source."""
    def __init__(self, like):
        self.negLogLike = like()
        self.like = like
        self.pars = [_Parameter(par) for par in like.params()]
    def restore(self, srcName=None):
        if srcName is None:
            for par in self.pars:
                par.setDataMembers()
        else:
            parNames = pyLikelihood.StringVector()
            self.like[srcName].src.spectrum().getParamNames(parNames)
            for parName in parNames:
                indx = self.like.par_index(srcName, parName)
                self.pars[indx].setDataMembers()
        self.like.syncSrcParams()
