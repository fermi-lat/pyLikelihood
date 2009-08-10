"""
@brief Compute the differential photon model flux (dN/dEdAdt) as a
function of energy, using the covariance matrix from the model fit to
estimate the 1 sigma error.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header$
#

import numpy as num
import pyLikelihood as pyLike

class FluxDensity(object):
    def __init__(self, like, srcName):
        self.like = like
        self.srcName = srcName
        self.ptsrc = pyLike.PointSource_cast(like[srcName].src)
        par_index_map = {}
        indx = 0
        for src in like.sourceNames():
            parNames = pyLike.StringVector()
            like[src].src.spectrum().getFreeParamNames(parNames)
            for par in parNames:
                par_index_map["::".join((src, par))] = indx
                indx += 1
        #
        # Build the source-specific covariance matrix.
        #
        if like.covariance is None:
            raise RuntimeError("Covariance matrix has not been computed.")
        covar = num.array(like.covariance)
        if len(covar) != len(par_index_map):
            raise RuntimeError("Covariance matrix size does not match the " +
                               "number of free parameters.")
        my_covar = []
        srcpars = pyLike.StringVector()
        like[srcName].src.spectrum().getFreeParamNames(srcpars)
        pars = ["::".join((srcName, x)) for x in srcpars]
        for xpar in pars:
            ix = par_index_map[xpar]
            my_covar.append([covar[ix][par_index_map[ypar]] for ypar in pars])
        self.covar = num.array(my_covar)
        self.srcpars = srcpars
    def value(self, energy):
        arg = pyLike.dArg(energy)
        return self.ptsrc.spectrum()(arg)
    def error(self, energy):
        arg = pyLike.dArg(energy)
        partials = num.array([self.ptsrc.spectrum().derivByParam(arg, x) 
                              for x in self.srcpars])
        return num.sqrt(num.dot(partials, num.dot(self.covar, partials)))
    def write_nuFnu(self, outfile, emin=100, emax=3e5, npts=500):
        estep = num.log(emax/emin)/(npts - 1)
        energies = emin*num.exp(estep*num.arange(npts, dtype=num.float))
        output = open(outfile, 'w')
        for ee in energies:
            F = self.value(ee)
            dF = self.error(ee)
            nuFnu = ee**2*F*1.602e-6
            dnuFnu =  ee**2*dF*1.602e-6
            output.write("%12.4e  %12.4e  %12.4e\n" % (ee, nuFnu, dnuFnu))
        output.close()
