"""
@file UpperLimits.py

@brief Class to compute upper limits and to manage the resulting data.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/ASP/pyASP/python/UpperLimits.py,v 1.1 2008/05/13 05:13:13 jchiang Exp $
#
import pyLikelihood as pyLike
import numpy as num

class QuadraticFit(object):
    def __init__(self, xx, yy):
        self.Sx = self.Sy = self.Sxy = self.Sxx = self.npts = 0
        self.xmin = min(xx)
        for x, y in zip(xx, yy):
            self.add_pair(x, y)
    def add_pair(self, x, y):
        xx = (x-self.xmin)*(x-self.xmin)
        self.Sx += xx
        self.Sy += y
        self.Sxy += xx*y
        self.Sxx +=  xx*xx
        self.npts += 1
    def fitPars(self):
        denominator = self.npts*self.Sxx - self.Sx*self.Sx
        slope = (self.npts*self.Sxy - self.Sy*self.Sx)/denominator
        intercept = (self.Sxx*self.Sy - self.Sx*self.Sxy)/denominator
        return intercept, slope
    def xval(self, yval):
        y0, dydx = self.fitPars()
        return num.sqrt((yval - y0)/dydx) + self.xmin
    def yval(self, xval):
        y0, dydx = self.fitPars()
        return y0 + dydx*xval*xval
    
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
                verbose=True, nsigmax=2, npts=5, renorm=False):
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
        #
        # Fit a quadratic to a handful of points
        #
        for i, x in enumerate(num.arange(x0, x0+nsigmax*dx, nsigmax*dx/npts)):
            xvals.append(x)
            par.setValue(x)
            self.like.logLike.syncSrcParams(source)
            self.fit(0, renorm=renorm)
            dlogLike.append(self.like() - logLike0)
            fluxes.append(self.like[source].flux(emin, emax))
            if verbose:
                print i, x, dlogLike[-1], fluxes[-1]
        yfit = QuadraticFit(xvals, dlogLike)
        #
        # Extend the fit until it surpasses the desired delta
        #
        while dlogLike[-1] < delta and len(dlogLike) < 30:
            x = yfit.xval(1.1*delta)
            xvals.append(x)
            par.setValue(x)
            self.like.logLike.syncSrcParams(source)
            self.fit(0, renorm=renorm)
            dlogLike.append(self.like() - logLike0)
            fluxes.append(self.like[source].flux(emin, emax))
            yfit.add_pair(x, dlogLike[-1])
            i += 1
            if verbose:
                print i, x, dlogLike[-1], fluxes[-1]
        par.setFree(1)
        if fix_src_pars:
            for item in freePars:
                src_spectrum.parameter(item.getName()).setFree(1)
        for value, param in zip(saved_pars, self.like.model.params):
            param.setValue(value)
        self._resyncPars()
        xx = ((delta - dlogLike[-2])/(dlogLike[-1] - dlogLike[-2])
              *(xvals[-1] - xvals[-2]) + xvals[-2])
        ul = ((delta - dlogLike[-2])/(dlogLike[-1] - dlogLike[-2])
              *(fluxes[-1] - fluxes[-2]) + fluxes[-2])
        self.results.append(ULResult(ul, emin, emax, delta,
                                     fluxes, dlogLike, xvals))
        return ul
    def _resyncPars(self):
        srcNames = self.like.sourceNames()
        for src in srcNames:
            self.like.logLike.syncSrcParams(src)
    def fit(self, verbosity=0, renorm=False):
        if renorm:
            self._renorm()
            return
        try:
            self.like.fit(verbosity)
        except RuntimeError:
            try:
                self.like.fit(verbosity)
            except RuntimeError:
                self.like.logLike.restoreBestFit()
                pass
    def _renorm(self):
        freeNpred, totalNpred = self._npredValues()
        deficit = sum(self.like.nobs) - totalNpred
        renormFactor = 1. + deficit/freeNpred
        if renormFactor < 1:
            renormFactor = 1
        srcNames = self.like.sourceNames()
        for src in srcNames:
            parameter = self.like._normPar(src)
            if parameter.isFree():
                oldValue = parameter.getValue()
                newValue = oldValue*renormFactor
                xmin, xmax = parameter.getBounds()
                newValue = min(max(newValue, xmin), xmax)
                parameter.setValue(newValue)
        self._resyncPars()
    def _npredValues(self):
        srcNames = self.like.sourceNames()
        freeNpred = 0
        totalNpred = 0
        for src in srcNames:
            npred = self.like.logLike.NpredValue(src)
            totalNpred += npred
            if self.like._normPar(src).isFree():
                freeNpred += npred
        return freeNpred, totalNpred

class UpperLimits(dict):
    def __init__(self, like):
        dict.__init__(self)
        self.like = like
        for srcName in like.sourceNames():
            if self.like.logLike.getSource(srcName).getType() == "Point":
                self[srcName] = UpperLimit(like, srcName)

if __name__ == '__main__':
    import hippoplotter as plot
    from analysis import like
    ul = UpperLimits(like)
    print ul['point source 0'].compute(renorm=True)
    results = ul['point source 0'].results[0]
    plot.scatter(results.parvalues, results.dlogLike, xname='par value',
                 yname='dlogLike')
    plot.hline(2.71/2)
