"""
@file UpperLimits.py

@brief Class to compute upper limits and to manage the resulting data.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/pyLikelihood/python/UpperLimits.py,v 1.13 2009/06/08 06:11:41 jchiang Exp $
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
                verbosity=1, nsigmax=2, npts=5, renorm=False,
                mindelta=1e-2):
        # Store the value of the covariance flag
        covar_is_current = self.like.covar_is_current
        source = self.source
        saved_pars = [par.value() for par in self.like.params()]
        saved_errors = [par.error() for par in self.like.params()]

        # Fix the normalization parameter for the scan.
        par = self.like.normPar(source)
        par.setFree(0)

        # Update the best-fit-so-far vector after having fixed the 
        # normalization parameter.
        self.like.saveCurrentFit()

        # For weak sources that use the PowerLaw model where the
        # reference energy is too low or that use the PowerLaw2 model
        # where the lower energy bound is too low, there can be a
        # strong correlation of the normalization parameter with the
        # photon index.  In this case, one can try to fix the other
        # source parameters to get a more stable upper limit. In
        # practice, one should reset the reference energy or lower
        # energy bound.
        if fix_src_pars:
            freePars = self.like.freePars(source)
            self.like.setFreeFlag(source, freePars, 0)

        logLike0 = self.like()
        x0 = par.getValue()
        dx = self._find_dx(par, nsigmax, renorm, logLike0, mindelta=mindelta)
        print dx

        xvals, dlogLike, fluxes = [], [], []
        if verbosity > 1:
            print self.like.model
        #
        # Fit a quadratic to a handful of points
        #
        for i, x in enumerate(num.arange(x0, x0+nsigmax*dx, nsigmax*dx/npts)):
            xvals.append(x)
            par.setValue(x)
            self.like.syncSrcParams(source)
            self.fit(0, renorm=renorm)
            dlogLike.append(self.like() - logLike0)
            fluxes.append(self.like[source].flux(emin, emax))
            if verbosity > 0:
                print i, x, dlogLike[-1], fluxes[-1]
        yfit = QuadraticFit(xvals, dlogLike)
        #
        # Extend the fit until it surpasses the desired delta
        #
        while dlogLike[-1] < delta and len(dlogLike) < 30:
            x = yfit.xval(1.1*delta)
            xvals.append(x)
            par.setValue(x)
            self.like.syncSrcParams(source)
            self.fit(0, renorm=renorm)
            dlogLike.append(self.like() - logLike0)
            fluxes.append(self.like[source].flux(emin, emax))
            yfit.add_pair(x, dlogLike[-1])
            i += 1
            if verbosity > 0:
                print i, x, dlogLike[-1], fluxes[-1]
        par.setFree(1)
        if fix_src_pars:
            self.like.setFreeFlag(source, freePars, 1)
        # Restore model parameters to original values
        for value, error, param in zip(saved_pars, saved_errors, 
                                       self.like.params()):
            param.setValue(value)
            param.setError(error)
        self._resyncPars()
        xx = ((delta - dlogLike[-2])/(dlogLike[-1] - dlogLike[-2])
              *(xvals[-1] - xvals[-2]) + xvals[-2])
        ul = ((delta - dlogLike[-2])/(dlogLike[-1] - dlogLike[-2])
              *(fluxes[-1] - fluxes[-2]) + fluxes[-2])
        self.results.append(ULResult(ul, emin, emax, delta,
                                     fluxes, dlogLike, xvals))
        # Restore value of covariance flag
        self.like.covar_is_current = covar_is_current
        return ul, xx
    def _find_dx(self, par, nsigmax, renorm, logLike0, niter=3, factor=2,
                 mindelta=1e-2):
        """Find an initial dx such that the change in -log-likelihood 
        evaluated at x0 + dx (dlogLike) is larger than mindelta.  A very 
        small or even negative value can occur if x0 is not right
        at the local minimum because of a large value of convergence
        tolerance.
        """
        x0 = par.getValue()
        dx = par.error()
        if dx == 0:
            dx = abs(par.getValue())
        for i in range(niter):
            par.setValue(x0 + dx*nsigmax)
            self.like.syncSrcParams(self.source)
            self.fit(0, renorm=renorm)
            dlogLike = self.like() - logLike0
            #print "_find_dx:", dx, par.getValue(), dlogLike
            if dlogLike > mindelta:
                break
            dx = max(abs(x0), factor*dx)
        return dx
    def _resyncPars(self):
        self.like.syncSrcParams()
    def fit(self, verbosity=0, renorm=False):
        if renorm:
            self._renorm()
            return
        try:
            self.like.optimize(verbosity)
        except RuntimeError:
            try:
                self.like.optimize(verbosity)
            except RuntimeError:
                self.like.restoreBestFit()
    def _renorm(self):
        freeNpred, totalNpred = self._npredValues()
        deficit = self.like.total_nobs() - totalNpred
        renormFactor = 1. + deficit/freeNpred
        if renormFactor < 1:
            renormFactor = 1
        srcNames = self.like.sourceNames()
        for src in srcNames:
            parameter = self.like.normPar(src)
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
            npred = self.like.NpredValue(src)
            totalNpred += npred
            if self.like.normPar(src).isFree():
                freeNpred += npred
        return freeNpred, totalNpred

class UpperLimits(dict):
    def __init__(self, like):
        dict.__init__(self)
        self.like = like
        for srcName in like.sourceNames():
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
