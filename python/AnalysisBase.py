"""
Base clase for Likelihood analysis Python modules.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/pyLikelihood/python/AnalysisBase.py,v 1.9 2006/05/28 22:31:57 jchiang Exp $
#

import numarray as num
import pyLikelihood as pyLike
from SrcModel import SourceModel
from SimpleDialog import SimpleDialog, map, Param

_plotter_package = 'root'

class AnalysisBase(object):
    _normName = {"ConstantValue": "Value",
                 "BrokenPowerLaw": "Prefactor",
                 "BrokenPowerLaw2": "Integral",
                 "PowerLaw": "Prefactor",
                 "PowerLaw2": "Integral",
                 "Gaussian": "Prefactor",
                 "FileFunction": "Normalization",
                 "LogParabola": "norm"}
    def __init__(self):
        self.maxdist = 20
    def _srcDialog(self):
        paramDict = map()
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
    def __call__(self):
        return -self.logLike.value()
    def fit(self, verbosity=3, tol=1e-5, optimizer=None):
        errors = self._errors(optimizer, verbosity, tol)
        return -self.logLike.value()
    def _errors(self, optimizer=None, verbosity=0, tol=1e-5, useBase=False):
        self.logLike.syncParams()
        if optimizer is None:
            optimizer = self.optimizer
        optFactory = pyLike.OptimizerFactory_instance()
        myOpt = optFactory.create(optimizer, self.logLike)
        myOpt.find_min(verbosity, tol)
        errors = myOpt.getUncertainty(useBase)
        j = 0
        for i in range(len(self.model.params)):
            if self.model[i].isFree():
                self.model[i].setError(errors[j])
                j += 1
        return errors
    def Ts(self, srcName, reoptimize=False, approx=True):
        self.logLike.syncParams()
        src = self.logLike.getSource(srcName)
        if src.getType() == "Point":
            freeParams = pyLike.DoubleVector()
            self.logLike.getFreeParamValues(freeParams)
            logLike1 = self.logLike.value()
            self._ts_src = self.logLike.deleteSource(srcName)
            logLike0 = self.logLike.value()
            if reoptimize:
                optFactory = pyLike.OptimizerFactory_instance()
                myOpt = optFactory.create(self.optimizer, self.logLike)
                myOpt.find_min(0, 1e-5)
            else:
                if approx:
                    try:
                        self._renorm()
                    except ZeroDivisionError:
                        pass
            logLike0 = max(self.logLike.value(), logLike0)
            Ts_value = 2*(logLike1 - logLike0)
            self.logLike.addSource(self._ts_src)
            self.logLike.setFreeParamValues(freeParams)
            self.model = SourceModel(self.logLike)
            return Ts_value
    def _renorm(self, factor=None):
        if factor is None:
            freeNpred, totalNpred = self._npredValues()
            deficit = sum(self.nobs) - totalNpred
            self.renormFactor = 1. + deficit/freeNpred
        else:
            self.renormFactor = factor
        srcNames = self.sourceNames()
        for src in srcNames:
            parameter = self._normPar(src)
            if parameter.isFree() and self._isDiffuseOrNearby(src):
                oldValue = parameter.getValue()
                parameter.setValue(oldValue*self.renormFactor)
    def _npredValues(self):
        srcNames = self.sourceNames()
        freeNpred = 0
        totalNpred = 0
        for src in srcNames:
            npred = self[src].Npred()
            totalNpred += npred
            if self._normPar(src).isFree() and self._isDiffuseOrNearby(src):
                freeNpred += npred
        return freeNpred, totalNpred
    def _isDiffuseOrNearby(self, srcName):
        if self[srcName].src.getType() == 'Diffuse':
            return True
        elif self._separation(self._ts_src, self[srcName].src) < self.maxdist:
            return True
        return False
    def _separation(self, src1, src2):
        dir1 = pyLike.PointSource_cast(src1).getDir()
        dir2 = pyLike.PointSource_cast(src2).getDir()
        return dir1.difference(dir2)*180./num.pi
    def _normPar(self, src):
        spectrum = self[src].spectrum()
        funcType = spectrum.genericName()
        return spectrum.parameter(self._normName[funcType])
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
    def __getitem__(self, name):
        return self.model[name]
    def __setitem__(self, name, value):
        self.model[name] = value
    def thaw(self, i):
        try:
            for ii in i:
                self.model[ii].setFree(1)
        except TypeError:
            self.model[i].setFree(1)
    def freeze(self, i):
        try:
            for ii in i:
                self.model[ii].setFree(0)
        except TypeError:
            self.model[i].setFree(0)
    def writeXml(self, xmlFile=None):
        if xmlFile is None:
            xmlFile = self.srcModel
        self.logLike.writeXml(xmlFile)
#    def __getattr__(self, attrname):
#        return getattr(self.logLike, attrname)

def _quotefn(filename):
    if filename is None:
        return None
    else:
        return "'" + filename + "'"
