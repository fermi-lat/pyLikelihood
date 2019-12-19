"""
@brief Wrapper interface for pyLikelihood.Composite2 to provide
more natural symantics for use in python alongside other analysis classes.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/ScienceTools-scons/pyLikelihood/python/Composite2.py,v 1.5 2010/07/10 17:01:49 jchiang Exp $
#

import pyLikelihood as pyLike
from SrcModel import SourceModel

class Composite2(object):
    def __init__(self, optimizer='Minuit'):
        self.composite = pyLike.Composite2()
        self.components = []
        self.tolType = pyLike.ABSOLUTE
        self.tol = 1e-2
        self.covariance = None
        self.covar_is_current = False
        self.optObject = None
        self.optimizer = optimizer
    def addComponent(self, like):
        self.composite.addComponent(like.logLike)
        self.components.append(like)
    def tieParameters(self, pars):
        my_pars = tuple([(x[0].logLike, x[0].par_index(x[1], x[2])) 
                         for x in pars])
        self.composite.tieParameters(my_pars)
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
    def minosError(self, component, srcname, parname, level=1):
        freeParams = pyLike.ParameterVector()
        self.composite.getFreeParams(freeParams)
        saved_values = [par.getValue() for par in freeParams]
        indx = self._compositeIndex(component, srcname, parname)
        if indx == -1:
            raise RuntimeError("Invalid parameter specification.")
        try:
            errors = self.optObject.Minos(indx, level)
            self.composite.setFreeParamValues(saved_values)
            return errors
        except RuntimeError, message:
            print ("Minos error encountered for parameter %i." % indx)
            self.composite.setFreeParamValues(saved_values)
    def _compositeIndex(self, target_component, target_src, target_par):
        indx = target_component.par_index(target_src, target_par)
        return self.composite.findIndex(target_component.logLike, indx)
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
        self.composite.setErrors(my_errors)
        for component in self.components:
            component.model = SourceModel(component.logLike)
    def __getattr__(self, attrname):
        return getattr(self.composite, attrname)
    def __repr__(self):
        my_string = []
        for i, component in enumerate(self.components):
            my_string.append("\n")
            my_string.append("Component %i:\n" % i)
            my_string.append(str(component.model))
        return "\n".join(my_string)
