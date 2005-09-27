"""
Base clase for Likelihood analysis Python modules.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/pyLikelihood/python/AnalysisBase.py,v 1.1.1.1 2005/08/22 16:19:27 jchiang Exp $
#

import numarray as num
import pyLikelihood as pyLike
from SimpleDialog import SimpleDialog, map, Param

_plotter_package = 'root'

class AnalysisBase(object):
    def __init__(self):
        pass
    def _srcDialog(self):
        paramDict = map()
        paramDict['Source Model File'] = Param('file', '*.xml')
        paramDict['optimizer'] = Param('string', 'Minuit')
        root = SimpleDialog(paramDict, title="Define Analysis Object:")
        root.mainloop()
        xmlFile = paramDict['Source Model File'].value()
        output = (xmlFile, paramDict['optimizer'].value())
        return output
    def setPlotter(self, plotter='root'):
        global _plotter_package
        _plotter_package = plotter
    def __call__(self):
        return -self.logLike.value()
    def fit(self, verbosity=3, tol=1e-5, optimizer=None):
        errors = self._errors(optimizer, verbosity, tol)
        return -self.logLike.value()
    def _errors(self, optimizer=None, verbosity=0, tol=1e-5, useBase=False):
        self.logLike.syncParams()
        if optimizer is None:
            optimizer = self.optimizer
        myOpt = eval("self.logLike.%s()" % optimizer)
        myOpt.find_min(verbosity, tol)
        errors = myOpt.getUncertainty(useBase)
        j = 0
        for i in range(len(self.model.params)):
            if self.model[i].isFree():
                self.model[i].setError(errors[j])
                j += 1
        return errors
    def sourceNames(self):
        srcNames = pyLike.StringVector()
        self.logLike.getSrcNames(srcNames)
        return tuple(srcNames)
    def oplot(self, color=None):
        self.plot(oplot=1, color=color)
    def _importPlotter(self):
        if _plotter_package == 'root':
            from RootPlot import RootPlot
            self.plotter = RootPlot
        elif _plotter_package == 'hippo':
            from HippoPlot import HippoPlot
            self.plotter = HippoPlot
    def plot(self, oplot=0, color=None):
        try:
            self._importPlotter()
        except ImportError:
            raise RuntimeError, ("Sorry plotting is not available using %s.\n"
                                 % _plotter_package +
                                 "Use setPlotter to try a different plotter")
        if oplot == 0:
            self.spectralPlot = self._plotData()
            if color is None:
                color = 'black'
        else:
            if color is None:
                color = 'red'
        srcNames = self.sourceNames()
        total_counts = None
        for src in srcNames:
            if total_counts is None:
                total_counts = self._plotSource(src, color=color)
            else:
                total_counts += self._plotSource(src, color=color)
        self.spectralPlot.overlay(self.e_vals, total_counts, color=color,
                                  symbol='line')
        self._plotResiduals(total_counts, oplot=oplot, color=color)
    def _plotResiduals(self, model, oplot=0, color='black'):
        resid = (self.nobs - model)/model
        resid_err = num.sqrt(self.nobs)/model
        if oplot and hasattr(self, 'residualPlot'):
            self.residualPlot.overlay(self.e_vals, resid, dy=resid_err,
                                      color=color, symbol='plus')
        else:
            self.residualPlot = self.plotter(self.e_vals, resid, dy=resid_err,
                                             xtitle='Energy (MeV)',
                                             ytitle='(counts - model)/model',
                                             xlog=1, color=color,
                                             symbol='plus')
            zeros = num.zeros(len(self.e_vals))
            self.residualPlot.overlay(self.e_vals, zeros, symbol='dotted')
    def _plotData(self):
        energies = self.e_vals
        my_plot = self.plotter(energies, self.nobs, dy=num.sqrt(self.nobs),
                               xlog=1, ylog=1, xtitle='Energy (MeV)',
                               ytitle='counts / bin')
        return my_plot
    def _plotSource(self, srcName, color='black'):
        energies = self.e_vals
        model_counts = self._srcCnts(srcName)
        try:
            self.spectralPlot.overlay(energies, model_counts, color=color,
                                      symbol='line')
        except AttributeError:
            self.spectralPlot = self.plotter(energies, model_counts, xlog=1,
                                             ylog=1, xtitle='Energy (MeV)',
                                             ytitle='counts spectrum',
                                             color=color, symbol='line')
        return model_counts
    def __repr__(self):
        return self._inputs
    def thaw(self, i):
        try:
            for ii in i:
                self.model[ii].setFree(1)
        except TypeError:
            self.model[i].setFree(1)
    def freeze(self, i):
        try:
            for ii in i:
                self.model[ii].setFree(1)
        except TypeError:
            self.model[i].setFree(0)
