# -*-mode:python; mode:font-lock;-*-
"""
@file IntegralUpperLimits.py

@brief Function to calculate upper limits by integrating Likelihood function
       to given \"probability\" level.

@author Stephen Fegan <sfegan@llr.in2p3.fr>

$Id: IntegralUpperLimit.py 884 2009-07-13 06:46:53Z sfegan $

See help for IntegralUpperLimits.calc for full details.
"""

import UnbinnedAnalysis
import scipy.integrate
import scipy.interpolate
import scipy.optimize
import scipy.stats
import math
from LikelihoodState import LikelihoodState

# These functions added 2009-04-01 to make better initial guesses for
# nuisance parameters by extrapolating them from previous iterations.
# This makes Minuit quicker (at least when using strategy 0)

def _guess_nuisance(x, like, cache):
    """Internal function which guesses the value of a nuisance
    parameter before the optimizer is called by interpolating from
    previously found values. Not intended for use outside of this
    package."""
    X = cache.keys()
    X.sort()
    if len(X)<2 or x>max(X) or x<min(X):
        return
    icache = 0
    for iparam in range(len(like.model.params)):
        if(like.model[iparam].isFree()):
            Y = []
            for ix in X: Y.append(cache[ix][icache])
            # Simple interpolation is best --- DO NOT use splines!
            p = scipy.interpolate.interp1d(X,Y)(x).item()
            limlo, limhi = like.model[iparam].getBounds()
            p = max(limlo, min(p, limhi))
            like.model[iparam].setValue(p)
            like.logLike.syncSrcParams(like[iparam].srcName)
            icache += 1

def _cache_nuisance(x, like, cache):
    """Internal function which caches the values of the nuisance
    parameters found after optimization so that they can be used
    again. Not intended for use outside of this package."""
    params = []
    for iparam in range(len(like.model.params)):
        if(like.model[iparam].isFree()):
            params.append(like.model[iparam].value())
    cache[x] = params

def _loglike(x, like, par, srcName, offset, verbose, no_optimizer,
             nuisance_cache):
    """Internal function used by the SciPy integrator and root finder
    to evaluate the likelihood function. Not intended for use outside
    of this package."""

    # Optimizer uses verbosity level one smaller than given here
    optverbose = max(verbose-1, 0)

    par.setFree(0)
    par.setValue(x)
    like.logLike.syncSrcParams(srcName)

    # This flag skips calling the optimizer - and is used in the case when
    # all parameters are frozen, since some optimizers might have problems
    # being called with nothing to do
    if not no_optimizer:
        try:
            if nuisance_cache != None:
                _guess_nuisance(x, like, nuisance_cache)
            like.fit(optverbose)
            if nuisance_cache != None:
                _cache_nuisance(x, like, nuisance_cache)
        except RuntimeError:
            like.fit(optverbose)
            if nuisance_cache != None:
                _cache_nuisance(x, like, nuisance_cache)
            pass
        pass
    
    return like.logLike.value() - offset

def _integrand(x, f_of_x, like, par, srcName, maxval, verbose=0,
               no_optimizer = False, nuisance_cache = None):
    """Internal function used by the SciPy integrator to evaluate the
    likelihood function. Not intended for use outside of this package."""

    f = math.exp(_loglike(x,like,par,srcName,maxval,verbose,no_optimizer,
                          nuisance_cache))
    f_of_x[x] = f
    if verbose:
        print "Function evaluation:", x, f
    return f

def _root(x, root_cache, like, par, srcName, subval, verbose=0,
          no_optimizer = False, nuisance_cache = None):
    """Internal function used by the SciPy root finder to evaluate the
    likelihood function. Not intended for use outside of this package."""

    if root_cache.has_key(x):
        f = root_cache[x]
    else:
        f = _loglike(x,like,par,srcName,subval,verbose,no_optimizer,
                     nuisance_cache)
        root_cache[x]=f
    if verbose:
        print "Root evaluation:", x, f
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
    point where the (linear interpolarion of the) log-likelihood
    passes desired threshold.  Not intended for use outside of this
    package."""
    return int_rep(x).item()-yseek
    
def calc(like, srcName, ul=0.95,\
         verbose=0, be_very_careful=False, freeze_all=False,
         delta_log_like_limits = 10.0, profile_optimizer = None,
         emin=100, emax=3e5):
    """Calculate an integral upper limit by direct integration.

  Description:

    Calculate an integral upper limit by integrating the likelihood
    function up to a point which contains a given fraction of the
    total probability. This is a fairly standard Bayesian approach to
    calculating upper limits, which assumes a uniform prior
    probability.  The likelihood function is not assumed to
    be distributed as chi-squared.

    This function first uses the optimizer to find the global minimum,
    then uses the scipy.integrate.quad function to integrate the
    likelihood function with respect to one of the parameters. During
    the integration, the other parameters can be frozen at their
    values found in the global minimum or optimized freely at each
    point.

  Inputs:

    like -- a binned or unbinned likelihood object which has the
            desired model. Be careful to freeze the index of the
            source for which the upper limit is being if you want to
            quote a limit with a fixed index.
    srcName -- the name of the source for which to compute the limit.
    ul -- probability level for the upper limit.
    verbose -- verbosity level. A value of zero means no output will
               be written. With a value of one the function writes
               some values describing its progress, but the optimizers
               don't write anything. Values larger than one direct the
               optimizer to produce verbose output.
    be_very_careful -- direct the integrator to be even more careful
                       in integrating the function, by telling it to
                       use a higher tolerance and to specifically pay
                       attention to the peak in the likelihood function.
                       More evaluations of the integrand will be made,
                       which WILL be slower and MAY result in a more
                       accurate limit.
    freeze_all -- freeze all other parameters at the values of the
                  global minimum.
    delta_log_like_limits -- the limits on integration is defined by
                             the region around the global maximum in
                             which the log likelihood is close enough
                             to the peak value. Too small a value will
                             mean the integral does not include a
                             significant amount of the likelihood function.
                             Too large a value may make the integrator
                             miss the peak completely and get a bogus
                             answer (although the \"be_very_careful\"
                             option will help here).
    profile_optimizer -- Alternative optimizer to use when computing the
                         profile, after the global minimum has been found.
                         Only set this if you want to use a different
                         optimizer for calculating the profile than for
                         calculating the global minimum.

  Outputs: (limit, results)

    limit -- the limit found.

    results -- a dictionary of additional results from the calculation,
               such as the value of the peak, the profile of the liklihood
               and two profile-likelihood upper-limits.
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
    optverbose = max(verbose-1, 0)

    ###########################################################################
    #
    # 1) Find the global maximum of the likelihood function using ST
    #
    ###########################################################################

    # Make sure desired parameter is free during global optimization
    src_spectrum = like[srcName].funcs['Spectrum']
    par = src_spectrum.normPar()
    par.setFree(1)
    like.logLike.syncSrcParams(srcName)

    # Perform global optimization
    if verbose:
        print "Finding global maximum"
    try:
        like.fit(optverbose)
    except RuntimeError:
        print "Optimizer failed to find global maximum, results may be wrong"
        pass
    original_optimizer = like.optimizer
    if profile_optimizer != None:
        like.optimizer = profile_optimizer

    # Store values of global fit
    maxval = like.logLike.value()
    fitval = par.getValue()
    fiterr = par.error()
    limlo, limhi = par.getBounds()
    if verbose:
        print "Maximum of %g with %s = %g +/- %g"\
              %(maxval,srcName,fitval,fiterr)

    # Freeze all other model parameters if requested (much faster!)
    if(freeze_all):
        for i in range(len(like.model.params)):
            like.model[i].setFree(0)
            like.logLike.syncSrcParams(like[i].srcName)

    # Freeze the parameter of interest
    par.setFree(0)
    like.logLike.syncSrcParams(srcName)

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

    # Search to find sensible limits of integration using SciPy Brent
    # method root finder. The tolerance is set based on the lower flux
    # limit - it's not so critical to find the integration limits with
    # high accuracy, since it they are chosen relatively arbitrarily.

    # 2009-04-16: modified to do logarithmic search before calling
    # Brent because the minimizer does not converge very well when it
    # is called alternatively at extreme ends of the flux range,
    # because the "nuisance" parameters are very far from their
    # optimal values from call to call.

    nuisance_cache = dict()
    root_cache = dict()
    subval = maxval - delta_log_like_limits
    brent_xtol = limlo*0.1

    xlo = min(fitval*0.1, fitval-(limhi-limlo)*1e-4)
    while(xlo>limlo and\
          _root(xlo,root_cache,like,par,srcName,subval,verbose,
                all_frozen,nuisance_cache)>=0):
        xlo *= 0.1
        pass
    if xlo<limlo: xlo=limlo
    if xlo>limlo or \
           _root(xlo, root_cache,like,par,srcName,subval,verbose,
                 all_frozen,nuisance_cache)<0:
        xlo = scipy.optimize.brentq(_root, xlo, fitval, xtol=brent_xtol,
                                    args = (root_cache,like,par,srcName,\
                                     subval,verbose,all_frozen,nuisance_cache))
        pass

    xhi = max(fitval*10.0, fitval+(limhi-limlo)*1e-4)
    while(xhi<limhi and\
          _root(xhi,root_cache,like,par,srcName,subval,verbose,
                all_frozen,nuisance_cache)>=0):
        xhi *= 10.0
        pass
    if xhi>limhi: xhi=limhi
    if xhi<limhi or \
           _root(xhi, root_cache,like,par,srcName,subval,verbose,
                 all_frozen,nuisance_cache)<0:
        xhi = scipy.optimize.brentq(_root, fitval, xhi, xtol=brent_xtol,
                                    args = (root_cache,like,par,srcName,\
                                     subval,verbose,all_frozen,nuisance_cache))
        pass

    if verbose:
        print "Integration bounds: %g to %g (%d fcn evals)"\
              %(xlo,xhi,len(root_cache))

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
    epsrel = (1.0-ul)*1e-3
    if be_very_careful:
        # In "be very careful" mode we explicitly tell "quad" that it
        # should examine more carefully the point at x=fitval, which
        # is the peak of the likelihood. We also use a tighter
        # tolerance value, but that seems to have a secondary effect.
        points = [ fitval ]
        epsrel = (1.0-ul)*1e-8
    
    f_of_x = dict()
    quad_ival, quad_ierr = \
          scipy.integrate.quad(_integrand, xlo, xhi,\
                               args=(f_of_x, like, par, srcName, maxval,\
                                     verbose, all_frozen ,nuisance_cache),\
                               points=points, epsrel=epsrel, epsabs=1)

    if verbose:
        print "Total integral: %g +/- %g (%d fcn evals)"\
              %(quad_ival,quad_ierr,len(f_of_x))

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
    x = f_of_x.keys()
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
    int_rep = scipy.interpolate.interp1d(x, Cint)        
    xlim_trapz = scipy.optimize.brentq(_int1droot, x[0], x[-1],
                                       args = (ul*cint, int_rep))
    ylim_trapz = int_rep(xlim_trapz).item()/cint

    # Evaluate upper limit using spline
    spl_rep = scipy.interpolate.splrep(x,y,xb=xlo,xe=xhi)
    spl_ival = scipy.interpolate.splint(xlo,xhi,spl_rep)
    xlim_spl = scipy.optimize.brentq(_splintroot, xlo, xhi, 
                                     args = (ul*spl_ival, xlo, spl_rep))
    ylim_spl = scipy.interpolate.splint(xlo,xlim_spl,spl_rep)/spl_ival

    # Test which is closest to QUADPACK adaptive method: TRAPZ or SPLINE
    if abs(spl_ival - quad_ival) < abs(trapz_ival - quad_ival):
        # Evaluate upper limit using spline
        if verbose:
            print "Using spline integral: %g (delta=%g)"\
                  %(spl_ival,abs(spl_ival/quad_ival-1))
        xlim = xlim_spl
        ylim = ylim_spl
        if verbose:
            print "Spline search: %g (P=%g)"%(xlim,ylim)
    else:
        # Evaluate upper limit using trapezoidal rule
        if verbose:
            print "Using trapezoidal integral: %g (delta=%g)"\
                  %(trapz_ival,abs(trapz_ival/quad_ival-1))
        xlim = xlim_trapz
        ylim = ylim_trapz
        if verbose:
            print "Trapezoidal search: %g (P=%g)"%(xlim,ul)

    like.optimizer = original_optimizer

    # Finally, since we have computed the profile likelihood,
    # calculate the right side of the 2-sided confidence region at the
    # UL% and 2*(UL-50)% levels under the assumption that the
    # likelihood is distributed as chi^2 of 1 DOF. Again, use the root
    # finder on a spline and linear representation of logL.

    profile_dlogL1 = -0.5*scipy.stats.chi2.isf(1-ul, 1)
    profile_dlogL2 = -0.5*scipy.stats.chi2.isf(1-2*(ul-0.5), 1)

    # The apline algorithm is prone to noise in the fitted logL,
    # especially in "be_very_careful" mode, so fall back ro a linear
    # interpolation if necessary

    spl_rep = scipy.interpolate.splrep(x,logy,xb=xlo,xe=xhi)
    spl_pflux1 = scipy.optimize.brentq(_splevroot, fitval, xhi, 
                                       args = (profile_dlogL1, spl_rep))
    spl_pflux2 = scipy.optimize.brentq(_splevroot, fitval, xhi, 
                                       args = (profile_dlogL2, spl_rep))

    int_rep = scipy.interpolate.interp1d(x,logy)
    int_pflux1 = scipy.optimize.brentq(_int1droot, max(min(x),fitval), max(x), 
                                       args = (profile_dlogL1, int_rep))
    int_pflux2 = scipy.optimize.brentq(_int1droot, max(min(x),fitval), max(x), 
                                       args = (profile_dlogL2, int_rep))

    if (2.0*abs(int_pflux1-spl_pflux1)/abs(int_pflux1+spl_pflux1) > 0.05 or \
        2.0*abs(int_pflux2-spl_pflux2)/abs(int_pflux2+spl_pflux2) > 0.05):
        if verbose:
            print "Using linear interpolation for profile UL estimate"
        profile_flux1 = int_pflux1
        profile_flux2 = int_pflux2
    else:
        if verbose:
            print "Using spline interpolation for profile UL estimate"
        profile_flux1 = spl_pflux1
        profile_flux2 = spl_pflux2

    # Pack up all the results
    results = dict(all_frozen     = all_frozen,
                   ul_frac        = ul,
                   ul_flux        = xlim,
                   ul_trapz       = xlim_trapz,
                   ul_spl         = xlim_spl,
                   profile_x      = x,
                   profile_y      = y,
                   peak_flux      = fitval,
                   peak_dflux     = fiterr,
                   peak_loglike   = maxval,
                   prof_ul_frac1  = ul,
                   prof_ul_dlogL1 = profile_dlogL1,
                   prof_ul_flux1  = profile_flux1,
                   prof_ul_frac2  = 2*(ul-0.5),
                   prof_ul_dlogL2 = profile_dlogL2,
                   prof_ul_flux2  = profile_flux2)
                   
#    return xlim, results

    # Set the parameter value that corresponds to the desired C.L.
    par.setValue(xlim)

    # Evaluate the flux corresponding to this upper limit.
    ul_value = like[srcName].flux(emin, emax)

    saved_state.restore()

    return ul_value, results

if __name__ == "__main__":
    import sys

    if(len(sys.argv)>2):
        srcName = sys.argv[1]
        base = sys.argv[2]
    elif(len(sys.argv)>1):
        srcName = sys.argv[1]
        base = '/home/sfegan/Analysis/Glast/Extragalactic/Run2_200MeV/'+srcName+'/'+srcName
    else:
        srcName = '1ES_1255+244'
        base = '/home/sfegan/Analysis/Glast/Extragalactic/Run2_200MeV/'+srcName+'/'+srcName

    obs = UnbinnedAnalysis.UnbinnedObs(eventFile = base+'_ev_roi.fits',
#                      scFile    = '/sps/glast/sfegan/data/FT2.fits',
                      scFile    = '/sps/glast/sfegan/TestSim/FT2_orbit8_v2.fits',
                      expMap    = base+'_expMap.fits',
                      expCube   = base+'_expCube.fits',
                      irfs      = 'P6_V1_DIFFUSE')

    # By using InteractiveMinuit the commands given to the Minuit
    # optimizer can be customized. There is no need to calculate error
    # estimates on the nuisance parameters while doing the profile, so
    # it's much quicker to use strategy zero and to not run the
    # "HESSE" step, whch calculates the covariance matrix. Also, for
    # increased reliability use MINIMIZE rather than MIGRAD, which
    # allows the SIMPLEX method to be called if necessary.

    # Using STR 0 and omitting HESSE speeds things up by a large
    # fraction - should also work on gttsmap and gtfindsrc :-)

    min_opt = 'InteractiveMinuit,MIN 0 $TOL,HESSE,.q'
    pro_opt = 'InteractiveMinuit,SET STR 0,MIN 0 $TOL,.q'

    # If you want to use the "be_very_careful" option, with all the
    # parameters free, then you should set the convergence tolerance
    # to be quite tight so that convergence noise doesn't spoil the
    # spline fitting. You can do that through ST or directly here if
    # you are using InteractiveMinuit (as follows)
    #
    # pro_opt = 'InteractiveMinuit,SET STR 0,MIN 0 0.01,.q'

    # If you don't have InteractiveMinuit then just use regular
    # Minuit (or whichever is your favourite optimizer)
    #
    # min_opt = 'Minuit'
    # pro_opt = None

    like = UnbinnedAnalysis.UnbinnedAnalysis(obs, base+'_model.xml',\
                                             min_opt)

    src_spectrum = like[srcName].funcs['Spectrum']
    par = src_spectrum.getParam("Index")
    if par:
        par.setFree(0)
        par.setValue(-2.0)
        like.logLike.syncSrcParams(srcName)

    ul, results = calc(like, srcName, verbose=1,
                       profile_optimizer = pro_opt,
                       be_very_careful=False, freeze_all=False)
#                       be_very_careful=True, freeze_all=False)
#                       be_very_careful=True, freeze_all=True)

    print results
    
    for i in range(len(results["profile_x"])):
        print results["profile_x"][i], results["profile_y"][i]

    print "Profile UL 1: %g (%g, %g)"%(results["prof_ul_flux1"],results["ul_frac"],results["prof_ul_dlogL1"])
    print "Profile UL 2: %g (%g, %g)"%(results["prof_ul_flux2"],results["prof_ul_frac2"],results["prof_ul_dlogL2"])
    print "UL: ",ul
