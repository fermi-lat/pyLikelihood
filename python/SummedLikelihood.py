"""
@brief Wrapper interface for pyLikelihood.SummedLikelihood to provide
more natural symantics for use in python alongside other analysis classes.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/pyLikelihood/python/SummedLikelihood.py,v 1.3 2009/06/08 06:11:41 jchiang Exp $
#

import pyLikelihood as pyLike

class Parameter(object):
    "Composite parameter object."
    def __init__(self, pars=[]):
        self.pars = pars
    def addParam(self, par):
        self.pars.append(par)
    def value(self):
        return self.pars[0].value()
    def getValue(self):
        return self.pars[0].getValue()
    def getBounds(self):
        return self.pars[0].getBounds()
    def isFree(self):
        return self.pars[0].isFree()
    def error(self):
        return self.pars[0].error()
    def setFree(self, flag):
        for par in self.pars:
            par.setFree(flag)
    def setValue(self, value):
        for par in self.pars:
            par.setValue(value)
    def setError(self, error):
        for par in self.pars:
            par.setError(error)

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
    def syncSrcParams(self, src=None):
        if src is not None:
            for comp in self.components:
                comp.logLike.syncSrcParams(src)
        else:
            for comp in self.components:
                for src in self.sourceNames():
                    comp.logLike.syncSrcParams(src)
    def fit(self, verbosity=3, tol=None, optimizer=None,
            covar=False, optObject=None):
        if tol is None:
            tol = self.tol
        errors = self._errors(optimizer, verbosity, tol, covar=covar,
                              optObject=optObject)
        return -self.composite.value()
    def optimize(self, verbosity=3, tol=None, optimizer=None):
        self._syncParams()
        if optimizer is None:
            optimizer = self.optimizer
        if tol is None:
            tol = self.tol
        optFactory = pyLike.OptimizerFactory_instance()
        myOpt = optFactory.create(optimizer, self.composite)
        myOpt.find_min_only(verbosity, tol, self.tolType)
    def normPar(self, source):
        return Parameter([like.normPar(source) for like in self.components])
    def __call__(self):
        return -self.composite.value()
    def sourceNames(self):
        return self.components[0].sourceNames()
    def params(self):
        my_params = []
        for i, like in enumerate(self.components):
            for j, par in enumerate(like.params()):
                if i == 0:
                    my_params.append(Parameter([par]))
                else:
                    my_params[j].addParam(par)
        return my_params
    def saveCurrentFit(self):
        for comp in self.components:
            comp.logLike.saveCurrentFit()
    def restoreBestFit(self):
        for comp in self.components:
            comp.logLike.restoreBestFit()
    def NpredValue(self, src):
        return sum([x.logLike.NpredValue(src) for x in self.components])
    def total_nobs(self):
        return sum([sum(x.nobs) for x in self.components])
    def __getattr__(self, attrname):
        print "called __getattr__ for ", attrname
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
