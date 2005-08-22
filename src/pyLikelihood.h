/**
   @page pyLikelihood pyLikelihood Tutorial

   @section tutorial Likelihood Analysis from Python

   Unbinned and binned analysis have been implemented in the <a
   href="">UnbinnedAnalysis.py</a> and <a
   href="">BinnedAnalysis.py</a> modules, respectively.  Each module
   contains two classes: @b UnbinnedObs and @b UnbinnedAnalysis in the
   former, and @b BinnedObs and @b BinnedAnalysis in the latter.

   The "Obs" classes differ in how they are constructed since the
   respective analyses require different sets of input data.
   Nonetheless, both implementations are intended to encapsulate the
   information associated with a specific observation.  In this
   context, an observation is defined in terms of the extraction
   region in the data space of photon arrival time, measured energy,
   and direction.  An observation also comprises ancilliary
   information specific to the data selections such as the exposure
   information and the response functions to be used.

   The signature of the @b UnbinnedObs constructor is

@verbatim
class UnbinnedObs(object):
    def __init__(self, eventFile=None, scFile=None, expMap=None,
                 expCube=None, irfs='DC1A', checkCuts=True):
@endverbatim

   and its parameters are

   - @b eventFile: Event data file name(s), either a single file name 
     or a tuple or list of file names.  If given as a single file name, it 
     can also be an ascii file of FITS file names.
   - @b scFile: Spacecraft data file name(s).  This can also be an ascii
     file of FITS file names.
   - @b expMap: Exposure map (produced by @b gtexpmap).  The geometry
     of this map matches that of the extraction region used to create
     the event files.
   - @b expCube: Live-time cube (produced by @b gtlivetimecube).  This
     an off-axis histogram of live-times at each point in the sky,
     partitioned as nested HealPix.
   - @b irfs: Instrument response functions, e.g., <tt>DC1</tt>,
     <tt>DC1A</tt>, <tt>G25</tt>, or <tt>TEST</tt>
   - @b checkCuts: A flag used for debugging purposes.  This should
     be set to True for a standard analysis.

   The @b BinnedObs constructor signature is

@verbatim
class BinnedObs(object):
    def __init__(self, srcMaps, expCube, binnedExpMap=None, irfs='DC1A'):
@endverbatim   

   and its parameters are

   - @b srcMaps: This is a counts map file with axes in position
     and energy and source map extensions created using @b gtsrcmaps.
     The counts map may be created with @b gtcntsmap.  If one provides
     a counts map without a complete set of source map extensions, the
     @b BinnedAnalysis class will examine the model definition file
     and will compute source maps in memory for all the sources that
     do not have source maps in the counts map file.
   - @b expCube: The live-time cube.
   - @b binnedExpMap: Exposure map appropriate for binned likelihood
     analysis. This is optional.  If it is not specified, then
     Likelihood will compute an appropriate map and output it as
     <tt>binned_exposure.fits</tt>.  These exposure maps are matched
     to the geometry of the counts map in srcMaps.
   - @b irfs: Instrument response functions, e.g., <tt>DC1</tt>,
     <tt>DC1A</tt>, <tt>G25</tt>, or <tt>TEST</tt>

   Consult the <a
   href="http://glast-ground.slac.stanford.edu/workbook/science-tools/pages/sciTools_likelihoodTutorial/likelihoodTutorial.htm">unbinned</a>
   and <a
   href="http://glast-ground.slac.stanford.edu/workbook/science-tools/pages/sciTools_binnedLikelihoodTutorial/binnedLikelihood.htm">binned</a>
   analysis tutorials for more detailed description of the
   inputs to these classes.

   The "Analysis" classes have the same public interfaces and can
   therefore be used interchangably in scripts.  The @b
   UnbinnedAnalysis constructor is defined as

@verbatim
class UnbinnedAnalysis(AnalysisBase):
    def __init__(self, observation, srcModel=None,  optimizer='Minuit'):
@endverbatim   

   and its parameters are

   - @b observation: An instance of the UnbinnedObs class.
   - @b srcModel: Name of the XML file containing the source model
     definition.
   - @b optimizer: Optimizer package to use: <tt>Minuit</tt>, 
     <tt>Drmngb</tt>, or <tt>Lbfgs</tt>

   The @b BinnedAnalysis constructor is identical except that it takes
   an instance of @b BinnedObs as the <tt>observation</tt> object.
   
   Factoring into separate analysis and observation classes affords
   flexibility in mixing and matching observations and models in a
   single Python session or script while preserving computational
   resources, so that one can do something like this:

@verbatim
>>> analysis1 = UnbinnedAnalysis(unbinnedObs, "model1.xml")
>>> analysis2 = UnbinnedAnalysis(unbinnedObs, "model2.xml")
@endverbatim

   Even though the two @b UnbinnedAnalysis instances access the
   same data in memory, distinct source models may be fit concurrently
   to those data without interfering with one another.  This will be
   useful in comparing, via a likelihood ratio test, for example, how
   well one model compares to another.

   @section command_line Starting up from the Python command line

   Here we perform an unbinned analysis. The steps that must be taken
   before proceeding, e.g., live-time, exposure and diffuse response
   calculations, are outlined in the <a
   href="http://glast-ground.slac.stanford.edu/workbook/science-tools/pages/sciTools_likelihoodTutorial/likelihoodTutorial.htm">unbinned
   analysis tutorial</a>.

   First, we import the data and analysis classes,
@verbatim
>>> from UnbinnedAnalysis import *
@endverbatim

   then we create an @b UnbinnedObs object:
@verbatim
>>> my_obs = UnbinnedObs(eventFiles, 'test_scData_0000.fits',
                         expMap='expMap.fits', expCube='expCube.fits',
                         irfs='TEST')
@endverbatim
   Here, <tt>eventFiles</tt> is an ascii file containing the names of
   the event files,
@verbatim
salathe[jchiang] cat eventFiles
eg_dif_filtered.fits
galdif_filtered.fits
ptsrcs_filtered.fits
salathe[jchiang] 
@endverbatim
   One could also have entered in a tuple or list if file names or use
   <tt>glob</tt> to generate the list.  For these data, the following 
   are equivalent to the above:
@verbatim
>>> my_obs = UnbinnedObs(('eg_dif_filtered.fits', 'galdif_filtered.fits',
                          'ptsrcs_filtered.fits'),
                         'test_scData_0000.fits', expMap='expMap.fits', 
                         expCube ='expCube.fits', irfs='DC1A')
                         
@endverbatim
or
@verbatim
>>> my_obs = UnbinnedObs(glob.glob('*filtered.fits'), 'test_scData_0000.fits',
                         expMap='expMap.fits', expCube='expCube.fits', 
                         irfs='DC1A')
@endverbatim

   One may omit all of the arguments in the @b UnbinnedObs class
   constructor, in which case a small GUI dialog is launched that
   allows one to browse the file system, use wild cards for specifying
   groups of files, etc..  So, entering
@verbatim
>>> my_obs = UnbinnedObs()
@endverbatim
   launches this dialog:

   @image html Obs_dialog0.png
   \n
   The buttons on the left will open file dialog boxes using the value
   shown in the text entry fields as a filter.  One can include wild
   cards or comma-separated lists of files in the text entry field.  
   Setting the entries as follows will create an @b UnbinnedObs 
   object equivalent to the previous examples:

   @image html Obs_dialog1.png

   \n
   Now we are ready to create an instance of @b UnbinnedAnalysis:

@verbatim
>>> analysis = UnbinnedAnalysis(my_obs, "srcModel.xml")
@endverbatim

   Here <tt>srcModel.xml</tt> is the xml file containing the model
   definition for Likelihood.

   Just as with the @b UnbinnedObs class, a small GUI is
   provided that allows one to browse the file system in case one
   omits the name of the model XML file. For example,

@verbatim
>>> analysis = UnbinnedAnalysis(my_obs)
@endverbatim
   launches

   @image html Analysis_dialog.png
   \n

   The @b UnbinnedObs and  @b UnbinnedAnalysis classes
   both have been implemented to allow one to see easily what data
   these objects comprise:

@verbatim
>>> print my_obs
Event file(s): ['ptsrcs_filtered.fits', 'galdif_filtered.fits', 'eg_dif_filtered.fits']
Spacecraft file(s): ['test_scData_0000.fits']
Exposure map: expMap.fits
Exposure cube: expCube.fits
IRFs: DC1A
>>> 
>>> print analysis
Event file(s): ['ptsrcs_filtered.fits', 'galdif_filtered.fits', 'eg_dif_filtered.fits']
Spacecraft file(s): ['test_scData_0000.fits']
Exposure map: expMap.fits
Exposure cube: expCube.fits
IRFs: DC1A
Source model file: srcModel.xml
Optimizer: Minuit
>>>
@endverbatim

   @section scripts Starting from a Python Script

It is convenient to prepare a script that creates the @b UnbinnedObs
and @b UnbinnedAnalysis objects with the proper parameter values so
that analysis of the data may be easily revisited in separate
sessions:

@verbatim
salathe[jchiang] cat my_anaylsis.py
import glob
from UnbinnedAnalysis import *

eventFiles = glob.glob('*filtered.fits')
obs = UnbinnedObs(eventFiles, 'test_scData_0000.fits', expMap='expMap.fits',
                  expCube='expCube.fits', irfs='DC1A')

like = UnbinnedAnalysis(obs, 'srcModel.xml')
salathe[jchiang]
@endverbatim

This just needs to be imported at the Python prompt:

@verbatim
salathe[jchiang] python
Python 2.3.3 (#1, Apr 24 2004, 23:59:52) 
[GCC 3.3.2 20031022 (Red Hat Linux 3.3.2-1)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> from my_analysis import *
@endverbatim

@section introspection Viewing and Setting Parameters, Plotting, Fitting, etc.

Python provides various means of introspection.  For example, the <tt>dir</tt>
command shows an object's attributes:
@verbatim
>>> dir(like)
['_Nobs', '__call__', '__class__', '__delattr__', '__dict__', '__doc__',
'__getattribute__', '__hash__', '__init__', '__module__', '__new__', 
'__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__str__', 
'__weakref__', '_errors', '_importPlotter', '_inputs', '_plotData', 
'_plotResiduals', '_plotSource', '_srcCnts', '_srcDialog', 'disp', 'e_vals', 
'energies', 'events', 'fit', 'freeze', 'logLike', 'model', 'nobs', 
'observation', 'oplot', 'optimizer', 'plot', 'resids', 'setPlotter', 
'sourceNames', 'thaw']
>>> 
@endverbatim

The objects themselves may also offer introspection. Both 
@b UnbinnedAnalysis and @b BinnedAnalysis objects have a
<tt>model</tt> attribute that allows one to view and manipulate the
current state of the various fit parameters.

To view the current model parameters, do 
@verbatim
>>> like.model
Extragalactic Diffuse
   Spectrum: PowerLaw
0      Prefactor:  1.450e+00  0.000e+00  1.000e-05  1.000e+02 ( 1.000e-07)
1          Index: -2.100e+00  0.000e+00 -3.500e+00 -1.000e+00 ( 1.000e+00) fixed
2          Scale:  1.000e+02  0.000e+00  5.000e+01  2.000e+02 ( 1.000e+00) fixed

Galactic Diffuse
   Spectrum: PowerLaw
3      Prefactor:  1.100e+01  0.000e+00  1.000e-03  1.000e+03 ( 1.000e-03)
4          Index: -2.100e+00  0.000e+00 -3.500e+00 -1.000e+00 ( 1.000e+00) fixed
5          Scale:  1.000e+02  0.000e+00  5.000e+01  2.000e+02 ( 1.000e+00) fixed

my_3EG_J0530p1323
   Spectrum: PowerLaw
6      Prefactor:  1.365e+01  0.000e+00  1.000e-05  1.000e+03 ( 1.000e-09)
7          Index: -2.460e+00  0.000e+00 -5.000e+00 -1.000e+00 ( 1.000e+00)
8          Scale:  1.000e+02  0.000e+00  3.000e+01  2.000e+03 ( 1.000e+00) fixed

my_3EG_J0534p2200
   Spectrum: PowerLaw
9      Prefactor:  2.700e+01  0.000e+00  1.000e-05  1.000e+03 ( 1.000e-09)
10         Index: -2.190e+00  0.000e+00 -5.000e+00 -1.000e+00 ( 1.000e+00)
11         Scale:  1.000e+02  0.000e+00  3.000e+01  2.000e+03 ( 1.000e+00) fixed

my_3EG_J0633p1751
   Spectrum: PowerLaw
12     Prefactor:  2.329e+01  0.000e+00  1.000e-05  1.000e+03 ( 1.000e-09)
13         Index: -1.660e+00  0.000e+00 -5.000e+00 -1.000e+00 ( 1.000e+00)
14         Scale:  1.000e+02  0.000e+00  3.000e+01  2.000e+03 ( 1.000e+00) fixed

>>> 
@endverbatim

The columns are 

- parameter index
- parameter name
- parameter value
- error estimate (zero before fitting)
- lower bound 
- upper bound 
- parameter scaling (in parentheses)
- fixed (or not)

By default, the <tt>plot()</tt> method uses pyROOT to create counts spectra
plots for comparing the model fits to the data.  The following creates
two plot windows, one for the counts spectra and one for the fractional
residuals of the fit:

@verbatim
>>> like.plot()
@endverbatim

@image html pyROOT_plot.png

\n

If HippoDraw is available, e.g., on SLAC linux boxes, then
the plotter can be changed to use it instead of pyROOT:
@verbatim
>>> like.setPlotter('hippo')
>>> like.plot()
@endverbatim

@image html hippo_plot.png

\n

One can set parameter values using the index:

@verbatim
>>> like.model[0] = 1.595
@endverbatim

optimizer::Parameter member functions are automatically dispatched to the
underlying C++ class from Python so that one can set the "free" flag, set
the bounds, and the scale factor

@verbatim
>>> like.model[1].setFree(1)
>>> like.model[3].setScale(1e-2)
>>> like.model[3] = 1.1
>>> like.model[3].setBounds(0.5, 2)
>>> like.model
Extragalactic Diffuse
   Spectrum: PowerLaw
0      Prefactor:  1.595e+00  0.000e+00  1.000e-05  1.000e+02 ( 1.000e-07)
1          Index: -2.100e+00  0.000e+00 -3.500e+00 -1.000e+00 ( 1.000e+00)
2          Scale:  1.000e+02  0.000e+00  5.000e+01  2.000e+02 ( 1.000e+00) fixed

Galactic Diffuse
   Spectrum: PowerLaw
3      Prefactor:  1.100e+00  0.000e+00  5.000e-01  2.000e+00 ( 1.000e-02)
4          Index: -2.100e+00  0.000e+00 -3.500e+00 -1.000e+00 ( 1.000e+00) fixed
5          Scale:  1.000e+02  0.000e+00  5.000e+01  2.000e+02 ( 1.000e+00) fixed

my_3EG_J0530p1323
   Spectrum: PowerLaw
6      Prefactor:  1.365e+01  0.000e+00  1.000e-05  1.000e+03 ( 1.000e-09)
7          Index: -2.460e+00  0.000e+00 -5.000e+00 -1.000e+00 ( 1.000e+00)
8          Scale:  1.000e+02  0.000e+00  3.000e+01  2.000e+03 ( 1.000e+00) fixed

my_3EG_J0534p2200
   Spectrum: PowerLaw
9      Prefactor:  2.700e+01  0.000e+00  1.000e-05  1.000e+03 ( 1.000e-09)
10         Index: -2.190e+00  0.000e+00 -5.000e+00 -1.000e+00 ( 1.000e+00)
11         Scale:  1.000e+02  0.000e+00  3.000e+01  2.000e+03 ( 1.000e+00) fixed

my_3EG_J0633p1751
   Spectrum: PowerLaw
12     Prefactor:  2.329e+01  0.000e+00  1.000e-05  1.000e+03 ( 1.000e-09)
13         Index: -1.660e+00  0.000e+00 -5.000e+00 -1.000e+00 ( 1.000e+00)
14         Scale:  1.000e+02  0.000e+00  3.000e+01  2.000e+03 ( 1.000e+00) fixed@endverbatim

Now, perform a fit, suppressing Minuit's screen output; the resulting value 
<tt>-log(Likelihood)</tt> is returned:

@verbatim
>>> like.fit(verbosity=0)
60552.466249687997
@endverbatim

Overplot the new result in red, the default:

@verbatim
>>> like.oplot()
@endverbatim

@image html hippo_plot_2.png
\n

A specific source can be accessed by its full name or by a fragment thereof:

@verbatim
>>> print model["633"]
my_3EG_J0633p1751
   Spectrum: PowerLaw
12     Prefactor:  2.897e+01  2.360e+00  1.000e-05  1.000e+03 ( 1.000e-09)
13         Index: -1.877e+00  4.136e-02 -5.000e+00 -1.000e+00 ( 1.000e+00)
14         Scale:  1.000e+02  0.000e+00  3.000e+01  2.000e+03 ( 1.000e+00) fixed@endverbatim

The <tt>logLike</tt> attribute is a Likelihood::LogLike object, and so its
member functions are exposed as Python methods:

@verbatim
>>> like.logLike.writeXml("fitted_model.xml")
@endverbatim
*/

