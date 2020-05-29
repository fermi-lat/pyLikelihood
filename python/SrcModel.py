"""
SourceModel interface to allow for manipulation of fit parameters.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/pyLikelihood/python/SrcModel.py,v 1.12 2016/10/13 02:10:40 echarles Exp $
#
import sys
from xml.dom import minidom
import pyLikelihood as pyLike

_app_helper = pyLike.AppHelpers()

def ids(istart=0):
    i = istart - 1
    while True:
        i += 1
        yield(i)

class SourceModel(object):
    def __init__(self, logLike, xmlFile=None):
        self.logLike = logLike
        self._loadSources()
        if xmlFile is not None:
            self._addXmlAttributes(xmlFile)
    def delete(self, source):
        src = self.logLike.deleteSource(source)
        self._loadSources()
        return src
    def add(self, source):
        try:
            print ("adding ", source.getName())
            self.logLike.addSource(source)
            self._loadSources()
        except:
            pass
    def syncParams(self):
        "Loop through sources and synchronize the parameters if necessary."
        for source_name, source in self.srcs.items():
            if source.is_modified:
                self.logLike.syncSrcParams(source_name)
                source.is_modified = False
    def _loadSources(self):
        srcNames = pyLike.StringVector()
        self.logLike.getSrcNames(srcNames)
        self.srcNames = tuple(srcNames)
        self.srcs = {}
        for name in srcNames:
            self.srcs[name] = Source(self.logLike.getSource(name))
        self._walk()
        self.printFreeOnly = False
    def _addXmlAttributes(self, xmlFile):
        srcs = minidom.parse(xmlFile).getElementsByTagName('source')
        for item in srcs:
            name = item.getAttribute('name')
            for key in item.attributes.keys():
                value = item.getAttribute(key)
                try:
                    eval('self.srcs[name].src.%s' % key)
                except AttributeError:
                    self.srcs[name].__dict__[key] = self._convertType(value)
                except KeyError:
                    # FIXME, do we want to do a recursive find here?
                    print ("Did not set xml attribute for nested source: %s : %s"%(key,value))
    def _convertType(self, value):
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value.encode()
    def _walk(self):
        indx = ids()
        self.params = []
        for srcName in self.srcNames:
            src = self[srcName]
            for funcName in src.funcs:
                if funcName == "Spectrum":
                    func = src.funcs[funcName]
                    for param in func.paramNames:
                        self.params.append(func.getParam(param))
                        src.funcs[funcName].appendParId(next(indx))
    def __setitem__(self, indx, value):
        self.params[indx].setValue(value)
        self.params[indx].setError(0)
    def __getitem__(self, srcName):
        try:
            return self.params[srcName]
        except:
            try:
                return self.srcs[srcName]
            except:
                pass
    def __repr__(self):
        lines = []
        for src in self.srcNames:
            lines.append(self[src].__repr__('   ', self.printFreeOnly))
        return "\n".join(lines)

    def addPrior(self, srcName, parName, funcname, **kwds):
        par = self.srcs[srcName].funcs["Spectrum"].params[parName]
        par.addPrior(funcname)
        par.setPriorParams(**kwds)

    def addGaussianPrior(self, srcName, parName, mean, sigma):
        par = self.srcs[srcName].funcs["Spectrum"].params[parName]
        par.addGaussianPrior(mean, sigma)

    def removePrior(self, srcName, parName):
        par = self.srcs[srcName].funcs["Spectrum"].params[parName]
        return par.removePrior()

    def getPriorLogValue(self, srcName, parName):
        par = self.srcs[srcName].funcs["Spectrum"].params[parName]
        return par.log_prior_value()

    def getPriorLogDeriv(self, srcName, parName):
        par = self.srcs[srcName].funcs["Spectrum"].params[parName]
        return par.log_prior_deriv()    

    def setPriorParams(self, srcName, parName, **kwds):
        par = self.srcs[srcName].funcs["Spectrum"].params[parName]
        par.setPriorParams(**kwds)

    def setGaussianPriorParams(self, srcName, parName, mean, sigma):
        par = self.srcs[srcName].funcs["Spectrum"].params[parName]
        par.setGaussianPriorParams(mean, sigma)

    def removePriors(self):
        for par in self.params:
            par.removePrior()

    def getPriors(self):
        ret_dict = {}
        for par in self.params:
            prior_params = par.getPriorParams()
            if prior_params is None:
                continue
            src_name = par.srcName
            prior_funcname = 'GaussianError'
            prior_par_dict = dict(funcname=prior_funcname,
                                  pars=prior_params)
            if src_name in ret_dict:
                ret_dict[src_name][par.getName()] = prior_par_dict
            else:
                ret_dict[src_name] = {par.getName():prior_par_dict}
        return ret_dict

    def addPriors(self, prior_dict):
        for src_name, src_prior_dict in prior_dict.items():
            for par_name, prior_par_dict in src_prior_dict.items():
                funcname = prior_par_dict['funcname']
                pars = prior_par_dict['pars']
                self.addPrior(src_name, par_name, funcname, **pars)

    def constrain_norms(self, srcNames, cov_scale=1.0):
        for name in srcNames:
            par = self.srcs[name].funcs["Spectrum"].normPar()
            err = par.error()
            val = par.getValue()
            if par.error() == 0.0 or not par.isFree():
                continue            
            self.addGaussianPrior(name, par.getName(), val, err * cov_scale)

    def constrain_params(self, srcNames, cov_scale=1.0):
        for name in srcNames:
            free_pars = pyLike.ParameterVector()
            self.srcs[name].funcs["Spectrum"].getFreeParams(free_pars)
            for i in range(free_pars.size()):
                par = free_pars[i]
                err = par.error()
                val = par.getValue()
                if par.error() == 0.0 or not par.isFree():
                    continue            
                self.addGaussianPrior(name, par.getName(), val, err * cov_scale)


class Source(object):
    def __init__(self, src):
        self.src = src
        funcs = src.getSrcFuncs()
        self.funcs = {}
        for item in funcs.keys():
            self.funcs[item] = Function(funcs[item], src.getName(), self)
        self.is_modified = False
    def __getitem__(self, name):
        return self.funcs[name]
    def __repr__(self, prefix='   ', free_only=False):
        lines = [self.src.getName()]
        for item in self.funcs:
            if item == "Spectrum":
                lines.append(prefix + item + ": " + self[item].genericName())
                lines.append(self[item].__repr__(prefix, free_only))
        if self.src.getType() == "Composite":
            for n in self.nested():
                lines.append(prefix + " Nested: " + n)
        return "\n".join(lines) + "\n"
    def __getattr__(self, attrname):
        #return getattr(self.src, attrname)
        srcType = self.src.getType()
        if srcType == "Composite":
            cast = pyLike.CompositeSource.cast(self.src)
        elif srcType == "Point":
            cast = pyLike.PointSource.cast(self.src)
        elif srcType == "Diffuse":
            cast = pyLike.DiffuseSource.cast(self.src)
        else:
            return None        
        return getattr(cast, attrname)

    def nested(self):
        if self.src.getType() != "Composite":
            return None
        comp = pyLike.CompositeSource.cast(self.src)
        sv = pyLike.StringVector()
        comp.getSrcNames(sv)
        n = [sv[i] for i in range(sv.size())]
        return n

class Function(object):
    def __init__(self, func, srcName=None, source_obj=None):
        self.func = func
        self.srcName = srcName
        names = pyLike.StringVector()
        func.getParamNames(names)
        self.paramNames = list(names)
        self.params = {}
        for name in self.paramNames:
            self.params[name] = Parameter(self.func.getParam(name), srcName,
                                          source_obj)
        self._parIds = []
    def __getitem__(self, name):
        return self.func.getParamValue(name)
    def __setitem__(self, name, value):
        self.func.setParam(name, value)
    def getParam(self, name):
        return self.params[name]
    def appendParId(self, indx):
        self._parIds.append(indx)
    def __repr__(self, prefix='', free_only=False):
        lines = []
        for indx, parName in zip(self._parIds, self.paramNames):
            par = self.getParam(parName)
            if not free_only or par.isFree():
                lines.append("%-3i%s%s" % (indx, prefix, par.__repr__()))
        return "\n".join(lines)
    def __getattr__(self, attrname):
        return getattr(self.func, attrname)

class Parameter(object):
    def __init__(self, parameter, srcName=None, source_obj=None):
        self.parameter = parameter
        self.srcName = srcName
        self.source_obj = source_obj
    def __repr__(self):
        par = self.parameter
        desc = ("%10s: %10.3e " % (par.getName(), par.getValue()) +
                "%10.3e " % par.error() +
                "%10.3e %10.3e " % par.getBounds() +
                "(%10.3e)" % par.getScale())
        if not par.isFree():
            desc += " fixed"
        return desc
    def setFree(self, value):
        self.parameter.setFree(value)
        if not value:
            self.parameter.setError(0)
        self.source_obj.is_modified = True
    def setScale(self, scale):
        self.parameter.setScale(scale)
        self.source_obj.is_modified = True
    def value(self):
        return self.parameter.getValue()
    def addPrior(self, funcname):
        if self.parameter.log_prior() is not None:
            raise RuntimeError("Prior for parameter %s already applied"
                               % self.parameter.getName())
        func = _app_helper.funcFactory().create(funcname)
        self.parameter.setPrior(func)
    def setPriorParams(self, **kwds):
        prior = self.parameter.log_prior()
        if prior is None:
            raise RuntimeError("No prior for parameter " 
                               + self.parameter.getName())
        for key, value in kwds.items():
            prior.setParam(key, value)
    def addGaussianPrior(self, mean, sigma):
        self.addPrior('GaussianError')
        self.setPriorParams(Mean=mean, Sigma=sigma)
    def getPriorParams(self):
        prior = self.parameter.log_prior()
        if prior is None:
            return None
        pars = {}
        names = pyLike.StringVector()
        prior.getParamNames(names)
        for name in names:
            pars[name] = prior.getParamValue(name)
        return pars
    def setGaussianPriorParams(self, mean, sigma):
        func = self.parameter.log_prior()
        if func.getName() != 'GaussianError':
            raise RuntimeError('Prior is not Gaussian')
        self.setPriorParams(Mean=mean, Sigma=sigma)
    def removePrior(self):
        return self.parameter.removePrior()
    def __getattr__(self, attrname):
        return getattr(self.parameter, attrname)
