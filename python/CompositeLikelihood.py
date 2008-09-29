"""
@brief Wrapper interface for pyLikelihood.CompositeLikelihood to provide
more natural symantics for use in python alongside other analysis classes.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/pyLikelihood/python/CompositeLikelihood.py,v 1.1 2008/09/26 05:11:40 jchiang Exp $
#

import pyLikelihood as pyLike

class CompositeLikelihood(object):
    def __init__(self):
        self.composite = pyLike.CompositeLikelihood()
        self.srcNames = []
        self.components = []
    def addComponent(self, srcName, like):
        self.composite.addComponent(srcName, like.logLike)
        self.srcNames.append(srcName)
        self.components.append(like)
    def fit(self, verbosity=2, tol=1e-5, optimizer='Minuit'):
        myOpt = pyLike.OptimizerFactory_instance().create(optimizer,
                                                          self.composite)
        myOpt.find_min(verbosity, tol)
    def __getattr__(self, attrname):
        return getattr(self.composite, attrname)
    def __repr__(self):
        my_string = []
        for name, component in zip(self.srcNames, self.components):
            my_string.append("\n")
            my_string.append("Component %s:\n" % name)
            my_string.append(str(component.model))
        return "\n".join(my_string)
