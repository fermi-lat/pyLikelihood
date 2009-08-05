"""
@brief Wrapper interface for pyLikelihood.CompositeLikelihood to provide
more natural symantics for use in python alongside other analysis classes.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/pyLikelihood/python/CompositeLikelihood.py,v 1.3 2009/03/31 18:20:53 jchiang Exp $
#

import pyLikelihood as pyLike

class CompositeLikelihood(object):
    def __init__(self, optimizer='Minuit'):
        self.composite = pyLike.CompositeLikelihood()
        self.srcNames = []
        self.components = []
        self.tolType = pyLike.ABSOLUTE
        self.tol = 1e-2
        self.covariance = None
        self.covar_is_current = False
        self.optObject = None
        self.optimizer = optimizer
    def addComponent(self, srcName, like):
        self.composite.addComponent(srcName, like.logLike)
        self.srcNames.append(srcName)
        self.components.append(like)
    def __call__(self):
        return -self.composite.value()
    def fit(self, verbosity=3, tol=None, optimizer=None,
            covar=False, optObject=None):
        if tol is None:
            tol = self.tol
        errors = self._errors(optimizer, verbosity, tol, covar=covar,
                              optObject=optObject)
        return self()
    def optimize(self, verbosity=3, tol=None, optimizer=None):
        self.composite.syncParams()
        if optimizer is None:
            optimizer = self.optimizer
        if tol is None:
            tol = self.tol
        optFactory = pyLike.OptimizerFactory_instance()
        myOpt = optFactory.create(optimizer, self.composite)
        myOpt.find_min_only(verbosity, tol, self.tolType)
    def _errors(self, optimizer=None, verbosity=0, tol=None,
                useBase=False, covar=False, optObject=None):
        self.composite.syncParams()
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
        my_errors = list(errors)
        #
        # Set errors for untied sources
        #
        for tiedName, component in zip(self.srcNames, self.components):
            srcNames = component.sourceNames()
            for src in srcNames:
                if src != tiedName:
                    spec = component.model[src].funcs['Spectrum']
                    parnames = pyLike.StringVector()
                    spec.getFreeParamNames(parnames)
                    for parname in parnames:
                        par_index = component.par_index(src, parname)
                        component.model[par_index].setError(my_errors.pop(0))
        #
        # Set errors for tied parameters for common sources
        #
        spec = self.components[0].model[self.srcNames[0]].funcs['Spectrum']
        numTiedPars = spec.getNumFreeParams()
        if spec.normPar().isFree():
            numTiedPars -= 1
        for src, component in zip(self.srcNames, self.components):
            tied_errors = my_errors[:numTiedPars]
            spec = component.model[src].funcs['Spectrum']
            parnames = pyLike.StringVector()
            spec.getFreeParamNames(parnames)
            for parname in parnames:
                if parname != spec.normPar().getName():
                    par_index = component.par_index(src, parname)
                    component.model[par_index].setError(tied_errors.pop(0))
        #
        # Set errors for normalization parameters
        #
        norm_errors = my_errors[numTiedPars:]
        for src, component in zip(self.srcNames, self.components):
            spec = component.model[src].funcs['Spectrum']
            if spec.normPar().isFree():
                parname = spec.normPar().getName()
                par_index = component.par_index(src, parname)
                component.model[par_index].setError(norm_errors.pop(0))
        print norm_errors
    def __getattr__(self, attrname):
        return getattr(self.composite, attrname)
    def __repr__(self):
        my_string = []
        for name, component in zip(self.srcNames, self.components):
            my_string.append("\n")
            my_string.append("Component %s:\n" % name)
            my_string.append(str(component.model))
        return "\n".join(my_string)
