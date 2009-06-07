"""
@brief Wrapper interface for pyLikelihood.SummedLikelihood to provide
more natural symantics for use in python alongside other analysis classes.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/pyLikelihood/python/SummedLikelihood.py,v 1.1 2009/06/05 23:42:28 jchiang Exp $
#

import pyLikelihood as pyLike

class Parameter(object):
    def __init__(self, pars):
        self.pars = pars
    def value(self):
        self.pars[

class SummedLikelihood(object):
    def __init__(self, optimizer='Minuit'):
        self.logLike = pyLike.SummedLikelihood()
        self.components = []
        self.covariance = None
        self.covar_is_current = False
        self.optObject = None
        self.optimizer = optimizer
        self.tolType = pyLike.ABSOLUTE
        self.tol = 1e-2
    def addComponent(self, like):
        self.logLike.addComponent(like.logLike)
        self.components.append(like)
        if len(self.components) == 1:
            self.model = self.components[0].model
    def fit(self, verbosity=3, tol=None, optimizer=None,
            covar=False, optObject=None):
        if tol is None:
            tol = self.tol
        errors = self._errors(optimizer, verbosity, tol, covar=covar,
                              optObject=optObject)
        return -self.logLike.value()
    def sourceNames(self):
        return self.components[0].sourceNames()
    def __getattr__(self, attrname):
        return getattr(self.logLike, attrname)
    def __repr__(self):
        return str(self.components[0].model)
    def _syncParams(self):
        for component in self.components:
            component.logLike.syncParams()
    def _errors(self, optimizer=None, verbosity=0, tol=None,
                useBase=False, covar=False, optObject=None):
        self._syncParams()
        if optimizer is None:
            optimizer = self.optimizer
        if tol is None:
            tol = self.tol
        if optObject is None:
            optFactory = pyLike.OptimizerFactory_instance()
            myOpt = optFactory.create(optimizer, self.logLike)
        else:
            myOpt = optObject
        self.optObject = myOpt
        myOpt.find_min(verbosity, tol, self.tolType)
        errors = myOpt.getUncertainty(useBase)
        if covar:
            self.covariance = myOpt.covarianceMatrix()
            self.covar_is_current = True
        else:
            self.covar_is_current = False
        for component in self.components:
            j = 0
            for i in range(len(component.model.params)):
                if component.model[i].isFree():
                    component.model[i].setError(errors[j])
                    j += 1
        return errors
