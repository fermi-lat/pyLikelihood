# -*-mode:python; mode:font-lock;-*-
"""
file IntegralUpperLimits.py

@brief Function to calculate upper limits by integrating Likelihood function
       to given \"probability\" level.

@author Stephen Fegan <sfegan@llr.in2p3.fr>

$Id: IntegralUpperLimit.py,v 1.7 2016/10/14 17:41:40 echarles Exp $

See help for IntegralUpperLimits.calc for full details.
"""

# 2011-09-27: Whenever possible call the Python Likelihood classes
# rather than the underlying C++ class - therefore, all references to
# "like.logLike" removed. This allows the code to work with
# SummedLikelihood. Fixes from Joshua Lande for transposed letters in
# a variable name which causes crashes occasionally - thanks!

# 2010-06-11: New algorithm to find integration limits. See below.
# Renamed some of the arguments for consistence with Jim's code, in
# particular "verbosity" and "cl". New code to allow the new search
# algorithm to be used to calculate chi-squared style upper limit.

# 2010-06-10: Add computation of probability for arbitrary flux
# values. Allow skipping of global minimization if user has already
# done it. Some small optimizations.

# 2009-04-01: Added nuisance cache to make better initial guesses for
# nuisance parameters by extrapolating them from previous iterations.
# This makes Minuit quicker (at least when using strategy 0)

import UnbinnedAnalysis
import scipy.integrate
import scipy.interpolate
import scipy.optimize
import scipy.stats
import math
from LikelihoodState import LikelihoodState

def _guess_nuisance(x, like, cache):
    """Internal function which guesses the value of a nuisance
    parameter before the optimizer is called by interpolating from
    previously found values. Not intended for use outside of this
    package."""
    X = list(cache.keys())
    X.sort()
    if len(X)<2:
        return
    elif x>max(X):
        _reset_nuisance(max(X), like, cache)
        return
    elif x<min(X):
        _reset_nuisance(min(X), like, cache)
        return        
    sync_name = ""
    icache = 0
    for iparam in range(len(like.model.params)):
        if sync_name != like[iparam].srcName:
            like.syncSrcParams(sync_name)
            sync_name = ""
        if(like.model[iparam].isFree()):
            Y = []
            for ix in X: Y.append(cache[ix][icache])
            # Simple interpolation is best --- DO NOT use splines!
            p = scipy.interpolate.interp1d(X,Y)(x).item()
            limlo, limhi = like.model[iparam].getBounds()
            p = max(limlo, min(p, limhi))
            like.model[iparam].setValue(p)
            sync_name = like[iparam].srcName
            icache += 1
    if sync_name != "":
        like.syncSrcParams(sync_name)

def _reset_nuisance(x, like, cache):
    """Internal function which sets the values of the nuisance
    parameters to those found in a previous iteration of the
    optimizer. Not intended for use outside of this package."""
    sync_name = ""
    icache = 0
    if x in cache:
        params = cache[x]
        for iparam in range(len(like.model.params)):
            if sync_name != like[iparam].srcName:
                like.syncSrcParams(sync_name)
                sync_name = ""
            if(like.model[iparam].isFree()):
                like.model[iparam].setValue(params[icache])
                sync_name = like[iparam].srcName
                icache += 1
        if sync_name != "":
            like.syncSrcParams(sync_name)
        return True
    return False

def _cache_nuisance(x, like, cache):
    """Internal function which caches the values of the nuisance
    parameters found after optimization so that they can be used
    again. Not intended for use outside of this package."""
    params = []
    for iparam in range(len(like.model.params)):
        if(like.model[iparam].isFree()):
            params.append(like.model[iparam].value())
    cache[x] = params

def _loglike(x, like, par, srcName, offset, verbosity, no_optimizer,
             optvalue_cache, nuisance_cache):
    """Internal function used by the SciPy integrator and root finder
    to evaluate the likelihood function. Not intended for use outside
    of this package."""

    # Optimizer uses verbosity level one smaller than given here
    optverbosity = max(verbosity-1, 0)

    par.setFree(False)
    par.setValue(x)
    like.syncSrcParams(srcName)

    # This flag skips calling the optimizer - and is used when calculating the
    # approximate function or in the case when all parameters are frozen or
    # since some optimizers might have problems being called with nothing to do
    if no_optimizer:
        return -like() - offset

    # Call the optimizer of the optimum value is not in the cache OR if
    # we fail to reset the nuisance parameters to those previously found
    optvalue = None
    if ((optvalue_cache == None) or (nuisance_cache == None) or
        (x not in optvalue_cache) or
        (_reset_nuisance(x, like, nuisance_cache) == False)):
        try:
            if(nuisance_cache != None):
                _guess_nuisance(x, like, nuisance_cache)
            like.optimize(optverbosity)
            if(nuisance_cache != None):
                _cache_nuisance(x, like, nuisance_cache)
        except RuntimeError:
            like.optimize(optverbosity)
            if(nuisance_cache != None):
                _cache_nuisance(x, like, nuisance_cache)
        optvalue = -like()
        if(optvalue_cache != None):
            optvalue_cache[x] = optvalue
    else:
        optvalue = optvalue_cache[x]
    return optvalue - offset

def _integrand(x, f_of_x, like, par, srcName, maxval, verbosity,
               no_optimizer, optvalue_cache, nuisance_cache):
    """Internal function used by the SciPy integrator to evaluate the
    likelihood function. Not intended for use outside of this package."""

    f = math.exp(_loglike(x,like,par,srcName,maxval,verbosity,no_optimizer,
                          optvalue_cache,nuisance_cache))
    f_of_x[x] = f
    if verbosity:
        print ("Function evaluation:", x, f)
    return f

def _approxroot(x, approx_cache, like, par, srcName, subval, verbosity):
    """Internal function used by the SciPy root finder to evaluate the
    approximate likelihood function. Not intended for use outside of
    this package."""

    if x in approx_cache:
        f = approx_cache[x]
    else:
        f = _loglike(x,like,par,srcName,subval,verbosity,True,None,None)
        approx_cache[x]=f
    if verbosity:
        print ("Approximate function root evaluation:", x, f)
    return f

def _root(x, like, par, srcName, subval, verbosity,
          no_optimizer, optvalue_cache, nuisance_cache):
    """Internal function used by the SciPy root finder to evaluate the
    likelihood function. Not intended for use outside of this package."""

    f = _loglike(x, like, par, srcName, subval, verbosity, no_optimizer,
                 optvalue_cache, nuisance_cache)
    if verbosity:
        print ("Exact function root evaluation:", x, f)
    return f

def _splintroot(xhi, yseek, xlo, spl_rep):
    """Internal function used by the SciPy root finder to find the
    point where integral of (spline) likelihood passes desired
    threshold.  Not intended for use outside of this package."""
    return scipy.interpolate.splint(xlo,xhi,spl_rep)-yseek

def _splevroot(x, yseek, spl_rep):
    """Internal function used by the SciPy root finder to find the
    point where the (spline of the) log-likelihood passes desired
    threshold.  Not intended for use outside of this package."""
    return scipy.interpolate.splev(x, spl_rep)-yseek

def _int1droot(x, yseek, int_rep):
    """Internal function used by the SciPy root finder to find the
    point where the (linear interpolation of the) log-likelihood
    passes desired threshold.  Not intended for use outside of this
    package."""
    return int_rep(x).item()-yseek

def _find_interval(like, par, srcName, no_optimizer,
                   maxval, fitval, limlo, limhi,
                   delta_log_like_limits = 2.71/2, verbosity = 0, tol = 0.01, 
                   no_lo_bound_search = False, nloopmax = 5,
                   optvalue_cache = dict(), nuisance_cache = dict()):
    """Internal function to search for interval of the normalization
    parameter in which the log Likelihood is larger than predefined
    value. Used to find the upper limit in the profile method and to
    find sensible limits of integration in the Bayesian method. Use
    the SciPy Brent method root finder to do the search. Use new fast
    method for up to nloopmax iterations then fall back to old method."""

    subval = maxval - delta_log_like_limits
    search_xtol = limlo*0.1
    search_ytol = tol

    # 2010-06-11: NEW and FASTER algorithm to find integration
    # limits. Instead of evaluating the real function while searching
    # for the root (which requires calling the optimizer) we now
    # evaluate an approximate function, in which all the background
    # parameters are kept constant. When we find the root (flux) of
    # the approximate function then optimize at that flux to evaluate
    # how close the real function is there. Then repeat this up to
    # "nloopmax" times, after which revert to old method if we haven't
    # converged. Each time the real function is evaluated at the root
    # of the approximate it forces the approximate function in the
    # next iteration to equal the real function at that point (since
    # the background parameters values are changed to those optimized
    # at that point) and so the real and approximate functions get
    # closer and closer around the region of the roots.

    # 2009-04-16: modified to do logarithmic search before calling
    # Brent because the minimizer does not converge very well when it
    # is called alternatively at extreme ends of the flux range,
    # because the "nuisance" parameters are very far from their
    # optimal values from call to call. THIS COMMENT IS OBSOLETED
    # BY PREVIOUS COMMENT EXCEPT IF/WHEN NEW METHOD FAILS.

    exact_root_evals = -len(optvalue_cache)
    approx_root_evals = 0
    
    temp_saved_state = LikelihoodState(like)

    # HI BOUND

    xlft = fitval
    xrgt = limhi
    xtst = fitval
    ytst = delta_log_like_limits
    iloop = 0

    while (iloop<nloopmax) and (xrgt>xlft) and (abs(ytst)>search_ytol):
        approx_cache = dict()
        approx_cache[xtst] = ytst
        if _approxroot(xrgt,approx_cache,like,par,srcName,subval,verbosity)<0:
            xtst = scipy.optimize.brentq(_approxroot, xlft, xrgt,
                                         xtol=search_xtol, 
                                    args = (approx_cache,like,par,
                                            srcName,subval,verbosity))
        else:
            xtst = xrgt
        ytst = _root(xtst, like, par,srcName, subval, verbosity,
                     no_optimizer, optvalue_cache, nuisance_cache)
        if ytst<=0: xrgt=xtst
        else: xlft=xtst
        iloop += 1
        approx_root_evals += len(approx_cache)-1
        pass
    xhi = xtst
    yhi = ytst

    if (xrgt>xlft) and (abs(ytst)>search_ytol):
        xlft = fitval
        for ix in optvalue_cache:
            if(optvalue_cache[ix]-subval>0 and ix>xlft):
                xlft = ix
        xrgt = limhi
        for ix in optvalue_cache:
            if(optvalue_cache[ix]-subval<0 and ix<xrgt):
                xrgt = ix
        if(xrgt > max(xlft*10.0, xlft+(limhi-limlo)*1e-4)):
            xtst = max(xlft*10.0, xlft+(limhi-limlo)*1e-4)            
            while(xtst<xrgt and\
                  _root(xtst, like,par, srcName, subval, verbosity,
                        no_optimizer, optvalue_cache, nuisance_cache)>=0):
                xtst *= 10.0
            if(xtst<xrgt):
                xrgt = xtst
        if xrgt>limhi: xrgt=limhi
        if xrgt<limhi or \
               _root(xrgt, like, par, srcName, subval, verbosity,
                     no_optimizer, optvalue_cache, nuisance_cache)<0:
            xhi = scipy.optimize.brentq(_root, xlft, xrgt, xtol=search_xtol,
                                        args = (like,par,srcName,\
                                                subval,verbosity,no_optimizer,
                                                optvalue_cache,nuisance_cache))
            pass
        yhi = _root(xhi, like, par, srcName, subval, verbosity,
                    no_optimizer, optvalue_cache, nuisance_cache)
        pass

    temp_saved_state.restore()

    # LO BOUND

    if(no_lo_bound_search):
        xlo = fitval
        ylo = maxval
        exact_root_evals += len(optvalue_cache)
        return [xlo, xhi, ylo, yhi, exact_root_evals, approx_root_evals]
    
    xlft = limlo
    xrgt = fitval
    xtst = fitval
    ytst = delta_log_like_limits
    iloop = 0

    while (iloop<nloopmax) and (xrgt>xlft) and (abs(ytst)>search_ytol):
        approx_cache = dict()        
        approx_cache[xtst] = ytst
        if _approxroot(xlft,approx_cache,like,par,srcName,subval,verbosity)<0:
            xtst = scipy.optimize.brentq(_approxroot, xlft, xrgt,
                                         xtol=search_xtol, 
                                         args = (approx_cache,like,par,
                                                 srcName,subval,verbosity))
        else:
            xtst = xlft
        ytst = _root(xtst, like, par, srcName, subval, verbosity,
                     no_optimizer, optvalue_cache, nuisance_cache)
        if ytst<=0: xlft=xtst
        else: xrgt=xtst
        approx_root_evals += len(approx_cache)-1
        iloop += 1
        pass
    xlo = xtst
    ylo = ytst

    if (xrgt>xlft) and (abs(ytst)>search_ytol):
        xrgt = fitval
        for ix in optvalue_cache:
            if(optvalue_cache[ix]-subval>0 and ix<xrgt):
                xrgt = ix
        xlft = limlo
        for ix in optvalue_cache:
            if(optvalue_cache[ix]-subval<0 and ix<xlft):
                xlft = ix
        if(xlft < min(xrgt*0.1, xrgt-(limhi-limlo)*1e-4)):
            xtst = min(xrgt*0.1, xrgt-(limhi-limlo)*1e-4)            
            while(xtst>xlft and\
                  _root(xtst, like,par, srcName, subval, verbosity,
                        no_optimizer, optvalue_cache, nuisance_cache)>=0):
                xtst *= 0.1
            if(xtst>xlft):
                xlft = xtst
        if xlft<limlo: xlft=limlo
        if xlft>limlo or \
               _root(xlft, like, par, srcName, subval, verbosity,
                     no_optimizer, optvalue_cache, nuisance_cache)<0:
            xlo = scipy.optimize.brentq(_root, xlft, xrgt, xtol=search_xtol,
                                        args = (like,par,srcName,\
                                                subval,verbosity,no_optimizer,
                                                optvalue_cache,nuisance_cache))
            pass
        ylo = _root(xlo, like, par, srcName, subval, verbosity,
                    no_optimizer, optvalue_cache, nuisance_cache)
        pass

    temp_saved_state.restore()

    exact_root_evals += len(optvalue_cache)
    return [xlo, xhi, ylo, yhi, exact_root_evals, approx_root_evals]

def calc(like, srcName, *args, **kwargs):
   print ("IntegralUpperLimits.calc() is deprecated, use calc_int() instead")
   return calc_int(like, srcName, *args,**kwargs)

def calc_int(like, srcName, cl=0.95, verbosity=0,
             skip_global_opt=False, be_very_careful=False, freeze_all=False,
             delta_log_like_limits = 10.0, profile_optimizer = None,
             emin=100, emax=3e5, poi_values = []):
    """Calculate an integral upper limit by direct integration.

  Description:

    Calculate an integral upper limit by integrating the likelihood
    function up to a point which contains a given fraction of the total
    probability. This is a fairly standard Bayesian approach to
    calculating upper limits, which assumes a uniform prior probability.
    The likelihood function is not assumed to be distributed as
    chi-squared.

    This function first uses the optimizer to find the global minimum,
    then uses the scipy.integrate.quad function to integrate the
    likelihood function with respect to one of the parameters. During the
    integration, the other parameters can be frozen at their values found
    in the global minimum or optimized freely at each point.

  Inputs:

    like -- a binned or unbinned likelihood object which has the
        desired model. Be careful to freeze the index of the source for
        which the upper limit is being if you want to quote a limit with a
        fixed index.

    srcName -- the name of the source for which to compute the limit.

    cl -- probability level for the upper limit.

    verbosity -- verbosity level. A value of zero means no output will
        be written. With a value of one the function writes some values
        describing its progress, but the optimizers don't write
        anything. Values larger than one direct the optimizer to produce
        verbose output.

    skip_global_opt -- if the model is already at the global minimum
        value then you can direct the integrator to skip the initial step
        to find the minimum. If you specify this option and the model is
        NOT at the global minimum your results will likely be wrong.

    be_very_careful -- direct the integrator to be even more careful
        in integrating the function, by telling it to use a higher
        tolerance and to specifically pay attention to the peak in the
        likelihood function.  More evaluations of the integrand will be
        made, which WILL be slower and MAY result in a more accurate
        limit. NOT RECOMMENDED

    freeze_all -- freeze all other parameters at the values of the
        global minimum.

    delta_log_like_limits -- the limits on integration is defined by
        the region around the global maximum in which the log likelihood
        is close enough to the peak value. Too small a value will mean the
        integral does not include a significant amount of the likelihood
        function.  Too large a value may make the integrator miss the peak
        completely and get a bogus answer (although the
        \"be_very_careful\" option will help here).

    profile_optimizer -- Alternative optimizer to use when computing
        the profile, after the global minimum has been found.  Only set
        this if you want to use a different optimizer for calculating the
        profile than for calculating the global minimum.
         
    emin, emax -- Bounds on energy range over which the flux should be
        integrated.

    poi_values -- Points of interest: values of the normalization
        parameter corresponding to fluxes of interest to the user. The
        integrator will calculate the integral of the probability
        distribution to each of these values and return them in the vector
        \"results.poi_probs\". This parameter must be a vector, and can be
        empty.

  Outputs: (limit, results)

    limit -- the flux limit found.

    results -- a dictionary of additional results from the
        calculation, such as the value of the peak, the profile of the
        likelihood and two profile-likelihood upper-limits.
  """  
    saved_state = LikelihoodState(like)

    ###########################################################################
    #
    # This function has 4 main components:
    #
    # 1) Find the global maximum of the likelihood function using ST
    # 2) Define the integration limits by finding the points at which the
    #    log likelihood has fallen by a certain amount
    # 3) Integrate the function using the QUADPACK adaptive integrator
    # 4) Calculate the upper limit by re-integrating the function using
    #    the evaluations made by the adaptive integrator. Two schemes are
    #    tried, splines to the function points and trapezoidal quadrature.
    #
    ###########################################################################

    # Optimizer uses verbosity level one smaller than given here
    optverbosity = max(verbosity-1, 0)

    ###########################################################################
    #
    # 1) Find the global maximum of the likelihood function using ST
    #
    ###########################################################################

    par = like.normPar(srcName)

    fitstat = None
    if not skip_global_opt:
        # Make sure desired parameter is free during global optimization
        par.setFree(True)
        like.syncSrcParams(srcName)

        # Perform global optimization
        if verbosity:
            print ("Finding global maximum")
        try:
            like.fit(optverbosity)
            fitstat = like.optObject.getRetCode()
            if verbosity and fitstat != 0:
                print ("Minimizer returned with non-zero code: ",fitstat)
        except RuntimeError:
            print ("Failed to find global maximum, results may be wrong")
            pass
        pass
    
    original_optimizer = like.optimizer
    if profile_optimizer != None:
        like.optimizer = profile_optimizer

    # Store values of global fit
    maxval = -like()
    fitval = par.getValue()
    fiterr = par.error()
    limlo, limhi = par.getBounds()
    # limlo should not be allowed to go down to 0
    limlo = max(limlo,0.01*fiterr,1e-4)
    if verbosity:
        print ("Maximum of %g with %s = %g +/- %g"\
              %(-maxval,srcName,fitval,fiterr))

    # Freeze all other model parameters if requested (much faster!)
    if(freeze_all):
        for i in range(len(like.model.params)):
            like.model[i].setFree(False)
            like.syncSrcParams(like[i].srcName)

    # Freeze the parameter of interest
    par.setFree(False)
    like.syncSrcParams(srcName)

    # Set up the caches for the optimum values and nuisance parameters
    optvalue_cache = dict()
    nuisance_cache = dict()
    optvalue_cache[fitval] = maxval
    _cache_nuisance(fitval, like, nuisance_cache)

    # Test if all parameters are frozen (could be true if we froze
    # them above or if they were frozen in the user's model
    all_frozen = True
    for i in range(len(like.model.params)):
        if like.model[i].isFree():
            all_frozen = False
            break

    ###########################################################################
    #
    # 2) Define the integration limits by finding the points at which the
    #    log likelihood has fallen by a certain amount
    #
    ###########################################################################

    if verbosity:
        print ("Finding integration bounds (delta log Like=%g)"\
              %(delta_log_like_limits))

    [xlo, xhi, ylo, yhi, exact_root_evals, approx_root_evals] = \
    _find_interval(like, par, srcName, all_frozen,
                   maxval, fitval, limlo, limhi,
                   delta_log_like_limits, verbosity, like.tol,
                   False, 5, optvalue_cache, nuisance_cache)

    if poi_values != None and len(poi_values)>0:
        xlo = max(min(xlo, min(poi_values)/2.0), limlo)
        xhi = min(max(xhi, max(poi_values)*2.0), limhi)

    if verbosity:
        print ("Integration bounds: %g to %g (%d full fcn evals and %d approx)"\
              %(xlo,xhi,exact_root_evals,approx_root_evals))

    profile_dlogL1 = -0.5*scipy.stats.chi2.isf(1-cl, 1)
    profile_dlogL2 = -0.5*scipy.stats.chi2.isf(1-2*(cl-0.5), 1)

    if yhi - delta_log_like_limits > profile_dlogL1:
      print ("calc_int error: parameter max", xhi, "is not large enough")
      print ("delta logLike =", yhi - delta_log_like_limits)
      return -1, {}

    ###########################################################################
    #
    # 3) Integrate the function using the QUADPACK adaptive integrator
    #
    ###########################################################################

    #
    # Do integration using QUADPACK routine from SciPy -- the "quad"
    # routine uses adaptive quadrature, which *should* spend more time
    # evaluating the function where it counts the most.
    #
    points = []
    epsrel = (1.0-cl)*1e-3
    if be_very_careful:
        # In "be very careful" mode we explicitly tell "quad" that it
        # should examine more carefully the point at x=fitval, which
        # is the peak of the likelihood. We also use a tighter
        # tolerance value, but that seems to have a secondary effect.
        points = [ fitval ]
        epsrel = (1.0-cl)*1e-8

    if verbosity:
        print ("Integrating probability distribution")

    nfneval = -len(optvalue_cache)
    f_of_x = dict()
    quad_ival, quad_ierr = \
          scipy.integrate.quad(_integrand, xlo, xhi,\
                               args = (f_of_x, like, par, srcName, maxval,\
                                       verbosity, all_frozen,
                                       optvalue_cache, nuisance_cache),\
                               points=points, epsrel=epsrel, epsabs=1)
    nfneval += len(optvalue_cache)

    if verbosity:
        print ("Total integral: %g +/- %g (%d fcn evals)"\
              %(quad_ival,quad_ierr,nfneval))

    ###########################################################################
    #
    # 4) Calculate the upper limit by re-integrating the function using
    #    the evaluations made by the adaptive integrator. Two schemes are
    #    tried, splines to the function points and trapezoidal quadrature.
    #
    ###########################################################################

    # Calculation of the upper limit requires integrating up to
    # various test points, and finding the one that contains the
    # prescribed fraction of the probability. Using the "quad"
    # function to do this by evaluating the likelihood function
    # directly would be computationally prohibitive, it is preferable
    # to use the function evaluations that have been saved in the
    # "f_of_x" variable.

    # We try 2 different integration approaches on this data:
    # trapezoidal quadrature and integration of a fitted spline, with
    # the expectation that the spline will be better, but that perhaps
    # the trapezoidal might be more robust if the spline fit goes
    # crazy. The method whose results are closest to those from "quad"
    # is picked to do the search.
    
    # Organize values computed into two vectors x & y
    x = list(f_of_x.keys())
    x.sort()
    y=[]
    logy=[]
    for xi in x:
        y.append(f_of_x[xi])
        logy.append(math.log(f_of_x[xi]))

    # Evaluate upper limit using trapezoidal rule
    trapz_ival = scipy.integrate.trapz(y,x)
    cint = 0
    Cint = [ 0 ]
    for i in range(len(x)-1):
        cint += 0.5*(f_of_x[x[i+1]]+f_of_x[x[i]])*(x[i+1]-x[i])
        Cint.append(cint)
    int_irep = scipy.interpolate.interp1d(x, Cint)
    xlim_trapz = scipy.optimize.brentq(_int1droot, x[0], x[-1],
                                       args = (cl*cint, int_irep))
    ylim_trapz = int_irep(xlim_trapz).item()/cint

    # Evaluate upper limit using spline
    spl_irep = scipy.interpolate.splrep(x,y,xb=xlo,xe=xhi)
    spl_ival = scipy.interpolate.splint(xlo,xhi,spl_irep)
    xlim_spl = scipy.optimize.brentq(_splintroot, xlo, xhi, 
                                     args = (cl*spl_ival, xlo, spl_irep))
    ylim_spl = scipy.interpolate.splint(xlo,xlim_spl,spl_irep)/spl_ival

    # Test which is closest to QUADPACK adaptive method: TRAPZ or SPLINE
    if abs(spl_ival - quad_ival) < abs(trapz_ival - quad_ival):
        # Evaluate upper limit using spline
        if verbosity:
            print ("Using spline integral: %g (delta=%g)"\
                  %(spl_ival,abs(spl_ival/quad_ival-1)))
        xlim = xlim_spl
        ylim = ylim_spl
        if verbosity:
            print ("Spline search: %g (P=%g)"%(xlim,ylim))
    else:
        # Evaluate upper limit using trapezoidal rule
        if verbosity:
            print ("Using trapezoidal integral: %g (delta=%g)"\
                  %(trapz_ival,abs(trapz_ival/quad_ival-1)))
        xlim = xlim_trapz
        ylim = ylim_trapz
        if verbosity:
            print ("Trapezoidal search: %g (P=%g)"%(xlim,cl))

    like.optimizer = original_optimizer

    ###########################################################################
    #
    # Since we have computed the profile likelihood, calculate the
    # right side of the 2-sided confidence region at the CL% and
    # 2*(CL-50)% levels under the assumption that the likelihood is
    # distributed as chi^2 of 1 DOF. Again, use the root finder on a
    # spline and linear representation of logL.
    #
    ###########################################################################

    # The spline algorithm is prone to noise in the fitted logL,
    # especially in "be_very_careful" mode, so fall back to a linear
    # interpolation if necessary

    spl_drep = scipy.interpolate.splrep(x,logy,xb=xlo,xe=xhi)
    spl_pflux1 = scipy.optimize.brentq(_splevroot, fitval, xhi, 
                                       args = (profile_dlogL1, spl_drep))
    spl_pflux2 = scipy.optimize.brentq(_splevroot, fitval, xhi, 
                                       args = (profile_dlogL2, spl_drep))

    int_drep = scipy.interpolate.interp1d(x,logy)
    int_pflux1 = scipy.optimize.brentq(_int1droot, max(min(x),fitval), max(x), 
                                       args = (profile_dlogL1, int_drep))
    int_pflux2 = scipy.optimize.brentq(_int1droot, max(min(x),fitval), max(x), 
                                       args = (profile_dlogL2, int_drep))

    if (2.0*abs(int_pflux1-spl_pflux1)/abs(int_pflux1+spl_pflux1) > 0.05 or \
        2.0*abs(int_pflux2-spl_pflux2)/abs(int_pflux2+spl_pflux2) > 0.05):
        if verbosity:
            print ("Using linear interpolation for profile UL estimate")
        profile_flux1 = int_pflux1
        profile_flux2 = int_pflux2
    else:
        if verbosity:
            print ("Using spline interpolation for profile UL estimate")
        profile_flux1 = spl_pflux1
        profile_flux2 = spl_pflux2

    ###########################################################################
    #
    # Evaluate the probabilities of the "points of interest" using the integral
    #
    ###########################################################################

    poi_probs = [];
    poi_dlogL_interp = [];
    poi_chi2_equiv = [];

    for xval in poi_values:
        dLogL = None
        if(xval >= xhi):
            pval = 1.0
        elif(xval <= xlo):
            pval = 0.0
        # Same test as above to decide between TRAPZ and SPLINE
        elif abs(spl_ival - quad_ival) < abs(trapz_ival - quad_ival):
            pval = scipy.interpolate.splint(xlo,xval,spl_irep)/spl_ival
            dlogL = scipy.interpolate.splev(xval, spl_drep)
        else:
            pval = int_irep(xval).item()/cint
            dlogL = int_drep(xval).item()                
        poi_probs.append(pval)
        poi_dlogL_interp.append(dlogL)
        poi_chi2_equiv.append(scipy.stats.chi2.isf(1-pval,1))

    ###########################################################################
    #        
    # Calculate the integral flux at the upper limit parameter value
    #
    ###########################################################################
    
    # Set the parameter value that corresponds to the desired C.L.
    par.setValue(xlim)

    # Evaluate the flux corresponding to this upper limit.
    ul_flux = like[srcName].flux(emin, emax)

    saved_state.restore()

    # Pack up all the results
    results = dict(all_frozen       = all_frozen,
                   ul_frac          = cl,
                   ul_flux          = ul_flux,
                   ul_value         = xlim,
                   ul_trapz         = xlim_trapz,
                   ul_spl           = xlim_spl,
                   int_limits       = [xlo, xhi],
                   profile_x        = x,
                   profile_y        = y,
                   peak_fitstatus   = fitstat,
                   peak_value       = fitval,
                   peak_dvalue      = fiterr,
                   peak_loglike     = maxval,
                   prof_ul_frac1    = cl,
                   prof_ul_dlogL1   = profile_dlogL1,
                   prof_ul_value1   = profile_flux1,
                   prof_ul_frac2    = 2*(cl-0.5),
                   prof_ul_dlogL2   = profile_dlogL2,
                   prof_ul_value2   = profile_flux2,
                   poi_values       = poi_values,
                   poi_probs        = poi_probs,
                   poi_dlogL_interp = poi_dlogL_interp,
                   poi_chi2_equiv   = poi_chi2_equiv,
                   flux_emin        = emin,
                   flux_emax        = emax)

    return ul_flux, results

def calc_chi2(like, srcName, cl=0.95, verbosity=0,
              skip_global_opt=False, freeze_all=False,
              profile_optimizer = None, emin=100, emax=3e5, poi_values = []):
    """Calculate an integral upper limit by the profile likelihood (chi2) method.

  Description:

    Calculate an upper limit using the likelihood ratio test, i.e. by
    supposing the Likelihood is distributed as chi-squared of one degree of
    freedom and finding the point at which the it decreases by the
    required amount to get an upper limit at a certain confidence limit.

    This function first uses the optimizer to find the global minimum,
    then uses the new root finding algorithm to find the point at which
    the Likelihood decreases by the required amount. The background
    parameters can be frozen at their values found in the global minimum
    or optimized freely at each point.

  Inputs:

    like -- a binned or unbinned likelihood object which has the
        desired model. Be careful to freeze the index of the source for
        which the upper limit is being if you want to quote a limit with a
        fixed index.

    srcName -- the name of the source for which to compute the limit.

    cl -- probability level for the upper limit.

    verbosity -- verbosity level. A value of zero means no output will
        be written. With a value of one the function writes some values
        describing its progress, but the optimizers don't write
        anything. Values larger than one direct the optimizer to produce
        verbose output.

    skip_global_opt -- if the model is already at the global minimum
        value then you can direct the integrator to skip the initial step
        to find the minimum. If you specify this option and the model is
        NOT at the global minimum your results will likely be wrong.

    freeze_all -- freeze all other parameters at the values of the
        global minimum.

    profile_optimizer -- Alternative optimizer to use when computing
        the profile, after the global minimum has been found. Only set
        this if you want to use a different optimizer for calculating the
        profile than for calculating the global minimum.

    emin, emax -- Bounds on energy range over which the flux should be
        integrated.

    poi_values -- Points of interest: values of the normalization
        parameter corresponding to fluxes of interest to the user. The
        profile likelihood be evaluated at each of these values and the
        equivalent probability under the LRT returned in the vector
        \"results.poi_probs\". This parameter must be a vector, and can be
        empty.

  Outputs: (limit, results)

    limit -- the flux limit found.

    results -- a dictionary of additional results from the calculation,
        such as the value of the peak value etc.
  """

    saved_state = LikelihoodState(like)

    ###########################################################################
    #
    # This function has 2 main components:
    #
    # 1) Find the global maximum of the likelihood function using ST
    # 2) Find the point at which it falls by the appropriate amount
    #
    ###########################################################################

    # Optimizer uses verbosity level one smaller than given here
    optverbosity = max(verbosity-1, 0)

    ###########################################################################
    #
    # 1) Find the global maximum of the likelihood function using ST
    #
    ###########################################################################

    par = like.normPar(srcName)

    fitstat = None
    if not skip_global_opt:
        # Make sure desired parameter is free during global optimization
        par.setFree(True)
        like.syncSrcParams(srcName)

        # Perform global optimization
        if verbosity:
            print ("Finding global maximum")
        try:
            like.fit(optverbosity)
            fitstat = like.optObject.getRetCode()
            if verbosity and fitstat != 0:
                print ("Minimizer returned with non-zero code: ",fitstat)
        except RuntimeError:
            print ("Failed to find global maximum, results may be wrong")
            pass
        pass
    
    original_optimizer = like.optimizer
    if profile_optimizer != None:
        like.optimizer = profile_optimizer

    # Store values of global fit
    maxval = -like()
    fitval = par.getValue()
    fiterr = par.error()
    limlo, limhi = par.getBounds()
    if verbosity:
        print ("Maximum of %g with %s = %g +/- %g"\
              %(-maxval,srcName,fitval,fiterr))

    # Freeze all other model parameters if requested (much faster!)
    if(freeze_all):
        for i in range(len(like.model.params)):
            like.model[i].setFree(False)
            like.syncSrcParams(like[i].srcName)

    # Freeze the parameter of interest
    par.setFree(False)
    like.syncSrcParams(srcName)

    # Set up the caches for the optimum values and nuisance parameters
    optvalue_cache = dict()
    nuisance_cache = dict()
    optvalue_cache[fitval] = maxval
    _cache_nuisance(fitval, like, nuisance_cache)

    # Test if all parameters are frozen (could be true if we froze
    # them above or if they were frozen in the user's model
    all_frozen = True
    for i in range(len(like.model.params)):
        if like.model[i].isFree():
            all_frozen = False
            break

    ###########################################################################
    #
    # 2) Find the point at which the likelihood has fallen by the
    #    appropriate amount
    #
    ###########################################################################

    delta_log_like = 0.5*scipy.stats.chi2.isf(1-2*(cl-0.5), 1)

    if verbosity:
        print ("Finding limit (delta log Like=%g)"\
              %(delta_log_like))

    [xunused, xlim, yunused, ylim, exact_root_evals, approx_root_evals] = \
    _find_interval(like, par, srcName, all_frozen,
                   maxval, fitval, limlo, limhi,
                   delta_log_like, verbosity, like.tol,
                   True, 5, optvalue_cache, nuisance_cache)

    if verbosity:
        print ("Limit: %g (%d full fcn evals and %d approx)"\
              %(xlim,exact_root_evals,approx_root_evals))

    ###########################################################################
    #
    # Evaluate the probabilities of the "points of interest" using the LRT
    #
    ###########################################################################
    
    poi_dlogL = [];
    poi_probs = [];
    for xval in poi_values:
        if(xval >= limhi):
            dlogL = None
            pval = 1.0
        elif(xval <= limlo):
            dlogL = None
            pval = 0.0
        else:
            dlogL = _loglike(xval, like, par, srcName, maxval, verbosity,
                             all_frozen, optvalue_cache, nuisance_cache)
            if(xval<fitval):
                pval = 0.5*(1-scipy.stats.chi2.cdf(-2*dlogL,1))
            else:
                pval = 0.5*(1+scipy.stats.chi2.cdf(-2*dlogL,1))
            if verbosity:
                print ("POI %g: Delta log Like = %g (Pr=%g)"%(xval,dlogL,pval))

        poi_probs.append(pval)
        poi_dlogL.append(dlogL)
    
    like.optimizer = original_optimizer

    ###########################################################################
    #        
    # Calculate the integral flux at the upper limit parameter value
    #
    ###########################################################################
    
    # Set the parameter value that corresponds to the desired C.L.
    par.setValue(xlim)

    # Evaluate the flux corresponding to this upper limit.
    ul_flux = like[srcName].flux(emin, emax)

    saved_state.restore()

    # Pack up all the results
    results = dict(all_frozen     = all_frozen,
                   ul_frac        = cl,
                   ul_flux        = ul_flux,
                   ul_value       = xlim,
                   ul_loglike     = maxval+ylim-delta_log_like,
                   ul_dloglike    = ylim-delta_log_like,
                   peak_fitstatus = fitstat,
                   peak_value     = fitval,
                   peak_dvalue    = fiterr,
                   peak_loglike   = maxval,
                   poi_values     = poi_values,
                   poi_probs      = poi_probs,
                   poi_dlogL      = poi_dlogL,
                   flux_emin      = emin,
                   flux_emax      = emax)

    return ul_flux, results
    

if __name__ == "__main__":
    import sys

    srcName = "EMS0001"
    obs = UnbinnedAnalysis.UnbinnedObs('ft1_roi.fits',
                                       scFile    = 'ft2.fits',
                                       expMap    = 'expMap.fits',
                                       expCube   = 'expCube.fits',
                                       irfs      = 'P6_V9_DIFFUSE')

    #min_opt = 'InteractiveMinuit,MIN 0 $TOL,HESSE,.q'
    #pro_opt = 'InteractiveMinuit,SET STR 0,MIN 0 $TOL,.q'
    min_opt = 'MINUIT'
    pro_opt = None
    
    like = UnbinnedAnalysis.UnbinnedAnalysis(obs, 'model.xml', min_opt)

    src_spectrum = like[srcName].funcs['Spectrum']
    par = src_spectrum.getParam("Index")
    if par:
        par.setFree(False)
        par.setValue(-2.0)
        like.syncSrcParams(srcName)

    ul, results = calc_int(like, srcName, verbosity=1)

    print (results)
    
    for i in range(len(results["profile_x"])):
        print (results["profile_x"][i], results["profile_y"][i])

    print ("Profile UL 1: %g (%g, %g)"%(results["prof_ul_flux1"],results["ul_frac"],results["prof_ul_dlogL1"]))
    print ("Profile UL 2: %g (%g, %g)"%(results["prof_ul_flux2"],results["prof_ul_frac2"],results["prof_ul_dlogL2"]))
    print ("UL: ",ul)
