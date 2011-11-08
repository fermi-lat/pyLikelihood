"""
A Module to calculate SEDs using the pyLikelihood framework.

The primary benefit to this implementation is that it requires no
temporary files and automatically saves the output in a nice format. All
you need is a BinnedAnalysis and you can directly generate the SED.

The SED is created by modifying the source of interest to have
a fixed spectral index and in each energy band fitting
the flux of the source.

Usage:

name='Vela'
like=BinnedAnalysis(...)
sed = SED(like,name)

sed = SED(like,name)

# save data points to a file
sed.save('sed_Vela.dat') 

# The SED can be plotted assuming that matplotlib is installed
sed.plot('sed_Vela.png') 

# And finally, the results of the SED fit can be packaged 
# into a convenient dictionary for further use

results=sed.todict()

# To load the data points into a new python script
# which have previously been saved to a file:

results_dictionary=eval(open('sed_vela.dat').read())

@author J. Lande <lande@slac.stanford.edu>

Todo:
* Merge upper limits at either edge in energy.

$Header$
"""
from os.path import join
import csv
from pprint import pformat
from StringIO import StringIO

import numpy as np
from scipy.stats import chi2
import pylab as P

from pyLikelihood import ParameterVector, dArg
from LikelihoodState import LikelihoodState
from UpperLimits import UpperLimits
from IntegralUpperLimit import calc_int

class SED(object):
    """ Object to make SEDs using pyLikelihood. """

    ul_choices = ['frequentist', 'bayesian']

    def __init__(self, like, name, 
                 bin_edges=None,
                 verbosity=0, 
                 freeze_background=True,
                 always_upper_limit=False,
                 ul_algorithm='bayesian',
                 powerlaw_index=-2,
                 min_ts=4,
                 ul_confidence=.95):
        """ Parameters:
            * like - pyLikelihood object
            * name - source to make an SED for
            * bin_edges - if specified, calculate the SED in these bins.
            * verbosity - how much output
            * freeze_background - don't refit background sources.
            * always_upper_limit - Always compute an upper limit. Default 
                                   is only when source is not significant. 
            * ul_algorithm - choices = 'frequentist', 'bayesian' 
            * powerlaw_index - fixed spectral index to assume when
                               computing SED.
            * min_ts - minimum ts in which to quote a SED points instead of an upper limit. 
            * ul_confidence - confidence level for upper limit. """
        self.name               = name
        self.verbosity          = verbosity
        self.freeze_background  = freeze_background
        self.always_upper_limit = always_upper_limit
        self.ul_algorithm       = ul_algorithm
        self.powerlaw_index     = powerlaw_index
        self.min_ts             = min_ts
        self.ul_confidence      = ul_confidence

        self.spectrum = like.logLike.getSource(self.name).spectrum()

        if bin_edges is not None:

            for e in bin_edges:
                if np.alltrue(np.abs(e - like.energies) > 0.5):
                    raise Exception("energy %.1f in bin_edges is not commensurate with the energy binning of pyLikelihood." % e)
            
            bin_edges = np.asarray(bin_edges)
            self.energy = np.sqrt(bin_edges[1:]*bin_edges[:-1])
        else:
            # These energies are always in MeV
            bin_edges = like.energies
            self.energy = like.e_vals

        self.lower_energy=bin_edges[:-1]
        self.upper_energy=bin_edges[1:]

        if ul_algorithm not in self.ul_choices:
            raise Exception("Upper Limit Algorithm %s not in %s" % (ul_algorithm,str(self.ul_choices)))

        # dN/dE, dN/dE_err and upper limits (ul)
        # always in units of ph/cm^2/s/MeV
        self.dnde=np.empty_like(self.energy)
        self.dnde_err=np.empty_like(self.energy)
        self.dnde_ul=-1*np.ones_like(self.energy) # -1 is no UL

        self.flux=np.empty_like(self.energy)
        self.flux_err=np.empty_like(self.energy)
        self.flux_ul=-1*np.ones_like(self.energy)

        self.eflux=np.empty_like(self.energy)
        self.eflux_err=np.empty_like(self.energy)
        self.eflux_ul=-1*np.ones_like(self.energy)

        self.ts=np.empty_like(self.energy)

        self._calculate(like)

    @staticmethod
    def frequentist_upper_limit(like,name,emin,emax,confidence,verbosity):
        """ Calculate a frequentist upper limit on the prefactor. 
            Returns the unscaled prefactor upper limit. """
        delta_logl = lambda confidence: chi2.ppf(2*confidence-1,1)/2.
        ul = UpperLimits(like)
        flux_ul, pref_ul = ul[name].compute(emin=emin, emax=emax, 
                                            delta=delta_logl,
                                            verbosity=verbosity)
        return pref_ul

    @staticmethod
    def bayesian_upper_limit(like,name,emin,emax,confidence,verbosity):
        """ Calculate a baysian upper limit on the prefactor.
            Return the unscaled prefactor upper limit. """
        flux_ul,results = calc_int(like, name, 
                                   freeze_all=True,
                                   skip_global_opt=True,
                                   emin=emin, emax=emax,
                                   cl = confidence,
                                   verbosity=verbosity)
        pref_ul = results['ul_value']
        return pref_ul

    @staticmethod
    def upper_limit(like,name,ul_algorithm,emin,emax,**kwargs):
        """ Calculates the upper limit. Returns the dN/dE, Flux, and eergy
            flux upper limit. """
        if ul_algorithm == 'frequentist': 
            f = SED.frequentist_upper_limit
        elif ul_algorithm == 'bayesian':  
            f = SED.bayesian_upper_limit

        pref_ul = f(like,name,emin,emax,**kwargs)

        prefactor=like[like.par_index(name, 'Prefactor')]
        pref_ul *= prefactor.getScale() # scale prefactor
        prefactor.setTrueValue(pref_ul)

        flux_ul = like.flux(name,emin,emax)
        eflux_ul = like.energyFlux(name,emin,emax)

        return pref_ul,flux_ul, eflux_ul

    def _calculate(self,like):
        """ Compute the flux data points for each energy. """

        name    = self.name
        verbosity = self.verbosity
        init_energes = like.energies[[0,-1]]

        # Freeze all sources except one to make sed of.
        all_sources = like.sourceNames()

        if name not in all_sources:
            raise Exception("Cannot find source %s in list of sources" % name)

        # make copy of parameter values + free parameters
        
        saved_state = LikelihoodState(like)

        if self.freeze_background:
            if verbosity: print 'Freezeing all parameters'
            # freeze all other sources
            for i in range(len(like.model.params)):
                like.freeze(i)

        # convert source to a PowerLaw of frozen index 

        source = like.logLike.getSource(name)
        old_spectrum=source.spectrum()
        like.setSpectrum(name,'PowerLaw')

        index=like[like.par_index(name, 'Index')]
        index.setTrueValue(self.powerlaw_index)
        index.setFree(0)
        like.syncSrcParams(name)

        # assume a canonical dnde=1e-11 at 1GeV index 2 starting value
        dnde = lambda e: 1e-11*(e/1e3)**-2

        optverbosity = max(verbosity-1, 0) # see IntegralUpperLimit.py

        for i,(lower,upper) in enumerate(zip(self.lower_energy,self.upper_energy)):

            e = np.sqrt(lower*upper)

            if verbosity: print 'Calculating spectrum from %.0dMeV to %.0dMeV' % (lower,upper)

            # goot starting guess for source
            prefactor=like[like.par_index(name, 'Prefactor')]
            prefactor.setScale(dnde(e))
            prefactor.setValue(1)
            prefactor.setBounds(1e-10,1e10)

            scale=like[like.par_index(name, 'Scale')]
            scale.setScale(1)
            scale.setValue(e)
            like.syncSrcParams(name)

            like.setEnergyRange(float(lower)+1, float(upper)-1)

            try:
                like.fit(optverbosity,covar=True)
            except Exception, ex:
                if verbosity: print 'ERROR gtlike fit: ', ex

            self.ts[i]=like.Ts(name,reoptimize=False)

            prefactor=like[like.par_index(name, 'Prefactor')]
            self.dnde[i] = prefactor.getTrueValue()
            self.dnde_err[i] = prefactor.error()*prefactor.getScale()

            self.flux[i] = like.flux(name, lower, upper)
            self.flux_err[i] = like.fluxError(name, lower, upper)

            self.eflux[i] = like.energyFluxError(name, lower, upper)
            self.eflux_err[i] = like.energyFluxError(name, lower, upper)

            if self.ts[i] < self.min_ts or self.always_upper_limit: 
                if verbosity: print 'Calculating upper limit from %.0dMeV to %.0dMeV' % (lower,upper)
                self.dnde_ul[i], self.flux_ul[i], self.eflux_ul[i] = SED.upper_limit(like,name,self.ul_algorithm,lower,upper,
                                                                                     confidence=self.ul_confidence,
                                                                                     verbosity=verbosity)

            if verbosity:
                print lower,upper,self.dnde[i],self.dnde_err[i],self.ts[i],self.dnde_ul[i]

        self.significant=self.ts>=self.min_ts

        # revert to old model
        like.setEnergyRange(*init_energes)
        like.setSpectrum(name,old_spectrum)
        saved_state.restore()

    def todict(self):
        """ Pacakge up the results of the SED fit into
            a nice dictionary. """
        return dict(
            Name=self.name,
            Energy=dict(
                Lower=self.lower_energy.tolist(),
                Upper=self.upper_energy.tolist(),
                Value=self.energy.tolist(),
                Units='MeV'),
            dNdE=dict(
                Value=self.dnde.tolist(),
                Error=self.dnde_err.tolist(),
                Upper_Limit=self.dnde_ul.tolist(),
                Units='ph/cm^2/s/MeV'),
            Ph_Flux=dict(
                Value=self.flux.tolist(),
                Error=self.flux_err.tolist(),
                Upper_Limit=self.flux_ul.tolist(),
                Units='ph/cm^2/s'),
            En_Flux=dict(
                Value=self.eflux.tolist(),
                Error=self.eflux_err.tolist(),
                Upper_Limit=self.eflux_ul.tolist(),
                Units='MeV/cm^2/s'),
            Test_Statistic=self.ts.tolist(),
            Significant=self.significant.tolist(),
            Spectrum=SED.spectrum_to_dict(self.spectrum))

    def __str__(self):
        """ Pack up values into a nicely formatted string. """
        results = self.todict()
        return pformat(results)

    @staticmethod
    def spectrum_to_dict(spectrum, errors=False):
        """ Convert a pyLikelihood object to a python 
            dictionary which can be easily saved to a file. """
        parameters=ParameterVector()
        spectrum.getParams(parameters)
        d = dict(name = spectrum.genericName())
        for p in parameters: 
            d[p.getName()]= p.getTrueValue()
            if errors: d['%s_err' % p.getName()]= p.error()*p.getScale()
        return d

    def save(self,filename,**kwargs):
        """ Save SED data points to a file. """
        if hasattr(filename,'write'):
            filename.write(self.__str__())
        else:
            f=open(filename,'w')
            f.write(self.__str__())
            f.close()

    @staticmethod
    def get_dnde(spectrum,energies):
        """ Returns the spectrum in units of ph/cm^2/s/MeV. """
        return np.asarray([spectrum(dArg(i)) for i in energies])
    @staticmethod 
    def plot_spectrum(axes,spectrum, npts=100, **kwargs):
        """ This function overlays a pyLikleihood spectrum
            object onto a Matplotlib axes assumign that
            (a) the x-axis is in MeV and (b) that
            the y-axis is E^2 dN/dE (MeV/cm^2/s) """
        low_lim, hi_lim = axes.get_xlim()
        eneriges = np.logspace(np.log10(low_lim), np.log10(hi_lim), npts)
        axes.plot(energies , energies**2*SED.get_dnde(spectrum,energies), **kwargs)

    @staticmethod
    def _plot_points(x, xlo, xhi, 
              y, y_err, y_ul, significant,
              energy_units,flux_units,
              axes, **kwargs):

        plot_kwargs = dict(linestyle='none', color='black')
        plot_kwargs.update(kwargs)

        s = significant

        dx_hi=xhi-x
        dx_lo=x-xlo

        # plot data points
        if sum(s)>0:
            axes.errorbar(x[s], y[s],
                          xerr=[dx_lo[s], dx_hi[s]], yerr=y_err[s],
                          capsize=0, **plot_kwargs)
        
        # and upper limits
        if sum(~s)>0:
            ul_kwargs = dict(linestyle='none', lolims=True, color='black')

            # plot veritical lines (with arrow)
            axes.errorbar(x[~s], y_ul[~s],
                          yerr=[0.4*y_ul[~s],np.zeros(sum(~s))],
                          lolims=True, **plot_kwargs)

            # plot horizontal line (no caps)
            axes.errorbar(x[~s], y_ul[~s],
                          xerr=[dx_lo[~s], dx_hi[~s]],
                          capsize=0, **plot_kwargs)

        axes.set_xscale('log')
        axes.set_yscale('log')
        
        
        axes.set_xlabel('Energy (%s)' % energy_units)
        axes.set_ylabel('E$^2$ dN/dE (%s cm$^{-2}$ s$^{-1}$)' % flux_units)
    
    def set_xlim(self, axes,lower,upper, extra=0.1):
        """ Set the xlim of the plot to be larger
            in the x and y direciton by a fraction
            'extra' in log-space. """
        l,h=np.log10(lower),np.log10(upper)
        low_lim=10**(l - 0.1*(h-l))
        hi_lim =10**(h + 0.1*(h-l))
        axes.set_xlim(low_lim,hi_lim)

    def plot(self,
             filename=None,
             axes=None, 
             fignum=None, figsize=(4,4),
             plot_spectral_fit=True,
             data_kwargs=dict(),
             spectral_kwargs=dict(color='red')):
        """ Plot the SED using matpotlib. """

        if axes is None:
            fig = P.figure(fignum,figsize)
            axes = fig.add_axes((0.22,0.15,0.75,0.8))
            self.set_xlim(axes,self.lower_energy[0],self.upper_energy[-1])

        SED._plot_points(
            x=self.energy, 
            xlo=self.lower_energy, 
            xhi=self.upper_energy, 
            y=self.energy**2*self.dnde, 
            y_err=self.energy**2*self.dnde_err, 
            y_ul=self.energy**2*self.dnde_ul,
            significant=self.significant,
            energy_units='MeV', flux_units='MeV',
            axes=axes, **data_kwargs)

        if plot_spectral_fit:
            print 'this is bad right now'
            SED.plot_spectrum(axes,self.spectrum, **spectral_kwargs)

        if filename is not None: P.savefig(filename)
