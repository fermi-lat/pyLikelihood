"""
Base class for Likelihood analysis Python modules.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/pyLikelihood/python/AnalysisBase.py,v 1.89 2017/08/18 00:20:22 echarles Exp $
#

import sys
import yaml
import numpy as num
import pyLikelihood as pyLike
from SrcModel import SourceModel
from LikelihoodState import LikelihoodState

try:
    from SimpleDialog import SimpleDialog, map, Param
except ImportError as message:
#    print ("Caught ImportError: ", message)
    pass

_plotter_package = 'mpl'

class AnalysisBase(object):
    def __init__(self):
        self.maxdist = 20
        self.tol = 1e-3
        self.covariance = None
        self.covar_is_current = False
        self.tolType = pyLike.ABSOLUTE
        self.optObject = None
        self.numeric_deriv = False
    def _srcDialog(self):
        paramDict = MyOrderedDict()
        paramDict['Source Model File'] = Param('file', '*.xml')
        paramDict['optimizer'] = Param('string', 'Drmngb')
        root = SimpleDialog(paramDict, title="Define Analysis Object:")
        root.mainloop()
        xmlFile = paramDict['Source Model File'].value()
        output = (xmlFile, paramDict['optimizer'].value())
        return output
    def setPlotter(self, plotter='hippo'):
        global _plotter_package
        _plotter_package = plotter
        if plotter == 'hippo':
            import hippoplotter as plot
            return plot
    def __call__(self):
        self.model.syncParams()
        return -self.logLike.value()
    def setFitTolType(self, tolType):

        '''Set the tolerance type of the fit.  Valid values of
        "tolType" are "0" for RELATIVE and "1" for ABSOLUTE.'''
        
        if tolType in (pyLike.RELATIVE, pyLike.ABSOLUTE):
            self.tolType = tolType
        else:
            raise RuntimeError("Invalid fit tolerance type. " +
                               "Valid values are 0=RELATIVE or 1=ABSOLUTE")
    def fit(self, verbosity=3, tol=None, optimizer=None,
            covar=False, optObject=None, numericDerivs=False):

        '''Perform the likelihood fit.  If "tol" is set to "None" it
        reverts to the global tolerance.  If "optimizer" is set to
        "None" it reverts to the global optimizer.  You can
        selectively calculate the covariance matrix by setting
        "covar=True".  You can also provide an optimization object via
        "optObject = myOpt" if you would like access to the optimizer
        results like the return codes after the fit (see pyLike for
        more details).  This function returns -Log(like).'''
        
        if tol is None:
            tol = self.tol
        errors = self._errors(optimizer, verbosity, tol, covar=covar,
                              optObject=optObject, numericDerivs=numericDerivs)
        return -self.logLike.value()
    def optimize(self, verbosity=3, tol=None, optimizer=None,
                 optObject=None):

        '''Optimize the current model.  You can increase the verbosity
        of the optimizer using the verbosity option (default is 3).
        If "tol" is none, it will use the global tolerance.  If
        "optimizer" is none it will use the global optimizer.  If
        "optObject" is none it will create one.  It will not replace
        the global optObject (self.optObject) with this one if it
        exists but if it is none, it will replace it with the new one.
        This function is different from the "fit" routine in that it
        does not calculate the covarience matrix.'''

        self.logLike.syncParams()
        if optimizer is None:
            optimizer = self.optimizer
        if tol is None:
            tol = self.tol
        optFactory = pyLike.OptimizerFactory_instance()
        if optObject is None:
            optFactory = pyLike.OptimizerFactory_instance()
            myOpt = optFactory.create(optimizer, self.logLike)
        else:
            myOpt = optObject
        # Preserve existing self.optObject unless optObject is not None
        if self.optObject is None or optObject is not None:
            self.optObject = myOpt
        myOpt.find_min_only(verbosity, tol, self.tolType)
    def _errors(self, optimizer=None, verbosity=0, tol=None,
                useBase=False, covar=False, optObject=None, numericDerivs=False):
        self.logLike.syncParams()
        if optimizer is None:
            optimizer = self.optimizer
        if tol is None:
            tol = self.tol
        if optObject is None:
            optFactory = pyLike.OptimizerFactory_instance()
            myOpt = optFactory.create(optimizer, self.logLike)
        else:
            myOpt = optObject
        self.optObject = myOpt
        if numericDerivs:
            myOpt.setNumericDerivFlag(numericDerivs)
        myOpt.find_min(verbosity, tol, self.tolType)
        errors = myOpt.getUncertainty(useBase)
        if covar:
            self.covariance = myOpt.covarianceMatrix()
            self.covar_is_current = True
        else:
            self.covar_is_current = False
        j = 0
        for i in range(len(self.model.params)):
            if self.model[i].isFree():
                self.model[i].setError(errors[j])
                j += 1
        return errors
    def minosError(self, *args):

        '''Evaluate the minos errors for a Minuit or NewMinuit fit.
        There are several ways to call this function:
        
           minosError(index): pass the parameter index only
           minosError(index,level): pass the parameter index and the
                                    level
           minosError(srcName,parName): pass the source name and
                                        the parameter name

        The "level" parameter is used to dynamically set a new error
        definition.  The default is suitable for a -log(like) analysis
        (1, sets the minuit level to 0.5, see
        Minuit2::FCNBase::ErrorDef).  Setting this to 2 would be
        suitable for a chi^2 analysis.'''
        
        if len(args) == 1:
            #param passed by index, no level
            return self._minosIndexError(args[0])
        if len(args) == 2 and args[0].__class__ == int:
            #param passed as index, level passed as 2nd arg
            return self._minosIndexError(args[0], args[1])
        par_index = self.par_index(args[0], args[1])
        if len(args) == 2:
            return self._minosIndexError(par_index)
        else:
            return self._minosIndexError(par_index, args[2])
    def par_index(self, srcName, parName):

        '''Returns the parameter index number in the model of the
        parameter identified by "parName" for a specific source
        identified by "srcName".'''
        
        source_names = self.sourceNames()
        par_index = -1
        for src in source_names:
            pars = pyLike.ParameterVector()
            self[src].src.spectrum().getParams(pars)
            for par in pars:
                par_index += 1
                if src == srcName and par.getName() == parName:
                    return par_index
        raise RuntimeError("Parameter %s for source %s not found."
                           % (parName, srcName))
    def _minosIndexError(self, par_index, level=1):
        if self.optObject is None:
            raise RuntimeError("To evaluate minos errors, a fit must first be "
                               + "performed using the Minuit or NewMinuit "
                               + "optimizers.")
        freeParams = pyLike.DoubleVector()
        self.logLike.getFreeParamValues(freeParams)
        pars = self.params()
        if par_index not in range(len(pars)):
            raise RuntimeError("Invalid model parameter index.")
        free_indices = {}
        ii = -1
        for i, par in enumerate(pars):
            if par.isFree():
                ii += 1
                free_indices[i] = ii
        if par_index not in free_indices.keys():
            raise RuntimeError("Cannot evaluate minos errors for a frozen "
                               + "parameter.")
        try:
            errors = self.optObject.Minos(free_indices[par_index], level)
            self.logLike.setFreeParamValues(freeParams)
            return errors
        except RuntimeError as message:
            print ("Minos error encountered for parameter %i." % par_index)
            print ("Attempting to reset free parameters.")
            self.thaw(par_index)
            self.logLike.setFreeParamValues(freeParams)
            raise RuntimeError(message)
    def getExtraSourceAttributes(self):

        '''Returns all of the extra attributes of all of the sources
        in the model.  These are any attributes that are not "funcs"
        or "src" which includes things like "name" and "type".'''
        
        source_attributes = {}
        for src in self.model.srcNames:
            source_attributes[src] = {}
            for key in self.model[src].__dict__.keys():
                if key not in ('funcs', 'src'):
                    source_attributes[src][key] = self.model[src].__dict__[key]
        return source_attributes
    def Ts(self, srcName, reoptimize=False, approx=True,
           tol=None, MaxIterations=10, verbosity=0):

        '''Computes the TS value for a source indicated by "srcName."
        If "reoptimize=True" is selected this function will reoptimize
        the model up to "MaxIterations" given the tolerance "tol"
        (default is the tolerance selected for the overall fit).  If
        "appox=True" is selected (the default) it will renormalize the
        model (see _renorm).'''
        
        saved_state = LikelihoodState(self)
        if verbosity > 0:
            print ("*** Start Ts_dl ***")
        source_attributes = self.getExtraSourceAttributes()
        self.logLike.syncParams()
        src = self.logLike.getSource(srcName)
        freeParams = pyLike.DoubleVector()
        self.logLike.getFreeParamValues(freeParams)
        # Get the number of free parameters in the baseline mode
        n_free_test = len(freeParams)
        n_free_src = len(self.freePars(srcName))
        n_free_base = n_free_test - n_free_src

        logLike1 = self.logLike.value()
        self._ts_src = self.logLike.deleteSource(srcName)
        logLike0 = self.logLike.value()

        if tol is None:
            tol = self.tol
        if reoptimize and n_free_base > 0:
            if verbosity > 0:
                print ("** Do reoptimize")
            optFactory = pyLike.OptimizerFactory_instance()
            myOpt = optFactory.create(self.optimizer, self.logLike)
            Niter = 1
            while Niter <= MaxIterations:
                try:
                    myOpt.find_min(0, tol)
                    break
                except RuntimeError as e:
                    print (e)
                if verbosity > 0:
                    print ("** Iteration :",Niter)
                Niter += 1
        else:
            if approx and n_free_base > 0:
                try:
                    self._renorm()
                except ZeroDivisionError:
                    pass
        self.logLike.syncParams()
        logLike0 = max(self.logLike.value(), logLike0)
        Ts_value = 2*(logLike1 - logLike0)
        self.logLike.addSource(self._ts_src)
        self.logLike.setFreeParamValues(freeParams)
        # Move call to saved_state.restore() here
        # to avoid issue with EblAtten spectral model, which is nested 
        # around other spectral models
        saved_state.restore()
        self.model = SourceModel(self.logLike)
        for src in source_attributes:
            self.model[src].__dict__.update(source_attributes[src])        
        self.logLike.value()
        return Ts_value
    def Ts_old(self, srcName, reoptimize=False, approx=True, tol=None):

        '''NOTE: this is the old method. Computes the TS value for a
        source indicated by "srcName."  If "reoptimize=True" is
        selected this function will reoptimize the model given the
        tolerance "tol" (default is the tolerance selected for the
        overall fit).  If "appox=True" is selected (the default) it
        will renormalize the model (see _renorm).'''
        
        source_attributes = self.getExtraSourceAttributes()
        self.logLike.syncParams()
        src = self.logLike.getSource(srcName)
        freeParams = pyLike.DoubleVector()
        self.logLike.getFreeParamValues(freeParams)
        logLike1 = self.logLike.value()
        self._ts_src = self.logLike.deleteSource(srcName)
        logLike0 = self.logLike.value()
        if tol is None:
            tol = self.tol
        if reoptimize:
            optFactory = pyLike.OptimizerFactory_instance()
            myOpt = optFactory.create(self.optimizer, self.logLike)
            myOpt.find_min_only(0, tol, self.tolType)
        else:
            if approx:
                try:
                    self._renorm()
                except ZeroDivisionError:
                    pass
        self.logLike.syncParams()
        logLike0 = max(self.logLike.value(), logLike0)
        Ts_value = 2*(logLike1 - logLike0)
        self.logLike.addSource(self._ts_src)
        self.logLike.setFreeParamValues(freeParams)
        self.model = SourceModel(self.logLike)
        #
        # reset the extra source attributes, if any
        #
        for src in source_attributes:
            self.model[src].__dict__.update(source_attributes[src])
        return Ts_value
    def flux(self, srcName, emin=100, emax=3e5, energyFlux=False):

        '''Returns the flux for a source with name "srcName" from emin
        (in MeV) to emax (in MeV).  If "energyFlux=False" it returns
        the integral flux; if True it will return the differential
        flux.'''

        if energyFlux:
            return self[srcName].energyFlux(emin, emax)
        else:
            return self[srcName].flux(emin, emax)
    def energyFlux(self, srcName, emin=100, emax=3e5):

        '''Returns the differential flux for a source with name
        "srcName" bewtween emin and emax (in MeV).'''

        return self.flux(srcName, emin, emax, True)
    def energyFluxError(self, srcName, emin=100, emax=3e5, npts=1000):

        '''Returns the error on the differential flux for a source
        with name "srcName" between emin and emax (in MeV).  "npts" is
        the number of energy points to use in the error calculation.
        '''

        return self.fluxError(srcName, emin, emax, True, npts)
    def fluxError(self, srcName, emin=100, emax=3e5, energyFlux=False,
                  npts=1000):

        '''Returns the error on the flux for a source with name
        "srcName" from emin (in MeV) to emax (in MeV).  If
        "energyFlux=False" it returns the integral flux; if True it
        will return the differential flux.'''
        
        par_index_map = {}
        indx = 0
        for src in self.sourceNames():
            parNames = pyLike.StringVector()
            self[src].src.spectrum().getFreeParamNames(parNames)
            for par in parNames:
                par_index_map["::".join((src, par))] = indx
                indx += 1
        #
        # Build the source-specific covariance matrix.
        #
        if self.covariance is None:
            raise RuntimeError("Covariance matrix has not been computed.")
        if not self.covar_is_current:
            sys.stderr.write("Warning: covariance matrix has not been " +
                             "updated in the most recent fit.\n")
        covar = num.array(self.covariance)
        if len(covar) != len(par_index_map):
            raise RuntimeError("Covariance matrix size does not match the " +
                               "number of free parameters.")
        my_covar = []
        srcpars = pyLike.StringVector()
        self[srcName].src.spectrum().getFreeParamNames(srcpars)
        pars = ["::".join((srcName, x)) for x in srcpars]
        if len(pars) == 0:
            # All parameters are fixed so return zero
            return 0
        for xpar in pars:
            ix = par_index_map[xpar]
            my_covar.append([covar[ix][par_index_map[ypar]] for ypar in pars])
        my_covar = num.array(my_covar)

        if energyFlux:
            partials = num.array([self[srcName].energyFluxDeriv(x, emin,
                                                                emax, npts) 
                                  for x in srcpars])
        else:
            partials = num.array([self[srcName].fluxDeriv(x, emin, emax, npts) 
                                  for x in srcpars])

        return num.sqrt(num.dot(partials, num.dot(my_covar, partials)))
    def setSpectrum(self, srcName, functionName):

        '''Set the spectral shape of a source identified by "srcName".
        The "functionName" is a string that must be one of the
        avaialble spectral functions (i.e. PowerLaw, PowerLaw2 etc.).
        You can also pass a spectrum object (see the addSource
        docString for more details).  The spectral parameters of this
        new model will be set to defaults which are probably not what
        you want them to be.'''
        
        source_attributes = self.getExtraSourceAttributes()
        src = self.logLike.getSource(srcName)
        src.setSpectrum(functionName)
        self.syncSrcParams(srcName)
        self._setSourceAttributes(source_attributes)
    def deleteSource(self, srcName):

        '''Removes a source with name "srcName" from the model.  It
        returns this source object so you can save it and use it
        later.'''
        
        source_attributes = self.getExtraSourceAttributes()
        src = self.logLike.deleteSource(srcName)
        self._setSourceAttributes(source_attributes)
        return src
    def addSource(self, src):

        '''Add a source to the active model.  You should pass a source
        object to this function.  Example:

        > test_src = pyLike.PointSource(0, 0, like.observation.observation)
        > pl = pyLike.SourceFactory_funcFactory().create("PowerLaw")
        > pl.setParamValues((1, -2, 100))
        > indexPar = pl.getParam("Index")
        > indexPar.setBounds(-3.5, -1)
        > pl.setParam(indexPar)
        > prefactor = pl.getParam("Prefactor")
        > prefactor.setBounds(1e-10, 1e3)
        > prefactor.setScale(1e-9)
        > pl.setParam(prefactor)
        > test_src.setSpectrum(pl)
        > test_src.setName("testSource")
        > test_src.setDir(193.45,-5.83,True,False)
        > like.addSource(test_src)

        You could also use the delete source function to return a
        fully formed source object and modify the parameters of that.
        '''
        
        source_attributes = self.getExtraSourceAttributes()
        self.logLike.addSource(src)
        self._setSourceAttributes(source_attributes)
    def mergeSources(self,compName,sourceNames,specFuncName):
        '''Merge a set of sources into a single composite source'''
        sv = pyLike.StringVector()
        for sn in sourceNames:
            sv.push_back(sn)
        source_attributes = self.getExtraSourceAttributes()
        comp = self.logLike.mergeSources(compName,sv,specFuncName)                
        self._setSourceAttributes(source_attributes)
        return comp
    def splitCompositeSource(self,compName):
        '''break apart a composite source and return a tuple with 
        the names of new sources and the spectral function'''
        sv = pyLike.StringVector()
        specFunc = self.logLike.splitCompositeSource(compName,sv)
        l = [sv[i] for i in range(sv.size())]
        return (l,specFunc)
    def _setSourceAttributes(self, source_attributes):
        self.model = SourceModel(self.logLike)
        for item in source_attributes:
            if self.model[item] is not None:
                self.model[item].__dict__.update(source_attributes[item])
    def writeCountsSpectra(self, outfile='counts_spectra.fits', nee=21):

        '''Writes a FITS file with the name "outfile" that contains
        the counts spectra of all of the sources in the active model.
        This is the same file that is written out by the balistic
        gtlike program.'''
        
        counts = pyLike.CountsSpectra(self.logLike)
        try:
            emin, emax = self.observation.observation.roiCuts().getEnergyCuts()
            counts.setEbounds(emin, emax, nee)
        except:
            pass
        counts.writeTable(outfile)
    def _renorm(self, factor=None):
        if factor is None:
            freeNpred, totalNpred = self._npredValues()
            deficit = sum(self.nobs) - totalNpred
            self.renormFactor = 1. + deficit/freeNpred
        else:
            self.renormFactor = factor
        if self.renormFactor < 1:
            self.renormFactor = 1
        srcNames = self.sourceNames()
        for src in srcNames:
            parameter = self.normPar(src)
            if parameter.isFree() and self._isDiffuseOrNearby(src):
                oldValue = parameter.getValue()
                newValue = oldValue*self.renormFactor
                # ensure new value is within parameter bounds
                xmin, xmax = parameter.getBounds()
                if xmin <= newValue and newValue <= xmax:
                    parameter.setValue(newValue)
    def _npredValues(self):
        srcNames = self.sourceNames()
        freeNpred = 0
        totalNpred = 0
        for src in srcNames:
            npred = self.logLike.NpredValue(src)
            totalNpred += npred
            if self.normPar(src).isFree() and self._isDiffuseOrNearby(src):
                freeNpred += npred
        return freeNpred, totalNpred
    def _isDiffuseOrNearby(self, srcName):
        if (self[srcName].src.getType() in ['Diffuse','Composite'] or 
            self._ts_src.getType() in ['Diffuse','Composite']):
            return True
        elif self._separation(self._ts_src, self[srcName].src) < self.maxdist:
            return True
        return False
    def _separation(self, src1, src2):
        dir1 = pyLike.PointSource_cast(src1).getDir()
        dir2 = pyLike.PointSource_cast(src2).getDir()
        return dir1.difference(dir2)*180./num.pi
    def saveCurrentFit(self):

        '''Saves the active fit parameter values if this fit happens
        to have a better log likelihood value than the one currently
        saved.  If it does, it replaces the saved fit with the active
        one.'''
        
        self.logLike.saveCurrentFit()
    def restoreBestFit(self):

        '''Restores the previously saved fit values saved via the
        "saveCurrentFit" function.'''
        
        self.logLike.restoreBestFit()
    def NpredValue(self, src, weighted=False):
        '''Returns the number of predicted counts for a source.'''
        return self.logLike.NpredValue(src,weighted)
    def total_nobs(self,weighted=False):
        '''Returns the total number of observed counts in the RoI.'''
        if weighted:
            return sum(self.nobs_wt)
        else:
            return sum(self.nobs)
    def syncSrcParams(self, src=None):

        '''Synchronizes the parameters of a source (identified by
        "src") with the active model.  This is useful if you add or
        delete a source from the model and want to reevaluate the log
        likelihood values.'''
        
        if src is not None:
            self.logLike.syncSrcParams(src)
        else:
            for src in self.sourceNames():
                self.logLike.syncSrcParams(src)
    def sourceNames(self):
        '''Returns a tuple that contains all of the source names in the model'''
        srcNames = pyLike.StringVector()
        self.logLike.getSrcNames(srcNames)
        return tuple(srcNames)
    def oplot(self, color=None):
        self.plot(oplot=1, color=color)
    def _importPlotter(self):
        try:
            if _plotter_package == 'root':
                from RootPlot import RootPlot
                self.plotter = RootPlot    
            elif _plotter_package == 'hippo':
                try:
                    from HippoPlot import HippoPlot
                    self.plotter = HippoPlot
                except ImportError:
                    print ("Failed importing Hippoplot.  Defaulting to MatPlotLib.")
                    from MPLPlot import MPLPlot
                    self.plotter = MPLPlot        
            elif _plotter_package == 'mpl':
                    from MPLPlot import MPLPlot
                    self.plotter = MPLPlot
        except ImportError:
            raise RuntimeError ("Sorry plotting is not available using %s.\n"
                                 % _plotter_package +
                                 "Use setPlotter to try a different plotter")
    def plot(self, oplot=0, color=None, omit=(), symbol='line', weighted=False):
        self._importPlotter()
        if oplot == 0:
            self.spectralPlot = self._plotData(weighted=weighted)
            if color is None:
                color = 'black'
        else:
            if color is None:
                color = 'red'
        srcNames = self.sourceNames()
        total_counts = None
        for src in srcNames:
            if total_counts is None:
                total_counts = self._plotSource(src, color=color, 
                                                show=(src not in omit), weighted=weighted)
            else:
                total_counts += self._plotSource(src, color=color, 
                                                 show=(src not in omit), weighted=weighted)
        self.spectralPlot.overlay(self.e_vals, total_counts, color=color,
                                  symbol=symbol)
        self._plotResiduals(total_counts, oplot=oplot, color=color, weighted=weighted)
    def _plotResiduals(self, model, nobs=None, oplot=0, color='black', weighted=False):
        if nobs is None:
            if weighted:
                nobs = self.nobs_wt
            else:
                nobs = self.nobs
        resid = (nobs - model)/model
        resid_err = num.sqrt(nobs)/model
        print ("Resid ", num.sum(nobs), model.sum(), resid.sum())
        if oplot and hasattr(self, 'residualPlot'):
            self.residualPlot.overlay(self.e_vals, resid, dy=resid_err,
                                      color=color, symbol='plus')
        else:
            self.residualPlot = self.plotter(self.e_vals, resid, dy=resid_err,
                                             xtitle='Energy (MeV)',
                                             ytitle='(counts - model)/model',
                                             xlog=1, color=color,
                                             symbol='plus',
                                             xrange=self._xrange())
            zeros = num.zeros(len(self.e_vals))
            self.residualPlot.overlay(self.e_vals, zeros, symbol='dotted')
    def _plotData(self, nobs=None, weighted=False):
        if nobs is None:
            if weighted:
                nobs = self.nobs_wt
            else:
                nobs = self.nobs
            errors = num.sqrt(nobs)
        else:
            errors = []
            for ntilde, nsq in zip(nobs, num.sqrt(self.nobs)):
                if nsq == 0:
                    errors.append(0)
                else:
                    errors.append(ntilde/nsq)
        energies = self.e_vals
        print ("Data ", num.sum(nobs))
        my_plot = self.plotter(energies, nobs, dy=errors,
                               xlog=1, ylog=1, xtitle='Energy (MeV)',
                               ytitle='counts / bin', xrange=self._xrange())
        return my_plot
    def _xrange(self):
        emin = self.energies[0]
        emax = self.energies[-1]
        if int(num.log10(emin)) != int(num.log10(emax)):
            return (emin, emax)
        else:
            return None
    def _plotSource(self, srcName, color='black', symbol='line', show=True,
                    display=None, weighted=False):
        energies = self.e_vals

        model_counts = self._srcCnts(srcName, weighted=weighted)
        print ("srcName ", model_counts.sum())

        if display is None:
            display = self.spectralPlot

        if show:
            try:
                display.overlay(energies, model_counts, color=color,
                                symbol=symbol)
            except AttributeError:
                self.spectralPlot = self.plotter(energies, model_counts, xlog=1,
                                                 ylog=1, xtitle='Energy (MeV)',
                                                 ytitle='counts spectrum',
                                                 color=color, symbol=symbol)
        return model_counts
    def plotSource(self, srcName, color='black', symbol='line'):
        self._plotSource(srcName, color, symbol)
    def __repr__(self):
        return self._inputs()
    def __getitem__(self, name):
        return self.model[name]
    def __setitem__(self, name, value):
        self.model[name] = value
        self.logLike.syncSrcParams(self.model[name].srcName)
    def normPar(self, srcName):

        '''Returns the normalization paramter of a souce specified by
        "srcName" (for example, it will return the "Prefactor"
        parameter of a source described by a PowerLaw).'''
        
        return self[srcName].funcs['Spectrum'].normPar()
    def freePars(self, srcName):

        '''Returns a tuple that contains all of the free parameters
        for a specific source indicated by "srcName".'''
        
        pars = pyLike.ParameterVector()
        self[srcName].funcs['Spectrum'].getFreeParams(pars)
        return tuple([x for x in pars])
    def setFreeFlag(self, srcName, pars, value):

        '''Sets the free flag to free (value = 1) or frozen (value =
        0) for the list of parameters indicated by pars for a specific
        source indicated by srcName.  '''

        
        src_spectrum = self[srcName].funcs['Spectrum']
        for item in pars:
            src_spectrum.parameter(item.getName()).setFree(value)
    def params(self):

        '''Returns a list of all of the parameters in the active
        model.'''
        
        return self.model.params

    def nFreeParams(self):
        
        '''Count the number of free parameters in the active model.'''
        nF = 0
        for par in self.model.params:
            if par.isFree():
                nF += 1
        return nF


    def thaw(self, i):

        '''Thaws a parameter with the given parameter index.  Use the
        par_index function to determine the index number of a specific
        parameter of a specific source.'''
        
        try:
            for ii in i:
                self.model[ii].setFree(True)
        except TypeError:
            self.model[i].setFree(True)
    def freeze(self, i):

        '''Freezes a parameter with the given parameter index.  Use
        the par_index function to determine the index number of a
        specific parameter of a specific source.'''
        
        try:
            for ii in i:
                self.model[ii].setFree(False)
        except TypeError:
            self.model[i].setFree(False)
    def writeXml(self, xmlFile=None):

        '''Write out an xml representation of the active model with
        the filename xmlFile.  If xmlFile is None (the default) it
        will overwrite the global xml file (i.e. the original file).
        '''
        
        if xmlFile is None:
            xmlFile = self.srcModel
        self.logLike.writeXml(xmlFile)
        self.srcModel = xmlFile
    def scan(self, srcName, parName, xmin=0, xmax=10, npts=50,
             tol=None, optimizer=None, optObject=None,
             fix_src_pars=False, verbosity=0, renorm=False):

        '''This function scans the values of a specific parameter
        specified by "parName" of a specific source specified by
        "srcName" in the range [xmin:xmax] with a resolution of npts.
        It then optimizes the active model.  This function returns two
        arrays: the first is an array of the x values evaluated and
        the second is an array of the change in likelihood value from
        the original model at those x values.  You can also pass True
        to "fix_src_pars" to fix all of the parameters of the source
        of interest.  The other options are similar to the fit and
        optimize functions. '''
        
        saved_state = LikelihoodState(self)
        indx = self.par_index(srcName,parName)
        # Fix the normalization parameter for the scan.
        bounds = self.model[indx].getBounds()
        self.model[indx].setBounds(xmin,xmax)
        self.freeze(indx)
        logLike0 = self.__call__()
        #need to check that all parameters are not frozen, else the call
        #to optimize will segfault, and a simple function evaluation is
        #enough
        allFrozen=True
        for name in self.sourceNames():
            if len(self.freePars(name)) != 0:
                allFrozen=False
                break

        if fix_src_pars:
            freePars = self.like.freePars(srcName)
            self.setFreeFlag(srcName, freePars, 0)
            self.syncSrcParams(srcName)

        if tol is None:
            tol = self.tol
        # Scan over the range of interest
        xvals, dlogLike = [], []
        for i, x in enumerate(num.linspace(xmin, xmax, npts)):
            xvals.append(x)
            self.model[indx] = x
            self.syncSrcParams(srcName)
            if not allFrozen :
                self.optimize(verbosity, tol, optimizer, optObject)
            dlogLike.append(self.__call__() - logLike0)
            if verbosity > 1:
                print (i, x, dlogLike[-1])

        # Restore model parameters to original values
        saved_state.restore()
        self.model[indx].setBounds(bounds)

        return num.array(xvals), num.array(dlogLike)

    def addPrior(self, srcName, parName, funcname, **kwds):
        self.model.addPrior(srcName, parName, funcname, **kwds)
        self.logLike.syncParams()

    def addGaussianPrior(self, srcName, parName, mean, sigma):
        self.model.addGaussianPrior(srcName, parName, mean, sigma)
        self.logLike.syncParams()

    def removePrior(self, srcName, parName):
        retVal = self.model.removePrior(srcName, parName)
        self.logLike.syncParams()
        return retVal

    def getPriorLogValue(self, srcName, parName):
        return self.model.getPriorLogValue(srcName, parName)

    def getPriorLogDeriv(self, srcName, parName):
        return self.model.getPriorLogDeriv(srcName, parName)

    def setPriorParams(self, srcName, parName, **kwds):
        self.model.setPriorParams(srcName, parName, **kwds)
        self.logLike.syncParams() 

    def setGaussianPriorParams(self, srcName, parName, mean, sigma):
        self.model.setGaussianPriorParams(srcName, parName, mean, sigma)
        self.logLike.syncParams()                 

    def removePriors(self):
        self.model.removePriors()
        self.logLike.syncParams()
 
    def getPriors(self):
        return self.model.getPriors()

    def addPriors(self, prior_dict):
        self.model.addPriors(prior_dict)
        self.logLike.syncParams()

    def constrain_norms(self, srcNames, cov_scale=1.0):
        self.model.constrain_norms(srcNames, cov_scale)
        self.logLike.syncParams()

    def constrain_params(self, srcNames, cov_scale=1.0):
        self.model.constrain_params(srcNames, cov_scale)
        self.logLike.syncParams()

    def writePriorsYaml(self, filename):
        self.logLike.syncParams()
        prior_dict = self.model.getPriors()
        if filename is None:
            fout = sys.stdout
        else:
            fout = open(filename, 'w!')
        yaml.dump(prior_dict, fout)
        if filename is not None:
            fout.close()

    def readPriorsYaml(self, filename):
        prior_dict = yaml.load(open(filename))
        self.model.addPriors(prior_dict)
        self.logLike.syncParams()


def _quotefn(filename):
    if filename is None:
        return None
    else:
        return "'" + filename + "'"

def _null_file(filename):
    if filename == 'none' or filename == '':
        return None
    else:
        return filename

