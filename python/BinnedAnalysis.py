"""
Python interface for binned likelihood.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/ScienceTools-scons/pyLikelihood/python/BinnedAnalysis.py,v 1.55 2016/03/30 22:06:08 echarles Exp $
#

import os
import sys
import bisect
import pyLikelihood as pyLike
from SrcModel import SourceModel
from AnalysisBase import AnalysisBase, _quotefn, _null_file, num
try:
    from SimpleDialog import SimpleDialog, map, Param
except ImportError:
    pass

_funcFactory = pyLike.SourceFactory_funcFactory()

class BinnedObs(object):
    def __init__(self, srcMaps=None, expCube=None, binnedExpMap=None,
                 irfs=None, phased_expmap=None):
        if srcMaps is None or expCube is None:
            srcMaps, expCube, binnedExpMap, irfs = self._obsDialog(srcMaps,
                                                                   expCube)
        self._inputs ='\n'.join(('Source maps: ' + str(srcMaps),
                                  'Exposure cube: ' + str(expCube),
                                  'Exposure map: ' + str(binnedExpMap),
                                  'IRFs: ' + str(irfs)))
        if phased_expmap is not None:
            self._inputs += '\n %s' % phased_expmap
        self.srcMaps = srcMaps
        self.expCube = expCube
        self.binnedExpMap = binnedExpMap
        self.phased_expmap = phased_expmap
        if irfs is None or irfs == 'CALDB':
            my_cuts = pyLike.Cuts(srcMaps, "", False, True, True)
            self.irfs = my_cuts.CALDB_implied_irfs()
        else:
            self.irfs = irfs

        pyLike.AppHelpers_checkExposureMap(srcMaps, binnedExpMap)
        # EAC switch to using AppHelpers...
        self.countsMap = pyLike.AppHelpers_readCountsMap(srcMaps)
        self._createObservation(srcMaps, expCube, self.irfs)
    def _createObservation(self, srcMaps, expCube, irfs):
        self._respFuncs = pyLike.ResponseFunctions()
        self._respFuncs.load_with_event_types(irfs, "", self.srcMaps, "")
        self._expMap = pyLike.ExposureMap()
        self._scData = pyLike.ScData()
        self._roiCuts = pyLike.RoiCuts()
        self._roiCuts.readCuts(srcMaps, "", False)
        self._expCube = pyLike.ExposureCube()
        self._expCube.readExposureCube(expCube)
        self._expCube.setEfficiencyFactor(self._respFuncs.efficiencyFactor())
        self._eventCont = pyLike.EventContainer(self._respFuncs,
                                                self._roiCuts,
                                                self._scData)
        # EAC: Use AppHelpers to get the right type of BinnedExposure map
        self._bexpmap = pyLike.AppHelpers_readBinnedExposure(self.binnedExpMap)
        if self.phased_expmap is not None:
            self._phased_expmap = pyLike.WcsMap2(self.phased_expmap)
            self.observation = pyLike.Observation(self._respFuncs,
                                                  self._scData,
                                                  self._roiCuts,
                                                  self._expCube,
                                                  self._expMap,
                                                  self._eventCont,
                                                  self._bexpmap,
                                                  self._phased_expmap)
        else:
            self.observation = pyLike.Observation(self._respFuncs,
                                                  self._scData,
                                                  self._roiCuts,
                                                  self._expCube,
                                                  self._expMap,
                                                  self._eventCont,
                                                  self._bexpmap)
        self._meanPsf = pyLike.MeanPsf(self.countsMap.refDir(),
                                       self.countsMap.energies(),
                                       self.observation)
        self.observation.setMeanPsf(self._meanPsf)
    def __getattr__(self, attrname):
        return getattr(self.observation, attrname)
    def __repr__(self):
        return self._inputs
    def _obsDialog(self, srcMaps, expCube):
        paramDict = MyOrderedDict()
        if srcMaps is None:
            paramDict['srcMaps'] = Param('file', '*.fits')
        else:
            paramDict['srcMaps'] = Param('file', srcMaps)
        if expCube is None:
            paramDict['expCube'] = Param('file', '*.fits')
        else:
            paramDict['expCube'] = Param('file', expCube)
        paramDict['binnedExpMap'] = Param('file', '')
        paramDict['irfs'] = Param('string', 'DC1A')
        root = SimpleDialog(paramDict, title="Binned Analysis Elements:")
        root.mainloop()
        output = (paramDict['srcMaps'].value(),
                  paramDict['expCube'].value(),
                  paramDict['binnedExpMap'].value(),
                  paramDict['irfs'].value())
        return output
    def state(self, output=sys.stdout):
        close = False
        try:
            output = open(output, 'w')
            close = False
        except:
            pass
        output.write("from BinnedAnalysis import *\n")
        output.write(("obs = BinnedObs(srcMaps=%s, expCube=%s, " +
                      "binnedExpMap=%s, irfs='%s')\n")
                     % (_quotefn(self.srcMaps), _quotefn(self.expCube),
                        _quotefn(self.binnedExpMap), self.irfs))
        if close:
            output.close()
        
class BinnedAnalysis(AnalysisBase):
    def __init__(self, binnedData, srcModel=None, optimizer='Drmngb',
                 use_bl2=False, verbosity=0, psfcorr=True, wmap=None):
        AnalysisBase.__init__(self)
        if srcModel is None:
            srcModel, optimizer = self._srcDialog()
        self.binnedData = binnedData
        self.srcModel = srcModel
        self.optimizer = optimizer
        if wmap and wmap != "none":
            self.wmap = pyLike.WcsMap2(wmap,"")
            self.wmap.setInterpolation(False)
            self.wmap.setExtrapolation(True)
        else:
            self.wmap = None

        if use_bl2:
            self.logLike = pyLike.BinnedLikelihood2(binnedData.countsMap,
                                                    binnedData.observation,
                                                    binnedData.srcMaps,
                                                    True, psfcorr)
        else:
            if self.wmap:
                self.logLike = pyLike.BinnedLikelihood(binnedData.countsMap,
                                                       self.wmap,
                                                       binnedData.observation,
                                                       binnedData.srcMaps,
                                                       True, psfcorr)
            else:
                self.logLike = pyLike.BinnedLikelihood(binnedData.countsMap,
                                                       binnedData.observation,
                                                       binnedData.srcMaps,
                                                       True, psfcorr)

        self.verbosity = verbosity
        self.logLike.initOutputStreams()
        self.logLike.readXml(srcModel, _funcFactory, False, True, False)
        self.model = SourceModel(self.logLike, srcModel)
        self.energies = num.array(self.logLike.energies())
        self.e_vals = num.sqrt(self.energies[:-1]*self.energies[1:])
        self.nobs = self.logLike.countsSpectrum()
        self.sourceFitPlots = []
        self.sourceFitResids  = []
    def _inputs(self):
        return '\n'.join((str(self.binnedData),
                          'Source model file: ' + str(self.srcModel),
                          'Optimizer: ' + str(self.optimizer)))
    def _srcCnts(self, srcName):
        cnts = num.array(self.logLike.modelCountsSpectrum(srcName))
        return cnts
    def state(self, output=sys.stdout):
        close = False
        try:
            output = open(output, 'w')
            close = False
        except:
            pass
        self.binnedData.state(output)
        output.write(("like = BinnedAnalysis(obs, srcModel=%s, " +
                      "optimizer='%s')\n")
                     % (_quotefn(self.srcModel), self.optimizer))
        if close:
            output.close()
    def __setitem__(self, name, value):
        self.model[name] = value
        self.logLike.syncParams()
    def setEnergyRange(self, emin, emax):
        kmin = bisect.bisect(self.energies, emin) - 1
        kmax = min(bisect.bisect_left(self.energies, emax),
                   len(self.energies)-1)
        self.selectEbounds(kmin, kmax)
        if self.verbosity > 0:
            print "setting energy bounds to "
            print "%.2f  %.2f" % (self.emin, self.emax)
    def selectEbounds(self, kmin, kmax):
        self.emin = self.energies[kmin]
        self.emax = self.energies[kmax]
        self.logLike.set_klims(kmin, kmax)
    def plot(self, oplot=0, color=None, omit=(), symbol='line'):
        AnalysisBase.plot(self, oplot, color, omit, symbol)
        try:
            yrange = self.spectralPlot.getRange('y')
            self.spectralPlot.overlay([self.emin, self.emin], yrange,
                                      symbol='dotted')
            self.spectralPlot.overlay([self.emax, self.emax], yrange,
                                      symbol='dotted')
            yrange = self.residualPlot.getRange('y')
            self.residualPlot.overlay([self.emin, self.emin], yrange,
                                      symbol='dotted')
            self.residualPlot.overlay([self.emax, self.emax], yrange,
                                      symbol='dotted')
        except AttributeError:
            pass
    def plotFixed(self, color='black', symbol='line', show=True, display=None):
        if self.logLike.fixedModelUpdated():
            self.logLike.buildFixedModelWts()
        energies = self.e_vals
        model_counts = self.logLike.fixedModelSpectrum()
        if display is None:
            display = self.spectralPlot
        if show:
            try:
                display.overlay(energies, model_counts, color=color,
                                symbol=symbol)
            except AttributeError:
                self.spectralPlot = self.plotter(energies, model_counts,
                                                 xlog=1, ylog=1, 
                                                 xtitle='Energy (MeV)',
                                                 ytitle='counts spectrum',
                                                 color=color, symbol=symbol)
        return model_counts
    def plotSourceFit(self, srcName, color='black'):
        self._importPlotter()
        nobs = num.array(self.logLike.countsSpectrum(srcName, False))
        errors = []
        for ntilde, nsq in zip(nobs, num.sqrt(self.nobs)):
            if nsq == 0:
                errors.append(0)
            else:
                errors.append(ntilde/nsq)
        errors = num.array(errors)
        model = self._srcCnts(srcName)

        self.sourceFitPlots.append(self._plotData(nobs))
        self._plotSource(srcName, color=color, display=self.sourceFitPlots[-1])
        self.sourceFitPlots[-1].setTitle(srcName)

        resid = (nobs - model)/model
        resid_err = errors/model
        self.sourceFitResids.append(self.plotter(self.e_vals, resid,
                                                 dy=resid_err,
                                                 xtitle='Energy (MeV)',
                                                 ytitle='(counts-model)/model',
                                                 xlog=1, color=color,
                                                 symbol='plus',
                                                 xrange=self._xrange()))
        zeros = num.zeros(len(self.e_vals))
        self.sourceFitResids[-1].overlay(self.e_vals, zeros, symbol='dotted')
        self.sourceFitResids[-1].setTitle(srcName)
    def writeModelMap(self, outfile, outtype='CCUBE'):
        model_map = pyLike.ModelMap(self.logLike)
        model_map.writeOutputMap(outfile, outtype)

def binnedAnalysis(mode='ql', ftol=None, **pars):
    """Return a BinnedAnalysis object using the data in gtlike.par."""
    parnames = ('irfs', 'cmap', 'bexpmap', 'expcube', 'srcmdl', 'optimizer',
                'psfcorr', 'chatter')
    pargroup = pyLike.StApp_parGroup('gtlike')
    for item in parnames:
        if not pars.has_key(item):
            if mode == 'ql':
                pargroup.Prompt(item)
            try:
                pars[item] = float(pargroup[item])
            except ValueError:
                pars[item] = pargroup[item]
            if pars[item] == 'true':
                pars[item] = True
            if pars[item] == 'false':
                pars[item] = False
    pargroup.Save()
    srcmaps = pars['cmap']
    expcube = _null_file(pars['expcube'])
    expmap = _null_file(pars['bexpmap'])
    irfs = pars['irfs']
    try:
        phased_expmap = _null_file(pars['phased_expmap'])
    except KeyError:
        phased_expmap = None
    obs = BinnedObs(srcMaps=srcmaps, expCube=expcube, binnedExpMap=expmap,
                    irfs=irfs, phased_expmap=phased_expmap)
    verbosity = 0
    if pars['chatter'] > 2:
        verbosity = 1
    like = BinnedAnalysis(obs, pars['srcmdl'], pars['optimizer'], 
                          use_bl2=False, verbosity=verbosity,
                          psfcorr=pars['psfcorr'],wmap=pars['wmap'])
    if ftol is not None:
        like.tol = ftol
    else:
        like.tol = pargroup.getDouble('ftol')
    return like
