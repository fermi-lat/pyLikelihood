"""
@file UpperLimits.py

@brief Class to compute upper limits and to manage the resulting data.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/pyLikelihood/python/UpperLimits.py,v 1.27 2009/10/31 21:23:06 jchiang Exp $
#
import copy
import bisect
import pyLikelihood as pyLike
import numpy as num
from LikelihoodState import LikelihoodState

class QuadraticFit(object):
    def __init__(self, xx, yy, xmin=None):
        self.Sx = self.Sy = self.Sxy = self.Sxx = self.npts = 0
        if xmin is None:
            self.xmin = min(xx)
        else:
            self.xmin = xmin
        for x, y in zip(xx, yy):
            self.add_pair(x, y)
    def add_pair(self, x, y):
        xx = (x - self.xmin)*(x - self.xmin)
        self.Sx += xx
        self.Sy += y
        self.Sxy += xx*y
        self.Sxx += xx*xx
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
        self.normPar = self.like.normPar(source)
        self.results = []
    def compute(self, emin=100, emax=3e5, delta=2.71/2., 
                tmpfile='temp_model.xml', fix_src_pars=False,
                verbosity=1, nsigmax=2, npts=5, renorm=False,
                mindelta=1e-2):
        saved_state = LikelihoodState(self.like)
        
        # Store the value of the covariance flag
        covar_is_current = self.like.covar_is_current
        source = self.source

        # Fix the normalization parameter for the scan.
        par = self.normPar
        par.setFree(0)
        self.like.syncSrcParams(self.source)

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
            self.like.syncSrcParams(self.source)

        logLike0 = self.like()
        x0 = par.getValue()
        dx, dlogLike_est = self._find_dx(par, nsigmax, renorm, 
                                         logLike0, mindelta=mindelta)

        xvals, dlogLike, fluxes = [], [], []
        if verbosity > 1:
            print self.like.model
        #
        # Fit a quadratic to a handful of points
        #
        if delta < dlogLike_est:
            npts = max(npts, 2.*nsigmax*dx/delta)
        for i, x in enumerate(num.arange(x0, x0+nsigmax*dx, nsigmax*dx/npts)):
            xvals.append(x)
            par.setValue(x)
            self.like.syncSrcParams(source)
            self.fit(0, renorm=renorm)
            dlogLike.append(self.like() - logLike0)
            fluxes.append(self.like[source].flux(emin, emax))
            if verbosity > 0:
                print i, x, dlogLike[-1], fluxes[-1]
            if dlogLike[-1] > delta and i > 2:
                # We have already surpassed the desired delta and 
                # have sufficient points for a quadratic fit, 
                # so exit this loop.
                break
        yfit = QuadraticFit(xvals, dlogLike)
        #
        # Extend the fit until it surpasses the desired delta
        #
        while dlogLike[-1] < delta and len(dlogLike) < 30:
            x = yfit.xval(1.1*delta)
            xvals.append(x)
            try:
                par.setValue(x)
            except RuntimeError, message:
                print par
                print x
                raise RuntimeError(message)
            self.like.syncSrcParams(source)
            self.fit(0, renorm=renorm)
            dlogLike.append(self.like() - logLike0)
            fluxes.append(self.like[source].flux(emin, emax))
            yfit.add_pair(x, dlogLike[-1])
            i += 1
            if verbosity > 0:
                print i, x, dlogLike[-1], fluxes[-1]
        if fix_src_pars:
            self.like.setFreeFlag(source, freePars, 1)
            self.like.syncSrcParams(self.source)
        # Restore model parameters to original values
        saved_state.restore()
        #
        # Linear interpolation for parameter value.  Step backwards
        # from last dlogLike value to ensure the target delta is
        # bracketed.
        #
        indx = len(dlogLike) - 2
        while delta < dlogLike[indx]:
            indx -= 1
        factor = (delta - dlogLike[indx])/(dlogLike[indx+1] - dlogLike[indx])
        xx = factor*(xvals[indx+1] - xvals[indx]) + xvals[indx]
        ul = factor*(fluxes[indx+1] - fluxes[indx]) + fluxes[indx]
        self.results.append(ULResult(ul, emin, emax, delta,
                                     fluxes, dlogLike, xvals))
        # Save profile information for debugging
        self.normPars = xvals
        self.dlogLike = dlogLike
        self.normPar_prof = xx
        self.delta = delta
        # Restore value of covariance flag
        self.like.covar_is_current = covar_is_current
        return ul, xx
    def _logLike(self, xpar, renorm):
        self.normPar.setValue(xpar)
        self.like.syncSrcParams(self.source)
        self.fit(0, renorm=renorm)
        return self.like()
    def _errorEst(self, renorm, verbosity=0):
        saved_state = LikelihoodState(self.like)
        logLike0 = saved_state.negLogLike

        # Store the value of the covariance flag
        covar_is_current = self.like.covar_is_current

        par = self.normPar
        x0 = par.getValue()
        xsig = par.error()   # initial error estimate

        # Fix the normalization parameter for the scan.
        par.setFree(0)
        self.like.syncSrcParams(self.source)

        # Set the lower bound to zero
        current_bounds = par.getBounds()
        if current_bounds[0] != 0 and verbosity > 0:
            print ("Setting lower bound on normalization parameter " +
                   "to zero temporarily for upper limit calculation.")
        par.setBounds(0, current_bounds[1])

        xvals = num.arange(x0, x0 + xsig*3, (xsig*3)/10.)
        yvals = num.array([self._logLike(x, renorm) for x in xvals])
        quadfit = QuadraticFit(xvals, yvals, xmin=x0)
        intercept, slope = quadfit.fitPars()
        sigest = num.sqrt(1./slope/2.)

        saved_state.restore()
        self.like.covar_is_current = covar_is_current

        return sigest
    def bayesianUL(self, cl=0.95, nsig=10, renorm=False, 
                   emin=100, emax=3e5, npts=50,
                   verbosity=1):
        saved_state = LikelihoodState(self.like)

        logLike0 = saved_state.negLogLike
        x0 = self.normPar.getValue()
        
        errEst = self._errorEst(renorm)
        normPar_nsig = errEst*nsig

        # Store the value of the covariance flag
        covar_is_current = self.like.covar_is_current
        source = self.source

        # Fix the normalization parameter for the scan.
        par = self.normPar
        par.setFree(0)
        self.like.syncSrcParams(self.source)

        # Set the lower bound to zero
        current_bounds = par.getBounds()
        if current_bounds[0] != 0 and verbosity > 0:
            print ("Setting lower bound on normalization parameter " +
                   "to zero temporarily for upper limit calculation.")
        par.setBounds(0, current_bounds[1])

        dlogLike_plus = (self._logLike(x0 + normPar_nsig, renorm)
                         - saved_state.negLogLike)
        dlogLike_minus = (self._logLike(max(x0 - normPar_nsig, 0), renorm)
                          - saved_state.negLogLike)

        while dlogLike_plus < 10:
            normPar_nsig += 2*errEst
            dlogLike_plus = (self._logLike(x0 + normPar_nsig, renorm)
                             - saved_state.negLogLike)
            dlogLike_minus = (self._logLike(max(x0 - normPar_nsig, 0), renorm)
                              - saved_state.negLogLike)

        # Integrate from max(0, x0 - normPar_nsig)
        xmin = max(0, x0 - normPar_nsig)
        dx = (x0 + normPar_nsig - xmin)/npts
        xx, yy = [], []
        for i in range(npts+1):
            xx.append(xmin + dx*i)
            yy.append(self._logLike(xx[-1], renorm) - logLike0)
            
        # Compute likelihood = exp(-dlogLike) for integral
        x = num.array(xx)
        y = num.exp(-num.array(yy))
        integral_dist = [0]
        for i in range(len(x)-1):
            integral_dist.append(integral_dist[-1] + 
                                 (y[i+1] + y[i])/2.*(x[i+1] - x[i]))
        integral_dist = num.array(integral_dist)/integral_dist[-1]
        ii = bisect.bisect(integral_dist, cl)
        ii = min(len(integral_dist)-1, ii)
        factor = ((cl - integral_dist[ii-1])/
                  (integral_dist[ii] - integral_dist[ii-1]))
        xval = factor*(x[ii] - x[ii-1]) + x[ii-1]
        par.setValue(xval)
        self.like.syncSrcParams(self.source)
        flux = self.like[self.source].flux(emin, emax)
        
        # Restore model parameters to original values
        saved_state.restore()

        # Save profiles for debugging
        self.bayesianUL_integral = x, integral_dist, y, yy
        
        return flux, xval
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
#            par.setValue(x0 + dx*nsigmax)
#            self.like.syncSrcParams(self.source)
#            self.fit(0, renorm=renorm)
#            dlogLike = self.like() - logLike0
            dlogLike = self._logLike(x0 + dx*nsigmax, renorm) - logLike0
            #print "_find_dx:", dx, par.getValue(), dlogLike
            if dlogLike > mindelta:
                break
            dx = max(abs(x0), factor*dx)
        return dx, dlogLike
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
