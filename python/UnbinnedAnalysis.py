"""
Python interface for unbinned likelihood

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/pyLikelihood/python/UnbinnedAnalysis.py,v 1.11 2006/06/27 04:10:47 jchiang Exp $
#

import sys
import glob
import numarray as num
import pyLikelihood as pyLike
from SrcModel import SourceModel
from AnalysisBase import AnalysisBase, _quotefn, _null_file
from SimpleDialog import SimpleDialog, map, Param

_funcFactory = pyLike.SourceFactory_funcFactory()

def _resolveFileList(files):
    fileList = files.split(',')
    my_list = []
    for file in fileList:
        my_list.extend(glob.glob(file.strip()))
    return my_list

class UnbinnedObs(object):
    def __init__(self, eventFile=None, scFile=None, expMap=None,
                 expCube=None, irfs='DC1A', checkCuts=True, sctable='SC_DATA'):
        self.sctable = sctable
        self.checkCuts = checkCuts
        if eventFile is None and scFile is None:
            eventFile, scFile, expMap, expCube, irfs = self._obsDialog()
        if checkCuts:
            self._checkCuts(eventFile, expMap, expCube)
        self.expMap = expMap
        self.expCube = expCube
        self.irfs = irfs
        self._inputs = '\n'.join(('Event file(s): ' + str(eventFile),
                                  'Spacecraft file(s): ' + str(scFile),
                                  'Exposure map: ' + str(expMap),
                                  'Exposure cube: ' + str(expCube),
                                  'IRFs: ' + str(irfs)))
        self._respFuncs = pyLike.ResponseFunctions()
        self._respFuncs.load(irfs)
        self._expMap = pyLike.ExposureMap()
        if expMap is not None and expMap != "":
            self._expMap.readExposureFile(expMap)
        self._scData = pyLike.ScData()
        self._roiCuts = pyLike.RoiCuts()
        self._expCube = pyLike.ExposureCube()
        if expCube is not None and expCube != "":
            self._expCube.readExposureCube(expCube)
        self._eventCont = pyLike.EventContainer(self._respFuncs, self._roiCuts,
                                                self._scData)
        self.observation = pyLike.Observation(self._respFuncs, self._scData,
                                              self._roiCuts, self._expCube,
                                              self._expMap, self._eventCont)
        self._readData(scFile, eventFile)
    def _checkCuts(self, eventFile, expMap=None, expCube=None):
        if eventFile is not None:
            eventFiles = self._fileList(eventFile)
            checkCuts = pyLike.AppHelpers_checkCuts
            checkTimeCuts = pyLike.AppHelpers_checkTimeCuts
            for file in eventFiles[1:]:
                checkCuts(eventFiles[0], 'EVENTS', file, 'EVENTS', False)
            if expMap is not None and expMap != '':
                checkCuts(eventFiles, 'EVENTS', expMap, '')
            if expCube is not None and expCube != '':
                checkTimeCuts(eventFiles, 'EVENTS', expCube, 'Exposure')
    def _obsDialog(self):
        paramDict = map()
        paramDict['eventFile'] = Param('file', '*.fits')
        paramDict['scFile'] = Param('file', '*.fits')
        paramDict['expMap'] = Param('file', '')
        paramDict['expCube'] = Param('file', '')
        paramDict['irfs'] = Param('string', 'DC1A')
        root = SimpleDialog(paramDict, title="Unbinned Analysis Elements:")
        root.mainloop()
        eventFiles = _resolveFileList(paramDict['eventFile'].value())
        scFiles = _resolveFileList(paramDict['scFile'].value())
        output = (eventFiles, scFiles,
                  paramDict['expMap'].value(),
                  paramDict['expCube'].value(),
                  paramDict['irfs'].value())
        return output
    def _fileList(self, files):
        if isinstance(files, str):
            return pyLike.Util_resolveFitsFiles(files)
        else:
            return files
    def _readData(self, scFile, eventFile):
        self._readScData(scFile)
        self._readEvents(eventFile)
    def _readScData(self, scFile):
        scFiles = self._fileList(scFile)
        self._scData.readData(scFiles[0], True, self.sctable)
        for file in scFiles[1:]:
            self._scData.readData(file)
        self.scFiles = scFiles
    def _readEvents(self, eventFile):
        if eventFile is not None:
            eventFiles = self._fileList(eventFile)
            self._roiCuts.readCuts(eventFiles, 'EVENTS', False)
            for file in eventFiles:
                self._eventCont.getEvents(file)
            self.eventFiles = eventFiles
    def __getattr__(self, attrname):
        return getattr(self.observation, attrname)
    def __repr__(self):
        return self._inputs
    def state(self, output=sys.stdout):
        close = False
        try:
            output = open(output, 'w')
            close = True
        except:
            pass
        output.write("from UnbinnedAnalysis import *\n")
        output.write(("obs = UnbinnedObs(%s, %s, expMap=%s, expCube=%s, " +
                      "irfs='%s')\n") % (`self.eventFiles`, `self.scFiles`,
                                         _quotefn(self.expMap),
                                         _quotefn(self.expCube), self.irfs))
        if close:
            output.close()

class UnbinnedAnalysis(AnalysisBase):
    def __init__(self, observation, srcModel=None,  optimizer='Drmngb'):
        AnalysisBase.__init__(self)
        if srcModel is None:
            srcModel, optimizer = self._srcDialog()
        self._inputs = '\n'.join((str(observation),
                                  'Source model file: ' + str(srcModel),
                                  'Optimizer: ' + str(optimizer)))
        self.observation = observation
        self.srcModel = srcModel
        self.optimizer = optimizer
        self.logLike = pyLike.LogLike(self.observation.observation)
        self.logLike.initOutputStreams()
        self.logLike.readXml(srcModel, _funcFactory)
        self.logLike.computeEventResponses()
        self.model = SourceModel(self.logLike)
        eMin, eMax = self.observation.roiCuts().getEnergyCuts()
        nee = 21
        estep = num.log(eMax/eMin)/(nee-1)
        self.energies = eMin*num.exp(estep*num.arange(nee, type=num.Float))
        self.e_vals = num.sqrt(self.energies[:-1]*self.energies[1:])
        self.nobs = self._Nobs()
        self.disp = None
        self.resids = None
    def _Nobs(self):
        return num.array(self.observation.eventCont().nobs(self.energies))
    def _srcCnts(self, srcName):
        source = self.logLike.getSource(srcName)
        cnts = []
        for emin, emax in zip(self.energies[:-1], self.energies[1:]):
            cnts.append(source.Npred(emin, emax))
        return num.array(cnts)
    def state(self, output=sys.stdout):
        close = False
        try:
            output = open(output, 'w')
            close = False
        except:
            pass
        self.observation.state(output)
        output.write(("foo = UnbinnedAnalysis(obs, srcModel=%s, " +
                      "optimizer='%s')\n")
                     % (_quotefn(self.srcModel), self.optimizer))
        if close:
            output.close()

def unbinnedAnalysis(mode="ql", rspfunc=None, fit_tolerance=None):
    """Return an UnbinnedAnalysis object using the data in a gtlikelihood.par
file."""
    pars = pyLike.StApp_parGroup('gtlikelihood')
    if mode == 'ql':
        pars.Prompt('scfile')
        pars.Prompt('evfile')
        pars.Prompt('exposure_map_file')
        pars.Prompt('exposure_cube_file')
        pars.Prompt('source_model_file')
        pars.Prompt('optimizer')
        pars.Save()
    evfiles = pyLike.Util_resolveFitsFiles(pars['evfile'])
    scfiles = pyLike.Util_resolveFitsFiles(pars['scfile'])
    irfs = pars['rspfunc']
    if rspfunc is not None:
        irfs = rspfunc
    obs = UnbinnedObs(evfiles, scfiles,
                      expMap=_null_file(pars['exposure_map_file']),
                      expCube=_null_file(pars['exposure_cube_file']),
                      irfs=irfs)
    like = UnbinnedAnalysis(obs, pars['source_model_file'], pars['optimizer'])
    if fit_tolerance is not None:
        like.tol = fit_tolerance
    else:
        like.tol = pars.getDouble('fit_tolerance')
    return like
