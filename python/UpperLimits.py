"""
@file UpperLimits.py

@brief Class to compute upper limits and to manage the resulting data.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/ASP/drpMonitoring/python/computeUpperLimit.py,v 1.3 2008/03/12 03:38:42 jchiang Exp $
#
import pyLikelihood as pyLike
import numpy as num

class ULResult(object):
    def __init__(self, value, emin, emax, delta, fluxes, dlogLike, parvalues):
        self.value = value
        self.emin, self.emax = emin, emax
        self.delta = delta
        self.fluxes, self.dlogLike, self.parvalues = fluxes, dlogLike, parvalues
    def __repr__(self):
        return ("%.2e ph/cm^2/s for emin=%.1f, emax=%.1f, delta(logLike)=%.2f"
                % (self.value, self.emin, self.emax, self.delta))

class UpperLimit(object):
    def __init__(self, like, source):
        self.like = like
        self.source = source
        self.results = []
    def compute(self, emin=100, emax=3e5, delta=2.71/2., 
                tmpfile='temp_model.xml', fix_src_pars=False,
                verbose=True, nsigmax=5, npts=30):
        source = self.source
        saved_pars = [par.value() for par in self.like.model.params]

        # Fix the normalization parameter for the scan.
        src_spectrum = self.like[source].funcs['Spectrum']
        par = src_spectrum.normPar()
        par.setFree(0)

        # For weak sources that use the PowerLaw model where the
        # reference energy is too low or that use the PowerLaw2 model
        # where the lower energy bound is too low, there can be a
        # strong correlation of the normalization parameter with the
        # photon index.  In this case, one can try to fix the other
        # source parameters to get a more stable upper limit. In
        # practice, one should reset the reference energy or lower
        # energy bound.
        if fix_src_pars:
            freePars = pyLike.ParameterVector()
            src_spectrum.getFreeParams(freePars)
            for item in freePars:
                src_spectrum.parameter(item.getName()).setFree(0)

        logLike0 = self.like()
        x0 = par.getValue()
        dx = par.error()

        if dx == 0:
            dx = x0
        xvals, dlogLike, fluxes = [], [], []
        if verbose:
            print self.like.model
        for i, x in enumerate(num.arange(x0, x0+nsigmax*dx, nsigmax*dx/npts)):
            xvals.append(x)
            par.setValue(x)
            self.like.logLike.syncSrcParams(source)
            try:
                self.like.fit(0)
            except RuntimeError:
                try:
                    self.like.fit(0)
                except RuntimeError:
                    self.like.logLike.restoreBestFit()
                    pass
            dlogLike.append(self.like() - logLike0)
            fluxes.append(self.like[source].flux(emin, emax))
            if verbose:
                print i, x, dlogLike[-1], fluxes[-1]
            if dlogLike[-1] > delta:
                break
            if len(dlogLike) > 2 and dlogLike[-1] < dlogLike[-2]:
                xvals.pop()
                dlogLike.pop()
                break
        par.setFree(1)
        if fix_src_pars:
            for item in freePars:
                src_spectrum.parameter(item.getName()).setFree(1)
        for value, param in zip(saved_pars, self.like.model.params):
            param.setValue(value)
        self.like.fit(0)
        xx = ((delta - dlogLike[-2])/(dlogLike[-1] - dlogLike[-2])
              *(xvals[-1] - xvals[-2]) + xvals[-2])
        ul = ((delta - dlogLike[-2])/(dlogLike[-1] - dlogLike[-2])
              *(fluxes[-1] - fluxes[-2]) + fluxes[-2])

        self.results.append(ULResult(ul, emin, emax, delta,
                                     fluxes, dlogLike, xvals))

        return ul

class UpperLimits(dict):
    def __init__(self, like):
        dict.__init__(self)
        self.like = like
        for srcName in like.sourceNames():
            if self.like.logLike.getSource(srcName).getType() == "Point":
                self[srcName] = UpperLimit(like, srcName)
    
if __name__ == '__main__':
    from UnbinnedAnalysis import *
    like = unbinnedAnalysis(mode='h')
    ul = UpperLimits(like)
    ul['grb'].compute()
    print ul['grb'].results
