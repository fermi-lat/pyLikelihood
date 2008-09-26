"""
@brief Wrapper interface for pyLikelihood.CompositeLikelihood to provide
more natural symantics for use in python alongside other analysis classes.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header$
#

import pyLikelihood as pyLike

class CompositeLikelihood(object):
    def __init__(self):
        self.composite = pyLike.CompositeLikelihood()
    def addComponent(self, srcName, like):
        self.composite.addComponent(srcName, like.logLike)
    def fit(self, verbosity=2, tol=1e-5, optimizer='Minuit'):
        myOpt = pyLike.OptimizerFactory_instance().create(optimizer,
                                                          self.composite)
        myOpt.find_min(verbosity, tol)
    def __getattr__(self, attrname):
        return getattr(self.composite, attrname)
