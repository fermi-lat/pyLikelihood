"""
@brief Wrapper interface for pyLikelihood.CompositeLikelihood to provide
more natural symantics for use in python alongside other analysis classes.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/pyLikelihood/python/CompositeLikelihood.py,v 1.2 2008/09/29 16:53:39 jchiang Exp $
#

import pyLikelihood as pyLike

class CompositeLikelihood(object):
    def __init__(self):
        self.composite = pyLike.CompositeLikelihood()
        self.srcNames = []
        self.components = []
        self.tolType = pyLike.ABSOLUTE
        self.tol = 1e-2
    def addComponent(self, srcName, like):
        self.composite.addComponent(srcName, like.logLike)
        self.srcNames.append(srcName)
        self.components.append(like)
    def fit(self, verbosity=2, tol=None, optimizer='Minuit'):
        myOpt = pyLike.OptimizerFactory_instance().create(optimizer,
                                                          self.composite)
        if tol is None:
            tol = self.tol
        myOpt.find_min(verbosity, tol, self.tolType)
    def __getattr__(self, attrname):
        return getattr(self.composite, attrname)
    def __repr__(self):
        my_string = []
        for name, component in zip(self.srcNames, self.components):
            my_string.append("\n")
            my_string.append("Component %s:\n" % name)
            my_string.append(str(component.model))
        return "\n".join(my_string)
