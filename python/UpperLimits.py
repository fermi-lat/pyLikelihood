"""
@file UpperLimits.py

@brief Class to compute upper limits and to manage the resulting data.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/ScienceTools-scons/pyLikelihood/python/UpperLimits.py,v 1.33 2013/05/28 21:27:32 jchiang Exp $
#
import copy
import bisect
import pyLikelihood as pyLike
import numpy as num
from LikelihoodState import LikelihoodState

class QuadraticFit_np(object):
    """numpy.poly1d/polyfit based implemetation"""
    def __init__(self, xx, yy, xmin=None):
        self.xx = [x for x in xx]
        self.yy = [y for y in yy]
        self.pars = num.polyfit(self.xx, self.yy, 2)
    def add_pair(self, x, y):
        self.xx.append(x)
        self.yy.append(y)
        self.pars = num.polyfit(self.xx, self.yy, 2)
    def errorEst(self):
        # Estimate the 1-sigma error by computing x-value from the
        # quadratic fit that gives dy = 0.5, appropriate for a
        # log-likelihood.
        yval = 0.5 + min(self.yy)
        dx = self.xval(yval) - min(self.xx)
        return dx
    def xval(self, yval):
        a, b, c = self.pars
        if a > 0:
            c -= yval
            qq = -0.5*(b + num.sign(b)*num.sqrt(b*b - 4.*a*c))
            x1, x2 = qq/a, c/qq
            return max(x1, x2)
        else:  # extrapolate a linear fit
            a, b = num.polyfit(self.xx, self.yy, 1)
            x = (yval - b)/a
            return x
    def yval(self, xval):
        f = num.poly1d(self.pars)
        y = f(xval)
        return y

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
    def errorEst(self):
        intercept, slope = self.fitPars()
        return num.sqrt(1./slope/2.)
    def fitPars(self):
        denominator = self.npts*self.Sxx - self.Sx*self.Sx
        slope = (self.npts*self.Sxy - self.Sy*self.Sx)/denominator
        intercept = (self.Sxx*self.Sy - self.Sx*self.Sxy)/denominator
        return intercept, slope
    def xval(self, yval):
        y0, dydx = self.fitPars()
        result = num.sqrt((yval - y0)/dydx) + self.xmin
        if result != result:
            raise RuntimeError("NaN encountered in QuadraticFit.xval")
        return result
    def yval(self, xval):
        y0, dydx = self.fitPars()
        result = y0 + dydx*xval*xval
        if result != result:
            raise RuntimeError("NaN encountered in QuadraticFit.yval")
        return result

QuadFit = QuadraticFit_np
    
class ULResult(object):
    def __init__(self, value, emin, emax, delta, fluxes, dlogLike, parvalues):
        self.value = value
        self.emin, self.emax = emin, emax
        self.delta = delta
        self.fluxes, self.dlogLike, self.parvalues = fluxes,dlogLike,parvalues
    def __repr__(self):
        return ("%.2e ph/cm^2/s for emin=%.1f, emax=%.1f, delta(logLike)=%.2f"
                % (self.value, self.emin, self.emax, self.delta))

class UpperLimit(object):
    def __init__(self, like, source):
        self.like = like
        self.source = source
        self.normPar = self.like.normPar(source)
        self.indx = self.like.par_index(source, self.normPar.getName())
        self.results = []
    def compute(self, emin=100, emax=3e5, delta=2.71/2., 
                tmpfile='temp_model.xml', fix_src_pars=False,
                verbosity=1, nsigmax=2, npts=5, renorm=False,
                mindelta=1e-2, resample=False):
        saved_state = LikelihoodState(self.like)
        
        # Store the value of the covariance flag
        covar_is_current = self.like.covar_is_current
        source = self.source

        # Save the error on the normalization parameter for use in estimating
        # the step size to use in the scan.
        normPar_error = self.like[self.indx].error()

        # Fix the normalization parameter for the scan.
        self.like.freeze(self.indx)

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
            self.like.syncSrcParams(source)

        logLike0 = self.like()
        x0 = self.like[self.indx].getValue()
        dx, dlogLike_est = self._find_dx(self.normPar, normPar_error,
                                         nsigmax, renorm, 
                                         logLike0, mindelta=mindelta)
        while True:
            i, xvals, dlogLike, fluxes = \
                   self._sample_likelihood_profile(delta, dx, dlogLike_est,
                                                   nsigmax, npts, verbosity,
                                                   renorm, source, emin, emax,
                                                   logLike0, x0)
            if max(dlogLike) > 1e-2:
                break
            dx *= 10

        yfit = QuadFit(xvals, dlogLike)
        #
        # Extend the fit until it surpasses the desired delta
        #
        while dlogLike[-1] < delta and len(dlogLike) < 30:
            x = yfit.xval(1.1*delta)
            xvals.append(x)
            try:
                self.like[self.indx] = x
            except RuntimeError, message:
                print (x)
                raise RuntimeError(message)
            self.fit(0, renorm=renorm)
            dlogLike.append(self.like() - logLike0)
            fluxes.append(self.like[source].flux(emin, emax))
            yfit.add_pair(x, dlogLike[-1])
            i += 1
            if verbosity > 0:
                print (i, x, dlogLike[-1], fluxes[-1])
        if resample:
            new_xvals = num.linspace(min(xvals), max(xvals), len(xvals))
            new_dlogLike = []
            new_fluxes = []
            for i, x in enumerate(new_xvals):
                try:
                    self.like[self.indx] = x
                except RuntimeError, message:
                    print (x)
                    raise RuntimeError(message)
                self.fit(0, renorm=renorm)
                new_dlogLike.append(self.like() - logLike0)
                new_fluxes.append(self.like[source].flux(emin, emax))
                if verbosity > 0:
                    print (i, x, new_dlogLike[-1], new_fluxes[-1])
            xvals = new_xvals
            dlogLike = new_dlogLike
            fluxes = new_fluxes
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
    def scan(self, xmin=0, xmax=10, npts=50,
             fix_src_pars=False, verbosity=1, renorm=False):
        saved_state = LikelihoodState(self.like)
        source = self.source

        # Fix the normalization parameter for the scan.
        self.like.freeze(self.indx)
        logLike0 = self.like()

        if fix_src_pars:
            freePars = self.like.freePars(source)
            self.like.setFreeFlag(source, freePars, 0)
            self.like.syncSrcParams(source)

        # Scan over the range of interest
        xvals, dlogLike = [], []
        for i, x in enumerate(num.linspace(xmin, xmax, npts)):
            xvals.append(x)
            self.like[self.indx] = x
            self.fit(0, renorm=renorm)
            dlogLike.append(self.like() - logLike0)
            if verbosity > 0:
                print (i, x, dlogLike[-1])

        # Restore model parameters to original values
        saved_state.restore()

        # Save values of the scan
        self.scanPars = xvals
        self.scanLike = dlogLike
        return xvals, dlogLike
    def _logLike(self, xpar, renorm):
        xmin, xmax = self.like[self.indx].getBounds()
        if xpar < xmin or xpar > xmax:
            raise RuntimeError("Attempt to set parameter value outside bounds.")
        self.like[self.indx] = xpar
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
        self.like.freeze(self.indx)

        # Set the lower bound to zero
        current_bounds = par.getBounds()
        if current_bounds[0] != 0 and verbosity > 0:
            print ("Setting lower bound on normalization parameter " +
                   "to zero temporarily for upper limit calculation.")
        self.like[self.indx].setBounds(0, current_bounds[1])

        xvals = num.arange(x0, x0 + xsig*3, (xsig*3)/10.)
        yvals = num.array([self._logLike(x, renorm) for x in xvals])
        quadfit = QuadFit(xvals, yvals, xmin=x0)
        sigest = quadfit.errorEst()

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
        self.like.freeze(self.indx)

        # Set the lower bound to zero
        current_bounds = self.normPar.getBounds()
        if current_bounds[0] != 0 and verbosity > 0:
            print ("Setting lower bound on normalization parameter " +
                   "to zero temporarily for upper limit calculation.")
        self.like[self.indx].setBounds(0, current_bounds[1])

        if x0 + normPar_nsig > current_bounds[1]:
            normPar_nsig = current_bounds[1] - x0

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
        self.like[self.indx] = xval
        flux = self.like[self.source].flux(emin, emax)
        
        # Restore model parameters to original values
        saved_state.restore()

        # Save profiles for debugging
        self.bayesianUL_integral = x, integral_dist, y, yy
        
        return flux, xval
    def _sample_likelihood_profile(self, delta, dx, dlogLike_est,
                                   nsigmax, npts, verbosity, renorm, source,
                                   emin, emax, logLike0, x0):
        xvals, dlogLike, fluxes = [], [], []
        if verbosity > 1:
            print (self.like.model)
        #
        # Fit a quadratic to a handful of points
        #
        if delta < dlogLike_est:
            npts = max(npts, 2.*nsigmax*dx/delta)
        for i, x in enumerate(num.arange(x0, x0+nsigmax*dx, nsigmax*dx/npts)):
            xvals.append(x)
            self.like[self.indx] = x
            self.fit(0, renorm=renorm)
            dlogLike.append(self.like() - logLike0)
            fluxes.append(self.like[source].flux(emin, emax))
            if verbosity > 0:
                print (i, x, dlogLike[-1], fluxes[-1])
            if dlogLike[-1] > delta and i > 2:
                # We have already surpassed the desired delta and 
                # have sufficient points for a quadratic fit, 
                # so exit this loop.
                break
        return i, xvals, dlogLike, fluxes
    def _find_dx(self, par, par_error, nsigmax, renorm, logLike0, 
                 niter=3, factor=2, mindelta=1e-2):
        """Find an initial dx such that the change in -log-likelihood 
        evaluated at x0 + dx (dlogLike) is larger than mindelta.  A very 
        small or even negative value can occur if x0 is not right
        at the local minimum because of a large value of convergence
        tolerance.
        """
        x0 = par.getValue()
        dx = par_error
        if dx == 0:
            dx = abs(par.getValue())
        for i in range(niter):
            dlogLike = self._logLike(x0 + dx*nsigmax, renorm) - logLike0
            #print ("_find_dx:", dx, par.getValue(), dlogLike)
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
    print (ul['point source 0'].compute(renorm=True))
    results = ul['point source 0'].results[0]
    plot.scatter(results.parvalues, results.dlogLike, xname='par value',
                 yname='dlogLike')
    plot.hline(2.71/2)
