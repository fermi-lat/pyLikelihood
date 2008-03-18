"""
Python interface for binned likelihood.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/pyLikelihood/python/BinnedAnalysis.py,v 1.21 2008/02/08 16:44:36 jchiang Exp $
#

import sys
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
                 irfs='DC1A'):
        if srcMaps is None or expCube is None:
            srcMaps, expCube, binnedExpMap, irfs = self._obsDialog(srcMaps,
                                                                   expCube)
        self._inputs = '\n'.join(('Source maps: ' + str(srcMaps),
                                  'Exposure cube: ' + str(expCube),
                                  'Exposure map: ' + str(binnedExpMap),
                                  'IRFs: ' + str(irfs)))
        self.srcMaps = srcMaps
        self.expCube = expCube
        self.binnedExpMap =binnedExpMap
        self.irfs = irfs
        self._createObservation(srcMaps, expCube, irfs)
        if binnedExpMap is not None and binnedExpMap != "":
            pyLike.SourceMap_setBinnedExposure(binnedExpMap)
        self.countsMap = pyLike.CountsMap(srcMaps)
    def _createObservation(self, srcMaps, expCube, irfs):
        self._respFuncs = pyLike.ResponseFunctions()
        self._respFuncs.load(irfs)
        self._expMap = pyLike.ExposureMap()
        self._scData = pyLike.ScData()
        self._roiCuts = pyLike.RoiCuts()
        self._roiCuts.readCuts(srcMaps, "", False)
        self._expCube = pyLike.ExposureCube()
        self._expCube.readExposureCube(expCube)
        self._eventCont = pyLike.EventContainer(self._respFuncs,
                                                self._roiCuts,
                                                self._scData)
        self.observation = pyLike.Observation(self._respFuncs, self._scData,
                                              self._roiCuts, self._expCube,
                                              self._expMap, self._eventCont)
    def __getattr__(self, attrname):
        return getattr(self.observation, attrname)
    def __repr__(self):
        return self._inputs
    def _obsDialog(self, srcMaps, expCube):
        paramDict = map()
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
    def __init__(self, binnedData, srcModel=None, optimizer='Drmngb'):
        AnalysisBase.__init__(self)
        if srcModel is None:
            srcModel, optimizer = self._srcDialog()
        self.binnedData = binnedData
        self.srcModel = srcModel
        self.optimizer = optimizer
        self.logLike = pyLike.BinnedLikelihood(binnedData.countsMap,
                                               binnedData.observation,
                                               binnedData.srcMaps,
                                               True)
        self.logLike.initOutputStreams()
        self.logLike.readXml(srcModel, _funcFactory, False)
        self.model = SourceModel(self.logLike, srcModel)
        self.energies = num.array(self.logLike.energies())
        self.e_vals = num.sqrt(self.energies[:-1]*self.energies[1:])
        self.nobs = self.logLike.countsSpectrum();
    def _inputs(self):
        return '\n'.join((str(self.binnedData),
                          'Source model file: ' + str(self.srcModel),
                          'Optimizer: ' + str(self.optimizer)))
    def _srcCnts(self, srcName):
        srcMap = self.logLike.sourceMap(srcName)
        npreds = srcMap.npreds()
        src = self.logLike.getSource(srcName)
        cnts = []
        for k in range(len(self.energies)-1):
            emin, emax = self.energies[k:k+2]
            cnts.append(src.pixelCounts(emin, emax, npreds[k], npreds[k+1]))
        return num.array(cnts)
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

def binnedAnalysis(mode='ql', ftol=None, **pars):
    """Return a BinnedAnalysis object using the data in gtlike.par."""
    parnames = ('irfs', 'cmap', 'bexpmap', 'expcube', 'srcmdl', 'optimizer')
    pargroup = pyLike.StApp_parGroup('gtlike')
    for item in parnames:
        if not pars.has_key(item):
            if mode == 'ql':
                pargroup.Prompt(item)
            try:
                pars[item] = float(pargroup[item])
            except ValueError:
                pars[item] = pargroup[item]
    pargroup.Save()
    srcmaps = pars['cmap']
    expcube = _null_file(pars['expcube'])
    expmap = _null_file(pars['bexpmap'])
    irfs = pars['irfs']
    obs = BinnedObs(srcmaps, expcube, expmap, irfs)
    like = BinnedAnalysis(obs, pars['srcmdl'], pars['optimizer'])
    if ftol is not None:
        like.tol = ftol
    else:
        like.tol = pargroup.getDouble('ftol')
    return like
