# pyLikelihood Python layer

The modules in `python/` are installed flat into
`site-packages/fermitools/`. That directory is on `sys.path` through
`fermitools.pth`, so they are imported top-level (`import
UnbinnedAnalysis`, not `from fermitools import …`). Inside the package
they import each other the same way (`from SrcModel import SourceModel`).

## Analysis workflow

### 1. Observation objects

```python
# Unbinned: events + spacecraft file + (optional) exposure map + livetime cube
from UnbinnedAnalysis import UnbinnedObs, UnbinnedAnalysis
obs = UnbinnedObs(eventFile, scFile, expMap=None, expCube=None,
                  irfs='CALDB', checkCuts=True, sctable='SC_DATA')

# Binned: gtsrcmaps output + livetime cube + binned exposure (gtexpcube2)
from BinnedAnalysis import BinnedObs, BinnedAnalysis, BinnedConfig
obs = BinnedObs(srcMaps='srcmaps.fits', expCube='ltcube.fits',
                binnedExpMap='bexpmap.fits', irfs='CALDB',
                phased_expmap=None)
```

- **`eventFile`/`scFile` formats.** Each can be a single name, a `@list`
  text file, a list of names, or a `pathlib.Path`.
  `pyLike.Util.resolveFitsFiles` expands lists (see
  `src/st_facilities/doc/architecture/`).
- **`irfs=None` or `'CALDB'`.** The IRF name is read from the first event
  file's DSS keywords (or the source-maps file's) through
  `pyLike.Cuts(file, ext, False, True, True).CALDB_implied_irfs()` (see
  `src/dataSubselector/doc/architecture/dss-keywords.md`). The response is
  then loaded once per selected event type with
  `ResponseFunctions.load_with_event_types`.
- **`checkCuts=True`** (unbinned only) checks that all event files carry
  the same DSS cuts, and that the exposure map and livetime cube match
  them. Mismatches raise `RuntimeError`.
- **Spacecraft data.** `UnbinnedObs` reads FT2 only over the ROI time
  range. It **clears the spacecraft arrays** after reading the events if a
  livetime cube is given, to save memory.
- **Binned exposure.** `BinnedObs` validates the binned exposure map
  against the source-maps file (`AppHelpers.checkExposureMap`). It reads
  the counts map and exposure with `AppHelpers.readCountsMap`/
  `readBinnedExposure`, which pick WCS or HEALPix. It also builds a
  `MeanPsf` at the counts-map reference direction.

### 2. Analysis objects

```python
like = UnbinnedAnalysis(obs, 'model.xml', optimizer='NewMinuit', nee=21)
like = BinnedAnalysis(obs, 'model.xml', optimizer='NewMinuit',
                      config=BinnedConfig(edisp_bins=-1), wmap=None,
                      psfcorr=True, delete_local_fixed=False)
```

- **Optimizer.** It is a name that `optimizers::OptimizerFactory`
  understands: `Minuit`, `NewMinuit`, `Drmngb`, `Drmnfb`, `Lbfgs` or
  `Powell` (case variants such as `MINUIT` are also accepted). See
  `src/optimizers/doc/architecture/minimizers.md`. The default is
  `'Drmngb'`. `Mcmc` is not a factory name; get it with
  `logLike.Mcmc()`.
- **Model loading.** The constructor loads the XML model with the
  module-level `_funcFactory` (`SourceFactory.funcFactory()`). The
  unbinned path calls `readXml(…, requireExposure=True, …)` and then
  `computeEventResponses()`; the binned path uses
  `requireExposure=False`.
- **`BinnedConfig(**kwargs)`** builds a `pyLike.BinnedLikeConfig`. Its
  keywords are `computePointSources`, `applyPsfCorrections`,
  `performConvolution`, `resample`, `resamp_factor`, `minbinsz`,
  `integ_type`, `psfEstimatorFtol`, `psfEstimatorPeakTh`, `verbose`,
  `edisp_bins`, `use_single_fixed_map`, `use_linear_quadrature`,
  `save_all_srcmaps`, `use_single_psf`, `load_existing_srcmaps`,
  `delete_local_fixed` and `no_cached_weightmaps`.
  - If `config` is passed, the `psfcorr`, `delete_local_fixed` and
    `no_cached_weightmaps` constructor arguments are ignored.
  - `use_bl2=True` raises: BinnedLikelihood2 was removed in 2016.
- **`wmap`** names a weights map. It is loaded through
  `WcsMapLibrary.instance().wcsmap(wmap, "")` with interpolation off and
  extrapolation on.
- **Convenience functions.** `unbinnedAnalysis(mode='ql', **pars)` and
  `binnedAnalysis(...)` read the missing parameters from `gtlike.par`,
  prompting in `ql` mode, and then **save** the par file. They set
  `like.tol` from `ftol`. `binnedAnalysis()` is broken on SWIG ≥ 4.1
  builds (see the README gotchas).

### 3. Inspecting and changing the model

```python
like.sourceNames()
like.model                       # SourceModel; print(like.model) lists everything
like['MySrc']                    # SrcModel.Source view (.src is the C++ Source)
i = like.par_index('MySrc', 'Prefactor')
like[i]                          # SrcModel.Parameter (flat index over all sources)
like[i] = 3.0                    # set value and sync to C++
like.freeze(i); like.thaw([i, i+1])
like.normPar('MySrc')            # the spectrum's normalization Parameter
like.freePars('MySrc')
like.setFreeFlag('MySrc', like.freePars('MySrc'), False)
like.setSpectrum('MySrc', 'LogParabola')
like.addSource(src); like.deleteSource('MySrc')
like.setEnergyRange(emin, emax)  # unbinned: set_ebounds; binned: snaps to bin edges (set_klims)
```

- **Flat parameter index.** The index used by `like[i]`, `freeze`,
  `thaw` and `par_index` is SourceModel's flat index. It is built by
  walking every source's functions in order (`SourceModel._walk`), and it
  is rebuilt whenever a source is added or deleted. After `addSource` or
  `deleteSource`, look indices up again with `par_index`.
- **Syncing to C++.** Changes made through `SrcModel.Parameter` set
  `is_modified`. `AnalysisBase.__setitem__` and `freeze`/`thaw` sync at
  once. `fit`, `optimize` and `__call__` call `syncParams()` before
  evaluating. If you change a C++ `optimizers::Parameter` directly
  (`like['MySrc'].src.spectrum().parameter('Index')`), call
  `like.syncSrcParams('MySrc')` yourself.

### 4. Fitting

```python
negLogL = like.fit(verbosity=0, tol=None, optimizer=None, covar=True,
                   optObject=None, numericDerivs=False)
like.optimize(verbosity=0)           # minimize only: no errors, no covariance
like.minosError('MySrc', 'Index')    # Minuit/NewMinuit only
like.covariance                      # list of lists, set when covar=True
like.optObject.getRetCode()          # optimizer of the last fit
like.setFitTolType(pyLike.RELATIVE)  # default ABSOLUTE (=1); RELATIVE is 0
```

- **What `fit()` does.** It creates a **new optimizer object every
  call** (unless `optObject` is given) and calls
  `find_min(verbosity, tol, tolType)` and `getUncertainty()`. It writes
  the errors back to the free parameters and returns `-logLike.value()`
  (a positive number for a good fit).
- **Return codes and `fit()`.** It does not raise on a non-zero optimizer
  return code. Check `like.optObject.getRetCode()` (meaning depends on the
  optimizer; see `src/optimizers/doc/architecture/`).
- **`like()`** returns the current `-logL`.

### 5. Test statistics, fluxes, upper limits, SEDs

```python
like.Ts('MySrc', reoptimize=False, approx=True)
like.flux('MySrc', emin=100, emax=3e5); like.fluxError('MySrc', 100, 3e5)
like.energyFlux('MySrc'); like.energyFluxError('MySrc')

from LikelihoodState import LikelihoodState
saved = LikelihoodState(like); ...; saved.restore()   # or restore('MySrc')

from UpperLimits import UpperLimits
ul = UpperLimits(like); ul['MySrc'].compute(emin=100, emax=3e5)  # profile, delta=2.71/2

import IntegralUpperLimit
ul_flux, results = IntegralUpperLimit.calc_int(like, 'MySrc', cl=0.95)   # Bayesian
ul_flux, results = IntegralUpperLimit.calc_chi2(like, 'MySrc', cl=0.95)  # profile

from SED import SED
sed = SED(like, 'MySrc', bin_edges=None, ul_algorithm='bayesian', min_ts=4)
sed.save('sed.dat'); sed.plot('sed.png'); sed.todict()

from FluxDensity import FluxDensity       # needs like.fit(covar=True) first
```

- **`Ts`** deletes the source and either renormalizes the nearby or
  diffuse sources (`approx=True`, the default, which uses `_renorm`) or
  re-optimizes (`reoptimize=True`, up to `MaxIterations`). It returns
  `2·(logL_with − logL_without)`, re-adds the source and restores the
  parameters with `LikelihoodState`. The `like.model` view is rebuilt.
- **`UpperLimits`** scans the normalization with a quadratic fit to
  `ΔlogL` until it reaches `delta`. While scanning it **freezes** the
  normalization and calls `saveCurrentFit`. The original state is
  restored afterwards. The `tmpfile` argument is unused.
- **`IntegralUpperLimit.calc_int`** integrates the likelihood over the
  normalization (uniform prior), using scipy `quad` and splines.
  - It returns `(-1, {})` on failure.
  - `calc()` is a deprecated alias.
  - It uses only the Python-level API, so it also works with
    `SummedLikelihood`.
- **`SED`** freezes the background (by default), fixes the source index
  at `powerlaw_index` and fits each energy band. Its docstring says it
  needs a binned analysis. It imports `pylab` at import time, so
  matplotlib must be installed even if you never plot.
- **`FluxDensity`** computes dN/dE and its 1σ error from the covariance
  matrix. It raises if `like.covariance` is `None` or does not match the
  number of free parameters.

### 6. Priors

`addPrior`, `addGaussianPrior`, `setPriorParams`, `removePrior(s)`,
`getPriors`, `addPriors`, `constrain_norms`/`constrain_params` (Gaussian
priors from the current covariance) and `writePriorsYaml`/
`readPriorsYaml` all go through the C++ `LogLike` prior API. See
`src/Likelihood/doc/architecture/`.

`readPriorsYaml` calls `yaml.load(open(filename))` without a `Loader`.
Since PyYAML 6 (6.0.3 is in the conda environment) that raises
`TypeError`. The `yaml.load` behaviour was confirmed at runtime;
`readPriorsYaml` itself was not run.

### 7. Joint fits

```python
from SummedLikelihood import SummedLikelihood
summed = SummedLikelihood(optimizer='NewMinuit')
summed.addComponent(like_psf0); summed.addComponent(like_psf1)
summed.fit(covar=True); summed.Ts('MySrc')
```

- **`SummedLikelihood` shares one model by name.**
  - All components must contain the same sources.
  - Parameters are addressed through the first component's model.
  - Setting a parameter (`summed[i] = x`, `freeze`, `thaw`) updates every
    component through a `SummedLikelihood.Parameter` that wraps the
    matching parameters.
  - `fit`/`__call__` also store a best-fit snapshot (`saveBestFit`).
- **`Composite2`** fits independent models with tied parameters:
  `tieParameters([(like1, src, par), (like2, src, par)])`.
- **`CompositeLikelihood`** stacks one named source across components:
  `addComponent(srcName, like)`.

### 8. Output

- `writeXml(file)` writes the model. With no argument it **overwrites
  the original model file**.
- `writeCountsSpectra(file)`.
- `BinnedAnalysis.writeModelMap(file, outtype='CCUBE')`.
- `state(file)` writes a Python script that rebuilds the objects.
- `plot()` plots counts spectra and residuals through matplotlib.

### Raw `pyLikelihood` use

Code that bypasses the Python classes must do by hand what they do:
- keep the Obs-level C++ objects alive
- call `logLike.initOutputStreams()`
- pass `pyLike.SourceFactory.funcFactory()` to `readXml`
- call `syncParams()` after changing parameters
- create an optimizer with
  `pyLike.OptimizerFactory.instance().create(name, logLike)`

## Module status

Import checks were made against an FT-2.5.1 conda environment with this
commit's `python/` placed first on `sys.path`. Runtime fits used
`Likelihood`'s binned test-suite data. This counts as confirmed at runtime
unless noted.

| Module | Status |
|--------|--------|
| `AnalysisBase` | Works. Base of the unbinned, binned and summed classes. `_srcDialog` (no model file given) raises `NameError`. |
| `UnbinnedAnalysis` | Works for normal use. `UnbinnedObs()` with no files hits the dead Tk dialog (`NameError`). `UnbinnedObs.state()` has a `pepr` typo (from reading the code). |
| `BinnedAnalysis` | Works: binned fit, `Ts`, freeze, `LikelihoodState` restore, `state()` and `plot()` exercised. `binnedAnalysis()` uses the removed flat name `StApp_parGroup`. |
| `SummedLikelihood` | Imports; used by the Likelihood test suite and fermipy. Not exercised here. |
| `Composite2`, `CompositeLikelihood` | Import. Rarely used. Not exercised. |
| `SrcModel`, `LikelihoodState` | Work (used by everything above). |
| `UpperLimits`, `IntegralUpperLimit` | Import; `IntegralUpperLimit` is exercised by Likelihood's `test_UpperLimit.py`. The `__main__` block of `UpperLimits.py` uses `hippoplotter` and a nonexistent `analysis` module. |
| `SED` | Imports (needs matplotlib). Not exercised. |
| `FluxDensity` | Imports. Not exercised. |
| `MPLPlot` | **The working plotter** and the default (`_plotter_package = 'mpl'`). |
| `HippoPlot` | Dead. HippoDraw was Python 2 only. The module imports (it imports `hippoplotter` lazily), but `setPlotter('hippo')` and `setPlotter()` fail with `ModuleNotFoundError`. |
| `RootPlot` | Imports `ROOT` at module load. PyROOT is not in the conda environment, so `setPlotter('root')` followed by `plot()` raises `RuntimeError`. It would only work with a user-installed PyROOT; `ST-unit-test`'s RootPlot check is commented out. |
| `SimpleDialog` | Imports (tkinter), but its consumers are broken: no `map` is defined, so their guarded imports fail and the `MyOrderedDict`/`Param` names are missing. |
| `SrcAnalysis` | Legacy 2005 predecessor of `UnbinnedAnalysis` (HippoDraw plots, flat SWIG names `AppHelpers_checkCuts`, `is not ""` SyntaxWarnings). Imports, but its constructor fails on current builds (from reading the code). |
| `ST_Version` | Git-describe version helper from SCons-era unit tests. No callers in `src/`. |
| `package_paths` | Dead (SwigPolicy). `import` fails: `No module named 'swig_setup'`. |
| `test_model` | Manual derivative checker for spectral functions. Uses `FileFunction_cast`. Not run by anything. |

## Runtime Python dependencies

These come from the conda environment, not from this package's CMake:
- `numpy`: nearly everything
- `scipy`: `IntegralUpperLimit`, `SED`
- `matplotlib`/`pylab`: `MPLPlot`, `SED`
- `pyyaml`: `AnalysisBase` imports it at module load
- `tkinter`: `SimpleDialog`

An environment without numpy, such as a minimal development build, can
`import pyLikelihood` but not `UnbinnedAnalysis` (confirmed at runtime).

## Python 2 remnants

- `SrcModel._convertType` returns `bytes` for string-valued extra XML
  attributes.
- Bare `except:` around `open()` in the `state()` methods.
- `$Header$` CVS keywords, and comments about `hippoplotter`/HippoDraw.
- `HippoPlot`, `package_paths` and `SrcAnalysis` as above.
- `print (...)` with a space everywhere: converted from Python 2 `print`
  statements. Many of them are unconditional diagnostic prints (`"Resid
  "`, `"srcName "` in `AnalysisBase.plot`, and `"adding "` in
  `SourceModel.add`, which also swallows every exception with a bare
  `except: pass`).
