"""
Interface to SWIG-wrapped C++ classes.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/ScienceTools-scons/pyLikelihood/python/SrcAnalysis.py,v 1.4 2009/03/31 18:20:53 jchiang Exp $
#
import os
import glob
import numpy as num
import pyLikelihood as pyLike
from SrcModel import SourceModel
from SimpleDialog import SimpleDialog, map, Param

_funcFactory = pyLike.SourceFactory_funcFactory()

def _resolveFileList(files):
    fileList = files.split(',')
    my_list = []
    for file in fileList:
        my_list.extend(glob.glob(file.strip()))
    return my_list

class Observation(object):
    def __init__(self, eventFile=None, scFile=None, expMap=None,
                 expCube=None, irfs='TEST', checkCuts=True):
        self.checkCuts = checkCuts
        if eventFile is None and scFile is None:
            eventFile, scFile, expMap, expCube, irfs = self._obsDialog()
        if checkCuts:
            self._checkCuts(eventFile, expMap, expCube)
        self._inputs = eventFile, scFile, expMap, irfs
        self._respFuncs = pyLike.ResponseFunctions()
        self._respFuncs.load(irfs)
        self._expMap = pyLike.ExposureMap()
        if expMap is not None and expMap is not "":
            self._expMap.readExposureFile(expMap)
        self._scData = pyLike.ScData()
        self._roiCuts = pyLike.RoiCuts()
        self._expCube = pyLike.ExposureCube()
        if expCube is not None and expCube is not "":
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
                checkCuts(eventFiles[0], 'EVENTS', file, 'EVENTS')
            if expMap is not None and expMap != '':
                checkCuts(eventFiles[0], 'EVENTS', expMap, '')
            if expCube is not None and expCube != '':
                checkTimeCuts(eventFiles[0], 'EVENTS', expCube, 'Exposure')
    def _obsDialog(self):
        paramDict = MyOrderedDict()
        paramDict['eventFile'] = Param('file', '*.fits')
        paramDict['scFile'] = Param('file', '*scData*.fits')
        paramDict['expMap'] = Param('file', '')
        paramDict['expCube'] = Param('file', '')
        paramDict['irfs'] = Param('string', 'TEST')
        root = SimpleDialog(paramDict, title="Observation Elements:")
        root.mainloop()
        eventFiles = _resolveFileList(paramDict['eventFile'].value())
        scFiles = _resolveFileList(paramDict['scFile'].value())
        output = (eventFiles, scFiles,
                  paramDict['expMap'].value(),
                  paramDict['expCube'].value(),
                  paramDict['irfs'].value())
        return output
    def __call__(self):
        return self.observation
    def _fileList(self, files):
        if isinstance(files, str):
            return [files]
        else:
            return files
    def _readData(self, scFile, eventFile):
        self._readScData(scFile)
        self._readEvents(eventFile)
    def _readScData(self, scFile):
        scFiles = self._fileList(scFile)
        self._scData.readData(scFiles[0], True)
        for file in scFiles[1:]:
            self._scData.readData(file)
    def _readEvents(self, eventFile):
        if eventFile is not None:
            eventFiles = self._fileList(eventFile)
            self._roiCuts.readCuts(eventFiles[0], 'EVENTS', False)
            for file in eventFiles:
                self._eventCont.getEvents(file)
    def __getattr__(self, attrname):
        return getattr(self.observation, attrname)
    def __repr__(self):
        lines = []
        for item in self._inputs:
            lines.append(item.__repr__().strip("'"))
        return '\n'.join(lines)

class SrcAnalysis(object):
    def __init__(self, observation, srcModel=None,  optimizer='Minuit'):
        if srcModel is None:
            srcModel, optimizer = self._srcDialog()
        self._inputs = srcModel, observation, optimizer
        self.observation = observation
        self.optimizer = optimizer
        self.events = self.observation.eventCont().events();
        self.logLike = pyLike.LogLike(self.observation())
        self.logLike.readXml(srcModel, _funcFactory)
        self.logLike.computeEventResponses()
        self.model = SourceModel(self.logLike)
        eMin, eMax = self.observation.roiCuts().getEnergyCuts()
        nee = 21
        estep = num.log(eMax/eMin)/(nee-1)
        self.energies = eMin*num.exp(estep*num.arange(nee, type=num.Float))
        self.disp = None
        self.resids = None
        self.tolType = pyLike.ABSOLUTE
    def _srcDialog(self):
        paramDict = MyOrderedDict()
        paramDict['Source Model File'] = Param('file', '*.xml')
        paramDict['optimizer'] = Param('string', 'Minuit')
        root = SimpleDialog(paramDict, title="Define SrcAnalysis Object:")
        root.mainloop()
        xmlFile = _resolveFileList(paramDict['Source Model File'].value())[0]
        output = (xmlFile, paramDict['optimizer'].value())
        return output
    def __call__(self):
        return -self.logLike.value()
    def _Nobs(self, emin, emax):
        nobs = 0
        for event in self.events:
            if emin < event.getEnergy() < emax:
                nobs += 1
        return nobs
    def plotData(self, yrange=None):
        import hippoplotter
        global plot
        plot = hippoplotter
        nt = plot.newNTuple(([], [], []),
                            ('energy', 'nobs', 'nobs_err'))
        self.data_nt = nt
        for emin, emax in zip(self.energies[:-1], self.energies[1:]):
            nobs = self._Nobs(emin, emax)
            nt.addRow((num.sqrt(emin*emax), nobs, num.sqrt(nobs)))
        self.disp = plot.XYPlot(nt, 'energy', 'nobs', yerr='nobs_err',
                                xlog=1, ylog=1)
        self.disp.getDataRep().setSymbol('filled_square', 2)
        if yrange is None:
            yrange = (0.5, max(nt.getColumn('nobs'))*1.5)
        self.disp.setRange('y', yrange[0], yrange[1])
    def _srcCnts(self, srcName):
        source = self.logLike.getSource(srcName)
        cnts = []
        for emin, emax in zip(self.energies[:-1], self.energies[1:]):
            cnts.append(source.Npred(emin, emax))
        return num.array(cnts)
    def _plot_model(self, source, yrange=None, lineStyle="Dot", oplot=False,
                    color='black'):
        import hippoplotter as plot
        if oplot and self.disp is not None:
            plot.canvas.selectDisplay(self.disp)
        else:
            self.plotData(yrange)
            
        self.col = lambda x: num.array(self.data_nt.getColumn(x))
        
        energies = self.col('energy')
        try:
            model = self._srcCnts(source)
        except:
            model = source
        plot.scatter(energies, model, oplot=True, pointRep='Line',
                     lineStyle=lineStyle, color=color)
        return model
    def _plot_residuals(self, model, oplot=None, color='black'):
        import hippoplotter as plot
        resid = (self.col('nobs') - model)/model
        resid_err = self.col('nobs_err')/model

        energies = self.col('energy')
        nt = plot.newNTuple((energies, resid, resid_err),
                            ('energy', 'residuals', 'resid_err'))
        if oplot and self.resids is not None:
            plot.canvas.selectDisplay(self.resids)
            rep = plot.XYPlot(nt, 'energy', 'residuals', yerr='resid_err',
                              xlog=1, oplot=1, color=color)
            rep.setSymbol('filled_square', 2)
        else:
            self.resids = plot.XYPlot(nt, 'energy', 'residuals',
                                      yerr='resid_err', xlog=1, color=color,
                                      yrange=(-1, 1))
            self.resids.getDataRep().setSymbol('filled_square', 2)
            plot.hline(0)
    def plot(self, srcs=None, oplot=False, yrange=None, color=None):
        import hippoplotter as plot
        if oplot and color is None:
            color = 'red'
        elif color is None:
            color = 'black'
        if isinstance(srcs, str):
            total = self._plot_model(srcs, yrange=yrange, color=color, 
                                     oplot=oplot, lineStyle='Solid')
        else:
            if srcs is None:
                srcs = pyLike.StringVector()
                self.logLike.getSrcNames(srcs)
            total = self._plot_model(srcs[0], yrange=yrange, color=color,
                                     oplot=oplot)
            if len(srcs) > 1:
                for src in list(srcs[1:]):
                    total += self._plot_model(src, oplot=True, color=color)
            self._plot_model(total, color=color, oplot=True, lineStyle='Solid')
        self._plot_residuals(total, oplot=oplot, color=color)
    def fit(self, verbosity=3, tol=1e-5, optimizer=None):
        errors = self._errors(optimizer, verbosity, tol)
        return -self.logLike.value()
    def _errors(self, optimizer=None, verbosity=0, tol=1e-2, useBase=False):
        self.logLike.syncParams()
        if optimizer is None:
            optimizer = self.optimizer
        myOpt = eval("self.logLike.%s()" % optimizer)
        myOpt.find_min(verbosity, tol, self.tolType)
        errors = myOpt.getUncertainty(useBase)
        j = 0
        for i in range(len(self.model.params)):
            if self.model[i].isFree():
                self.model[i].setError(errors[j])
                j += 1
        return errors
    def __repr__(self):
        lines = []
        for item in self._inputs:
            lines.append(item.__repr__().strip("'"))
        return '\n'.join(lines)
    def thaw(self, i):
        self.model[i].setFree(True)
    def freeze(self, i):
        self.model[i].setFree(False)

if __name__ == '__main__':
    observation = Observation('galdiffuse_events_0000.fits',
                              'galdiffuse_scData_0000.fits',
                              'expMap_test.fits')
    srcAnalysis = SrcAnalysis('galdiffuse_model.xml', observation)
    srcAnalysis.plot('Galactic Diffuse')
