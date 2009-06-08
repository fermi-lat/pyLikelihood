"""
@brief Wrapper interface for pyLikelihood.SummedLikelihood to provide
more natural symantics for use in python alongside other analysis classes.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/pyLikelihood/python/SummedLikelihood.py,v 1.2 2009/06/07 03:22:07 jchiang Exp $
#

import pyLikelihood as pyLike

class Parameter(object):
    "Composite parameter object."
    def __init__(self, pars=[]):
        self.pars = pars
    def addParam(self, par):
        self.pars.append(par)
    def __getattr___(self, attrname):
        return getattr(self.pars[0], attrname)
    def setFree(self, flag):
        for par in self.pars:
            par.setFree(flag)
    def setValue(self, value):
        for par in self.pars:
            par.setValue(value)

class SummedLikelihood(object):
    def __init__(self, optimizer='Minuit'):
        self.composite = pyLike.SummedLikelihood()
        self.components = []
        self.covariance = None
        self.covar_is_current = False
        self.optObject = None
        self.optimizer = optimizer
        self.tolType = pyLike.ABSOLUTE
        self.tol = 1e-2
    def sourceNames(self):
        return self.components[0].sourceNames()
    def addComponent(self, like):
        self.composite.addComponent(like.logLike)
        self.components.append(like)
        if len(self.components) == 1:
            self.model = self.components[0].model
            self.logLike = self.components[0].logLike
    def fit(self, verbosity=3, tol=None, optimizer=None,
            covar=False, optObject=None):
        if tol is None:
            tol = self.tol
        errors = self._errors(optimizer, verbosity, tol, covar=covar,
                              optObject=optObject)
        return -self.composite.value()
    def __call__(self):
        return -self.composite.value()
    def sourceNames(self):
        return self.components[0].sourceNames()
    def params(self):
        my_params = Parameter([x for x in self.components[0].params()])
        for item in self.components[1:]:
            for par in item.params():
                my_params.addParam(par)
        return my_params
    def __getattr__(self, attrname):
        return getattr(self.components[0], attrname)
    def __repr__(self):
        return str(self.components[0].model)
    def _syncParams(self):
        for component in self.components:
            component.logLike.syncParams()
    def __getitem__(self, name):
        return self.model[name]
    def __setitem__(self, name, value):
        self.model[name] = value
        self.composite.syncSrcParams(self.model[name].srcName)
    def _errors(self, optimizer=None, verbosity=0, tol=None,
                useBase=False, covar=False, optObject=None):
        self._syncParams()
        if optimizer is None:
            optimizer = self.optimizer
        if tol is None:
            tol = self.tol
        if optObject is None:
            optFactory = pyLike.OptimizerFactory_instance()
            myOpt = optFactory.create(optimizer, self.composite)
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
