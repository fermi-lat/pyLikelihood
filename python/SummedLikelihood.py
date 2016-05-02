"""
@brief Wrapper interface for pyLikelihood.SummedLikelihood to provide
more natural semantics for use in python alongside other analysis
classes.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/ScienceTools-scons/pyLikelihood/python/SummedLikelihood.py,v 1.24 2016/04/28 22:29:46 echarles Exp $
#

import pyLikelihood as pyLike
from SrcModel import SourceModel
from LikelihoodState import LikelihoodState
from AnalysisBase import AnalysisBase

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
    def getScale(self):
        return self.pars[0].getScale()
    def getBounds(self):
        return self.pars[0].getBounds()
    def isFree(self):
        return self.pars[0].isFree()
    def error(self):
        return self.pars[0].error()
    def alwaysFixed(self):
        return self.pars[0].alwaysFixed()
    def setFree(self, flag):
        for par in self.pars:
            par.setFree(flag)
    def setValue(self, value):
        for par in self.pars:
            par.setValue(value)
    def setError(self, error):
        for par in self.pars:
            par.setError(error)
    def setBounds(self, minValue, maxValue):
        for par in self.pars:
            par.setBounds(minValue, maxValue)
    def setScale(self, scale):
        for par in self.pars:
            par.setScale(scale)
    def setAlwaysFixed(self, alwaysFixed):
        for par in self.pars:
            par.setAlwaysFixed(alwaysFixed)
    def setEquals(self, rhs):
        for par in self.pars:
            par.setEquals(rhs)
    def __getattr__(self, attrname):
        return getattr(self.pars[0], attrname)

class SummedLikelihood(AnalysisBase):
    def __init__(self, optimizer='Minuit'):
        self.composite = pyLike.SummedLikelihood()
        #the C++ SummedLikelihood has many if not all the properties
        #of a logLike object
        self.logLike = self.composite
        self.components = []
        self.covariance = None
        self.covar_is_current = False
        self.optObject = None
        self.optimizer = optimizer
        self.tolType = pyLike.ABSOLUTE
        self.tol = 1e-2
        self.saved_state = None
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
        negLogLike = -self.composite.value()
        self.saveBestFit(negLogLike)
        return negLogLike
    def optimize(self, verbosity=3, tol=None, optimizer=None):
        self._syncParams()
        if optimizer is None:
            optimizer = self.optimizer
        if tol is None:
            tol = self.tol
        optFactory = pyLike.OptimizerFactory_instance()
        myOpt = optFactory.create(optimizer, self.composite)
        myOpt.find_min_only(verbosity, tol, self.tolType)
        self.saveBestFit()
    def normPar(self, source):
        return Parameter([like.normPar(source) for like in self.components])
    def __call__(self):
        negLogLike = -self.composite.value()
        self.saveBestFit(negLogLike)
        return negLogLike
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

    def nFreeParams(self):        
        '''Count the number of free parameters in the active model.'''
        nF = 0
        pars = self.params()
        for par in pars:
            if par.isFree():
                nF += 1
        return nF

    def saveBestFit(self, negLogLike=None):
        if negLogLike is None:
            negLogLike = -self.composite.value()
        if (self.saved_state is None or 
            negLogLike <= self.saved_state.negLogLike):
            self.saveCurrentFit(negLogLike)
    def saveCurrentFit(self, negLogLike=None):
        self.saved_state = LikelihoodState(self, negLogLike)
    def restoreBestFit(self):
        if (self.saved_state is not None and 
            self() > self.saved_state.negLogLike):
            self.saved_state.restore()
        else:
            self.saveCurrentFit()
    def NpredValue(self, src):
        return self.composite.NpredValue(src)
    def total_nobs(self):
        return sum([sum(x.nobs) for x in self.components])
    def __repr__(self):
        return str(self.components[0].model)
    def _syncParams(self):
        for component in self.components:
            component.logLike.syncParams()
    def __getitem__(self, name):
        item = self.model[name]
        try:
            item.type
            return item
        except AttributeError:
            par = Parameter([item])
            for comp in self.components[1:]:
                par.addParam(comp[name])
            return par
    def __setitem__(self, name, value):
        for component in self.components:
            component[name] = value
            component.syncSrcParams(self.model[name].srcName)
    def thaw(self, i):
        for component in self.components:
            component.thaw(i)
        self.saved_state = None
    def freeze(self, i):
        for component in self.components:
            component.freeze(i)
        self.saved_state = None
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
        self._set_errors(errors)
        return errors
    def _set_errors(self, errors):
        source_attributes = self.components[0].getExtraSourceAttributes()
        my_errors = list(errors)
        self.composite.setErrors(my_errors)
        for component in self.components:
            component.model = SourceModel(component.logLike)
            for src in source_attributes:
                component.model[src].__dict__.update(source_attributes[src])
    def minosError(self, srcname, parname, level=1):
        freeParams = pyLike.ParameterVector()
        self.composite.getFreeParams(freeParams)
        saved_values = [par.getValue() for par in freeParams]
        par_index = self.components[0].par_index(srcname, parname)
        index = self.composite.findIndex(par_index)
        if index == -1:
            raise RuntimeError("Invalid parameter specification")
        try:
            errors = self.optObject.Minos(index, level)
            self.composite.setFreeParamValues(saved_values)
            return errors
        except RuntimeError, message:
            print "Minos error encountered for parameter %i" % index
            self.composite.setFreeParamValues(saved_values)
    def par_index(self, srcname, parname):
        return self.components[0].par_index(srcname, parname)
    def Ts(self, srcName, reoptimize=False, approx=True,
           tol=None, MaxIterations=10, verbosity=0):
        if verbosity > 0:
            print "*** Start Ts_dl ***"
        source_attributes = self.components[0].getExtraSourceAttributes()
        self.syncSrcParams()
        freeParams = pyLike.DoubleVector()
        self.components[0].logLike.getFreeParamValues(freeParams)
        # Get the number of free parameters in the baseline mode
        n_free_test = len(freeParams)
        n_free_src = len(self.freePars(srcName))
        n_free_base = n_free_test - n_free_src

        logLike1 = -self()
        self._ts_src = []
        for comp in self.components:
            comp._ts_src = comp.logLike.deleteSource(srcName) 
            self._ts_src.append(comp._ts_src)
        logLike0 = -self()
        if tol is None:
            tol = self.tol
   
        if reoptimize and n_free_base > 0:
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
            if approx and n_free_base > 0:
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
        self.model = self.components[0].model
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
    def setSpectrum(self, srcName, functionName):
        for comp in self.components:
            comp.setSpectrum(srcName, functionName)
        self.model = self.components[0].model
    def deleteSource(self, srcName):
        src = self.components[0].deleteSource(srcName)
        for comp in self.components[1:]:
            comp.deleteSource(srcName)
        self.model = self.components[0].model
        self.saved_state = None
        return src
    def addSource(self, src):
        for comp in self.components:
            comp.addSource(src)
        self.model = self.components[0].model
        self.saved_state = None

    def plot(self, *args):
        raise NotImplementedError("plot not implemented for SummedLikelihood")
    def setPlotter(self, *args):
        raise NotImplementedError("setPlotter not implemented for SummedLikelihood")
    def oplot(self, *args):
        raise NotImplementedError("oplot not implemented for SummedLikelihood")
    def plotSource(self, *args):
        raise NotImplementedError("plotSource not implemented for SummedLikelihood")
    def writeCountsSpectra(self, *args):
        raise NotImplementedError("writeCountsSpectra not implemented for SummedLikelihood")
    def setFitTolType(self, tolType):
        if tolType in (pyLike.RELATIVE, pyLike.ABSOLUTE):
            for comp in self.components:
                comp.setFitTolType(tolType)
        else:
            raise RuntimeError("Invalid fit tolerance type. " +
                               "Valid values are 0=RELATIVE or 1=ABSOLUTE")
    def setFreeFlag(self, srcName, pars, value):
        for comp in self.components:
            comp.setFreeFlag(srcName, pars, value)
    def writeXml(self, xmlFile=None):
        self.components[0].writeXml(xmlFile)
