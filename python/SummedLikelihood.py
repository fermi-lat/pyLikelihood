"""
@brief Wrapper interface for pyLikelihood.SummedLikelihood to provide
more natural symantics for use in python alongside other analysis
classes.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/pyLikelihood/python/SummedLikelihood.py,v 1.6 2009/06/08 23:09:03 jchiang Exp $
#

import pyLikelihood as pyLike
from SrcModel import SourceModel

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
    def __repr__(self):
        return str(self.components[0].model)
    def _syncParams(self):
        for component in self.components:
            component.logLike.syncParams()
    def __getitem__(self, name):
        return self.model[name]
    def __setitem__(self, name, value):
        for component in self.components:
            component[name] = value
            component.syncSrcParams(self.model[name].srcName)
    def thaw(self, i):
        for component in self.components:
            component.thaw(i)
    def freeze(self, i):
        for component in self.components:
            component.freeze(i)
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
    def Ts(self, srcName, reoptimize=False, approx=True,
           tol=None, MaxIterations=10, verbosity=0):
        if verbosity > 0:
            print "*** Start Ts_dl ***"
        source_attributes = self.components[0].getExtraSourceAttributes()
        self.syncSrcParams()
        freeParams = pyLike.DoubleVector()
        self.components[0].logLike.getFreeParamValues(freeParams)
        logLike1 = -self()
        self._ts_src = []
        for comp in self.components:
            comp._ts_src = comp.logLike.deleteSource(srcName) 
            self._ts_src.append(comp._ts_src)
        logLike0 = -self()
        if tol is None:
            tol = self.tol
        if reoptimize:
            if verbosity > 0:
                print "** Do reoptimize"
            optFactory = pyLike.OptimizerFactory_instance()
            myOpt = optFactory.create(self.optimizer, self.composite)
            Niter = 1
            while Niter <= MaxIterations:
                try:
                    myOpt.find_min(0, tol)
                    break
                except RuntimeError,e:
                    print e
                if verbosity > 0:
                    print "** Iteration :",Niter
                Niter += 1
        else:
            if approx:
                try:
                    self._renorm()
                except ZeroDivisionError:
                    pass
        self.syncSrcParams()
        logLike0 = max(-self(), logLike0)
        Ts_value = 2*(logLike1 - logLike0)
        for ts_src, comp in zip(self._ts_src, self.components):
            comp.logLike.addSource(ts_src)
            comp.logLike.setFreeParamValues(freeParams)
            comp.model = SourceModel(comp.logLike)
            for src in source_attributes:
                comp.model[src].__dict__.update(source_attributes[src])
        return Ts_value
    def _renorm(self, factor=None):
        if factor is None:
            freeNpred, totalNpred = self._npredValues()
            deficit = self.total_nobs() - totalNpred
            self.renormFactor = 1. + deficit/freeNpred
        else:
            self.renormFactor = factor
        if self.renormFactor < 1:
            self.renormFactor = 1
        srcNames = self.sourceNames()
        for src in srcNames:
            parameter = self.normPar(src)
            if (parameter.isFree() and 
                self.components[0]._isDiffuseOrNearby(src)):
                oldValue = parameter.getValue()
                newValue = oldValue*self.renormFactor
                # ensure new value is within parameter bounds
                xmin, xmax = parameter.getBounds()
                if xmin <= newValue and newValue <= xmax:
                    parameter.setValue(newValue)
    def _npredValues(self):
        srcNames = self.sourceNames()
        freeNpred = 0
        totalNpred = 0
        for src in srcNames:
            npred = self.NpredValue(src)
            totalNpred += npred
            if (self.normPar(src).isFree() and 
                self.components[0]._isDiffuseOrNearby(src)):
                freeNpred += npred
        return freeNpred, totalNpred
