"""
@brief Wrapper interface for pyLikelihood.CompositeLikelihood to provide
more natural symantics for use in python alongside other analysis classes.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/pyLikelihood/python/CompositeLikelihood.py,v 1.6 2010/05/03 22:28:47 cohen Exp $
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
    def minosError(self, component_name, srcname, parname,level=1):
        freeParams = pyLike.ParameterVector()
        self.composite.getFreeParams(freeParams)
        saved_values = [par.getValue() for par in freeParams]
        indx = self._compositeIndex(component_name, srcname, parname)
        if indx == -1:
            raise RuntimeError("Invalid parameter specification")
        try:
            errors = self.optObject.Minos(indx,level)
            self.composite.setFreeParamValues(saved_values)
            return errors
        except RuntimeError, message:
            print ("Minos error encountered for parameter %i." % par_index)
            print ("Attempting to reset free parameters.")
            for tiedName, component in zip(self.srcNames, self.components):
                if component_name == tiedName:
                    component.thaw(component.par_index(srcname, parname))
                    break
            self.composite.setFreeParamValues(saved_values)
            raise RuntimeError(message)
    def _compositeIndex(self, target_component, target_src, target_par):
        indx = -1
        #
        # Loop over non-tied parameters
        #
        for tiedName, component in zip(self.srcNames, self.components):
            srcNames = component.sourceNames()
            for src in srcNames:
                if src != tiedName:
                    spec = component.model[src].funcs['Spectrum']
                    parnames = pyLike.StringVector()
                    spec.getFreeParamNames(parnames)
                    for parname in parnames:
                        indx += 1
                        if (target_component == tiedName and
                            target_src == src and
                            target_par == parname):
                            return indx

        #
        # Loop over tied parameters for common sources (just need to do 
        # this for the first component).
        #
        spec = self.components[0].model[self.srcNames[0]].funcs['Spectrum']
        parnames = pyLike.StringVector()
        spec.getFreeParamNames(parnames)
        for parname in parnames:
            if parname != spec.normPar().getName():
                indx += 1
                if target_src in self.srcNames and target_par == parname:
                    return indx
        #
        # Loop over normalization parameters
        #
        for src, component in zip(self.srcNames, self.components):
            spec = component.model[src].funcs['Spectrum']
            if spec.normPar().isFree():
                parname = spec.normPar().getName()
                indx += 1
                if target_src == src and target_par == parname:
                    return indx
        return indx
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
    def __getattr__(self, attrname):
        return getattr(self.composite, attrname)
    def __repr__(self):
        my_string = []
        for name, component in zip(self.srcNames, self.components):
            my_string.append("\n")
            my_string.append("Component %s:\n" % name)
            my_string.append(str(component.model))
        return "\n".join(my_string)
