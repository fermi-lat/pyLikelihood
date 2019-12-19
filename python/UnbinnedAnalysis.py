"""
Python interface for unbinned likelihood

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/pyLikelihood/python/UnbinnedAnalysis.py,v 1.50 2016/09/15 21:27:41 echarles Exp $
#

import sys
import glob
import pyLikelihood as pyLike
from SrcModel import SourceModel
from AnalysisBase import AnalysisBase, _quotefn, _null_file, num
try:
    from SimpleDialog import SimpleDialog, map, Param
except ImportError as message:
    pass

_funcFactory = pyLike.SourceFactory_funcFactory()

def _resolveFileList(files):
    fileList = files.split(',')
    my_list = []
    for file in fileList:
        my_list.extend(glob.glob(file.strip()))
    return my_list

class UnbinnedObs(object):
    def __init__(self, eventFile=None, scFile=None, expMap=None,
                 expCube=None, irfs=None, checkCuts=True, sctable='SC_DATA'):
        self.sctable = sctable
        self.checkCuts = checkCuts
        if eventFile is None and scFile is None:
            eventFile, scFile, expMap, expCube, irfs = self._obsDialog()
        if checkCuts:
            self._checkCuts(eventFile, expMap, expCube)
        self.expMap = expMap
        self.expCube = expCube
        if irfs is None or irfs == 'CALDB':
            evfiles = self._fileList(eventFile)
            my_cuts = pyLike.Cuts(evfiles[0], "EVENTS", False, True, True)
            self.irfs = my_cuts.CALDB_implied_irfs()
        else:
            self.irfs = irfs
        self._inputs = '\n'.join(('Event file(s): ' + str(eventFile),
                                  'Spacecraft file(s): ' + str(scFile),
                                  'Exposure map: ' + str(expMap),
                                  'Exposure cube: ' + str(expCube),
                                  'IRFs: ' + str(irfs)))
        self._respFuncs = pyLike.ResponseFunctions()
        evfiles = self._fileList(eventFile)
        self._respFuncs.load_with_event_types(self.irfs, "",
                                              evfiles[0], "EVENTS")
        self._expMap = pyLike.ExposureMap()
        if expMap is not None and expMap != "":
            self._expMap.readExposureFile(expMap)
        self._scData = pyLike.ScData()
        self._roiCuts = pyLike.RoiCuts()
        self._expCube = pyLike.ExposureCube()
        if expCube is not None and expCube != "":
            self._expCube.readExposureCube(expCube)
        self._expCube.setEfficiencyFactor(self._respFuncs.efficiencyFactor())
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
            checkExpMapCuts = pyLike.AppHelpers_checkExpMapCuts
            for file in eventFiles[1:]:
                checkCuts(eventFiles[0], 'EVENTS', file, 'EVENTS', False)
            if expMap is not None and expMap != '':
                checkExpMapCuts(eventFiles, expMap)
            if expCube is not None and expCube != '':
                checkTimeCuts(eventFiles, 'EVENTS', expCube, 'Exposure')
    def _obsDialog(self):
        paramDict = MyOrderedDict()
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
        self._readScData(scFile, eventFile)
        self._readEvents(eventFile)
        if self.expCube is not None and self.expCube != "":
            # Clear the spacecraft data to save memory for long observations.
            self._scData.clear_arrays()
    def _readEvents(self, eventFile):
        if eventFile is not None:
            eventFiles = self._fileList(eventFile)
            self._roiCuts.readCuts(eventFiles, 'EVENTS', False)
            for file in eventFiles:
                self._eventCont.getEvents(file)
            self.eventFiles = eventFiles
    def _readScData(self, scFile, eventFile):
        if eventFile is not None:
            eventFiles = self._fileList(eventFile)
            self._roiCuts.readCuts(eventFiles, 'EVENTS', False)
        tmin = self._roiCuts.minTime()
        tmax = self._roiCuts.maxTime()
        scFiles = self._fileList(scFile)
        self._scData.readData(scFiles, tmin, tmax, self.sctable)
        self.scFiles = scFiles
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
                      "irfs='%s')\n") % (pepr(self.eventFiles), repr(self.scFiles),
                                         _quotefn(self.expMap),
                                         _quotefn(self.expCube), self.irfs))
        if close:
            output.close()

class UnbinnedAnalysis(AnalysisBase):
    def __init__(self, observation, srcModel=None, optimizer='Drmngb', nee=21):
        AnalysisBase.__init__(self)
        if srcModel is None:
            srcModel, optimizer = self._srcDialog()
        self.observation = observation
        self.srcModel = srcModel
        self.optimizer = optimizer
        self.logLike = pyLike.LogLike(self.observation.observation)
        self.logLike.initOutputStreams()
        self.logLike.readXml(srcModel, _funcFactory, True, True, False)
        self.logLike.computeEventResponses()
        self.model = SourceModel(self.logLike, srcModel)
        eMin, eMax = self.observation.roiCuts().getEnergyCuts()
        estep = num.log(eMax/eMin)/(nee-1)
        self.energies = eMin*num.exp(estep*num.arange(nee, dtype=num.float))
        self.energies[-1] = eMax
        self.e_vals = num.sqrt(self.energies[:-1]*self.energies[1:])
        self.nobs = self._Nobs()
        self.nobs_wt = self.nobs
        self.disp = None
        self.resids = None
        self.sourceFitPlots = []
        self.sourceFitResids  = []
    def _inputs(self):
        return '\n'.join((str(self.observation),
                          'Source model file: ' + str(self.srcModel),
                          'Optimizer: ' + str(self.optimizer)))
    def _Nobs(self):
        return num.array(self.observation.eventCont().nobs(self.energies))
    def plotSourceFit(self, srcName, color='black'):
        self._importPlotter()
        source = self.logLike.getSource(srcName)
        nobs = self.observation.eventCont().nobs(self.energies, source)
        errors = []
        for ntilde, nsq in zip(nobs, num.sqrt(self.nobs)):
            if nsq == 0:
                errors.append(0)
            else:
                errors.append(ntilde/nsq)
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
    def _srcCnts(self, srcName, weighted=False):
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
        output.write(("like = UnbinnedAnalysis(obs, srcModel=%s, " +
                      "optimizer='%s')\n")
                     % (_quotefn(self.srcModel), self.optimizer))
        if close:
            output.close()
    def reset_ebounds(self, new_energies):
        eMin, eMax = self.observation.roiCuts().getEnergyCuts()
        if eMin != min(new_energies) or eMax != max(new_energies):
            self.logLike.set_ebounds(min(new_energies), max(new_energies))
        elist = [x for x in new_energies]
        elist.sort()
        self.energies = num.array(elist)
        self.e_vals = num.sqrt(self.energies[:-1]*self.energies[1:])
        self.nobs = self._Nobs()
    def setEnergyRange(self, emin, emax):
        roi_ebounds = self.observation.roiCuts().getEnergyCuts()
#        if emin < roi_ebounds[0] or emax > roi_ebounds[1]:
# At J. Ballet request, this case will now be handled by the C++ member
# function Likelihood::LogLike::value(...) which will return zero if
# the selected energy bounds exclude the data originally selected by
# the ROI bounds.
#            raise RuntimeError("UnbinnedAnalysis.setEnergyRange: " +
#                               "attempt to set energy bound outside of " +
#                               "data range of %.2f %.2f" % roi_ebounds)
        self.logLike.set_ebounds(emin, emax)
        #
        # Set the number of energy bands for plotting by scaling to
        # the default number using the ROI energy range.
        #
        nee = 21
        eMin_roi, eMax_roi = self.observation.roiCuts().getEnergyCuts()
        npts = int(nee*(num.log(emax) - num.log(emin))
                   /(num.log(eMax_roi) - num.log(eMin_roi)))
        if npts < 2:
            npts = 5
        energies = num.logspace(num.log10(emin), num.log10(emax), npts)
        self.reset_ebounds(energies)
        
def unbinnedAnalysis(mode="ql", ftol=None, nee=21, **pars):
    """Return an UnbinnedAnalysis object using the data in gtlike.par"""
    parnames = ('irfs', 'scfile', 'evfile', 'expmap', 'expcube', 
                'srcmdl', 'optimizer')
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
    irfs = pars['irfs']
    evfilename = pars['evfile']
    if evfilename.find('@') == 0:
        evfilename = evfilename[1:]
    evfiles = pyLike.Util_resolveFitsFiles(evfilename)
    scfiles = pyLike.Util_resolveFitsFiles(pars['scfile'])
    obs = UnbinnedObs(evfiles, scfiles,
                      expMap=_null_file(pars['expmap']),
                      expCube=_null_file(pars['expcube']),
                      irfs=irfs)
    like = UnbinnedAnalysis(obs, pars['srcmdl'], pars['optimizer'], nee=nee)
    if ftol is not None:
        like.tol = ftol
    else:
        like.tol = pargroup.getDouble('ftol')
    return like
