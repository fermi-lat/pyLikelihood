# pyLikelihood SWIG interface

The whole module is defined by one file, `src/pyLikelihood.i` (712
lines). This page lists what it exposes, from which package, and the
helper code it adds. Line references are to commit 65657a8.

## Structure of `pyLikelihood.i`

1. `%{ … %}` holds the C++ `#include`s compiled into the wrapper. The
   Likelihood headers are grouped in dependency order. This block also
   defines `class StAppInterface : public st_app::StApp`, a do-nothing
   application used to open a par file (see `StApp.parGroup` below). It
   then has `using` declarations for `optimizers::Parameter`,
   `ParameterNotFound`, `Function`, `Exception`.
2. `%include stl.i` and the **string typemaps** (accept `os.PathLike`).
3. The global **`%exception`** block.
4. **`%template`** instantiations of the STL types used in signatures.
5. **`%include`** of each wrapped header, in the same dependency order as
   the `#include`s. SWIG needs base classes and by-value types declared
   before use.
6. **`%extend`** blocks that add Python-only methods.

`%feature("autodoc", "1")` is switched on **after** the `st_app` and
`astro` `%include`s. Classes from those two packages therefore have no
generated signature docstrings, and everything after them does.

## What is wrapped from where

This is the authoritative list. "`%include`" means SWIG generates Python
classes and functions for the header. "`#include` only" means the
wrapper compiles against the header (for `%extend` code or as a
dependency) but generates no Python API for it.

| Package | `%include`d (Python API generated) | `#include` only |
|---------|-------------------------------------|-----------------|
| `st_app` | `AppParGroup.h`, `StApp.h` | — |
| `astro` | `ProjBase.h`, `SkyProj.h`, `HealpixProj.h`, `SkyDir.h`, `JulianDate.h`, `SolarSystem.h` | — |
| `dataSubselector` | `CutBase.h`, `BitMaskCut.h`, `Cuts.h` | — |
| `healpix` | `CosineBinner.h` | — |
| `map_tools` | `Exposure.h`, `SkyImage.h` | — |
| `optimizers` | `Arg.h`, `dArg.h`, `Parameter.h`, `Function.h`, `Statistic.h`, `FunctionTest.h`, `FunctionFactory.h`, `Optimizer.h`, `OptimizerFactory.h`, `Mcmc.h`, `Minuit.h`, `NewMinuit.h` | `ParameterNotFound.h` |
| `st_facilities` | `FitsImage.h`, `Util.h` | — |
| `irfs` | `irfInterface/IEfficiencyFactor.h` | `irfInterface/IrfsFactory.h`, `irfLoader/Loader.h` (also `irfInterface/Irfs.h` via `Aeff.h`) |
| `st_stream` | — | `st_stream.h` (for `initOutputStreams`) |
| CLHEP | — | `Random/RandFlat.h`, `Random/Random.h` (for `Util.setRandomSeed`/`shoot`) |
| `pyLikelihood` | `Aeff.h` (`pyLikelihood.Aeff(irfName)(energy, theta, convtype, phi)`), `enableFPE.h` (`pyLikelihood.enableFPE()`) | — |
| `Likelihood` | 89 headers, listed below | — |

The following are **not** Python classes, even though some package docs
say they are wrapped: `irfInterface::Irfs`, `IrfsFactory`,
`irfLoader::Loader` and `optimizers::ParameterNotFound`. A SWIG 4.5 build
has no `pyLikelihood.IrfsFactory`, `Irfs`, `Loader_go` or
`ParameterNotFound` (confirmed at runtime). Python users who need IRFs
use `pyIrfLoader` from the `irfs` package.

### Likelihood headers (89), in `%include` order

- **No other Likelihood dependencies:**
  - `AppHelpers`, `BinnedConfig`, `Convolve`, `DiffRespIntegrand`,
    `Drm`, `Exception`, `EquinoxRotation`
  - `ExposureCube`, `ExposureMap`, `FileFunction`, `FitScanner`,
    `FitUtils`, `GaussianError`, `ModelMap`, `ProjMap`
  - `ResponseFunctions`, `RoiCuts`, `ScaleFactor`, `ScanUtils`, `ScData`,
    `SkyDirArg`, `SkyDirFunction`, `Snapshot`, `SparseVector`, `TrapQuad`,
    `TiedParameter`, `WcsMapLibrary`, `WeightMap`
  - spectral functions: `BrokenPowerLaw2`, `BrokenPowerLaw3`,
    `BrokenPowerLawExpCutoff`, `DMFitFunction`, `ExpCutoff`,
    `ExpCutoffSEDPeak`, `LogGaussian`, `LogNormal`, `LogNormalLog`,
    `LogParabola`, `MultipleBrokenPowerLaw`, `SmoothBrokenPowerLaw`,
    `SmoothDoubleBrokenPowerLaw`, `PiecewisePowerLaw`,
    `PowerLawSuperExpCutoff` (and `…2`, `…3`, `…4`), `PowerLaw2`
- **Next tier:** `BinnedExposureBase`, `Event`, `FileUtils`,
  `HealpixProjMap`, `MapBase`, `Pixel`, `SourceMap`, `WcsMap2`
- **Then:** `BinnedExposure`, `BinnedHealpixExposure`, `EventContainer`,
  `MapCubeFunction2`, `PSFUtils`, `SpatialMap`
- **Core:** `CountsMapBase`, `Source`, `SrcArg`, `Observation`
- **Depend on the core:** `BinnedCountsCache`, `CountsMap`,
  `CountsMapHealpix`, `DiffuseSource`, `MeanPsf`, `Npred`,
  `OneSourceFunc`, `PointSource`, `SpatialFunction`, `SourceFactory`,
  `SourceMapCache`, `SourceModel`
- **Then:** `CompositeSource`, `ConvolveHealpix`, `RadialProfile`,
  `RadialDisk`, `RadialGaussian`
- `LogLike`
- **`LogLike` subclasses:** `BinnedLikelihood`, `Composite2`,
  `CompositeLikelihood`, `OptEM`, `SummedLikelihood`
- `CountsSpectra`

Many spectral functions are **not** wrapped as classes, for example
`PowerLaw` (a private class in `optimizers/src`), `BandFunction` and
`EblAtten`. They are still available
from Python as `optimizers::Function` objects through
`SourceFactory.funcFactory().create(name)` and XML models. Their
parameters are reached through the generic `Function` interface.

### `%template` instantiations

- **Pairs:** `DoublePair`, `IntPair`, `SkyDirPair`, `FuncPair`,
  `DoubleVectorPair`, `ParamPair_t` (`pair<LogLike*, size_t>`)
- **Vectors:** `DoubleVector`, `FloatVector`, `BoolVector`, `SizetVector`,
  `StringVector`, `DoubleVectorVector`, `FloatVectorVector`,
  `EventVector`, `SkyDirVector`, `BitMaskCutVector`, `ArgVector`,
  `ParameterVector`, `PixelVector`, `ParVector_t`
- **Map:** `FuncMap` (`map<string, Function*>`)
- **Sparse vectors:** `SparseIntVector`, `SparseFloatVector`,
  `SparseDoubleVector`

C++ methods that fill a vector through a reference argument need one of
these objects passed in. For example:

```python
v = pyLike.StringVector()
like.logLike.getSrcNames(v)
```

## `%extend` helpers

| Class | Added member | What it does |
|-------|--------------|--------------|
| `LogLike` | `initOutputStreams(maxChatter=2)` | `st_stream::OStream::initStdStreams()` + `SetMaximumChatter`. Without it, C++ output is lost. |
| `LogLike` | static `enableFPE()` | Calls `pyLikelihood::enableFPE()`. |
| `LogLike` | static `set_ScaleFactor_complement(func, flag)` | `dynamic_cast` to `ScaleFactor`. |
| `LogLike` | `print_source_params()`, `src_param_table()` | Print to `std::cout` (not `st_stream`). |
| `LogLike` | `getNumFreeParams()`, `getFreeParamValues(vec)`, `srcNames()` | Convenience wrappers; `srcNames()` returns a list. |
| `LogLike` | `Mcmc()` | Returns a new `optimizers::Mcmc(*this)`. |
| `BinnedLikelihood` | `modelCounts(srcName)` | Per-pixel model counts for one source, **only in pixels with data** (zero elsewhere). |
| `Source` | `flux()`, `flux(emin, emax, npts=100)` | Dispatches to `PointSource` or `DiffuseSource`. A `CompositeSource` would hit the `DiffuseSource` branch with a null pointer (from reading the code; not checked at runtime). |
| `PointSource`, `DiffuseSource`, `CompositeSource` | static `cast(Source*)` | Checked downcast; throws `RuntimeError` on failure. |
| `SpatialMap`, `FileFunction`, `PiecewisePowerLaw` | static `cast(Function*)` | Checked downcast. |
| `Minuit`, `NewMinuit` | static `cast(Optimizer*)` | Checked downcast, to reach `getQuality`, `getDistance`, `Minos`, … |
| `SourceFactory` | static `funcFactory()` | New `FunctionFactory` with every Likelihood function prototype registered (`AppHelpers::addFunctionPrototypes`). This is the factory `readXml` needs. |
| `ResponseFunctions` | `load_with_event_types(irfs, base, file, extname)` | Strips any `" (…)"` suffix from the IRF name, reads the DSS event-type selection from the file, and loads one response per selected event type. |
| `EquinoxRotation` | `fromMapCoords(dir)`, `toMapCoords(dir)` | Wrap `do_rotation`. |
| `DiffRespIntegrand` | static `srcDir(mu, phi, eqRot)` | Out-parameter → return value. |
| `Event` | `ra_dec()`, `sc_dir()` | Return `(ra, dec)` pairs. |
| `st_facilities::Util` | static `resolveFitsFiles(infile)`, `skyDir2pixel(proj, dir)`, `pixel2SkyDir(proj, i, j)`, `setRandomSeed(seed)`, `shoot()` | Out-parameter wrappers; CLHEP random access. `setRandomSeed` constructs a temporary `HepRandom(seed)`, which may not reseed the global engine as intended (from reading the code; not checked at runtime). |
| `st_app::StApp` | static `parGroup(appName)` | Runs `StApp::processCommandLine` with a dummy `argv`, builds a `StAppInterface(appName)` and returns a **copy** of its `AppParGroup`. This opens `<appName>.par` through `PFILES`. |
| `st_app::AppParGroup` | `__getitem__`, `getDouble`, `getInt`, `getBool`, `Save()` | Typed parameter access from Python. |
| `map_tools::Exposure` | `data(skyDir)` | The `CosineBinner` for one sky direction. |
| `healpix::CosineBinner` | `costheta(i)`, `__getitem__(i)` | Bounds-checked (throws `RuntimeError("IndexError")`, not `IndexError`). |
| `optimizers::Parameter` | `setEquals(rhs)` | Python stand-in for `operator=`. |

## Typemaps

- **Strings and paths** (added in 65657a8): for `std::string` and
  `const std::string &` arguments, the typecheck accepts `str`, `bytes`
  or any object with `__fspath__`, and the in-typemap calls
  `PyOS_FSPath` and then UTF-8 decodes. The `freearg` typemap is emptied
  because the standard one refers to variables these typemaps don't
  define. This applies to every wrapped function taking a string, in
  every package. It does not apply to `std::vector<std::string>`
  arguments: pass a `StringVector` or a list of `str`. The installed
  builds checked for this review predate the change, so the typemaps are
  verified by reading only.
- Branch `origin/py-stable-abi` (unmerged) changes the macros
  `PyBytes_AS_STRING`/`GET_SIZE` to the Limited-API functions and links
  `Python3::SABIModule`. That is a step toward a Python-version-independent
  `abi3` module.

## Exception mapping

```c++
%exception {
   try { $action }
   catch (std::exception & eObj) {
      PyErr_SetString(PyExc_RuntimeError, eObj.what()); return NULL;
   }
}
```

- Every `std::exception`, including `std::invalid_argument`,
  `hoops::Hexception`, `tip::TipException` and `optimizers::Exception`
  subclasses, reaches
  Python as **`RuntimeError`**, with no type information. Python code in
  `python/` therefore catches `RuntimeError` and sometimes matches on the
  message.
- Anything not derived from `std::exception` is not caught, and the
  interpreter aborts. Fermi's own exception types (`hoops::Hexception`,
  `tip::TipException`, `optimizers::Exception`) all derive from it.
- Exceptions thrown during **library load** (static initializers in
  `irfLoader`) are outside any wrapper and always abort.

## SWIG version constraints

| Requirement | Where | Effect |
|-------------|-------|--------|
| `find_package(SWIG 3.0.1 REQUIRED COMPONENTS python)` | top-level `CMakeLists.txt` | Nominal minimum. |
| `swig>=4.1` | `recipe/meta.yaml`, `environments/fermitools-develop-*.yml` | What the conda builds actually use (a 2026 dev environment has 4.5.0). |
| `UseSWIG_TARGET_NAME_PREFERENCE STANDARD` | here and top level | The CMake target is `pyLikelihood`, and its output is `_pyLikelihood.so`. |

**The SWIG 4.1 break.** Since 4.1, SWIG no longer creates the flat
module-level aliases `Class_staticMethod` (the old default,
`-flatstaticmethod`, is now off). Static methods exist only as
`Class.staticMethod`. The low-level `_pyLikelihood.Class_staticMethod`
C functions still exist. Commits 29ac68e, e612f5d and e09f247 (July–August
2026) moved the main modules to the new spelling. They also restored the
`%extend SourceFactory { static funcFactory() }` form, replacing an
`%inline` free function `SourceFactory_funcFactory` that had been added
as a workaround (it remains, commented out, in the `.i`). Code still
using flat names fails with `AttributeError` on current builds; the list
is in the README's gotchas. Code that must run on both old and new builds
can use `pyLike.SourceFactory.funcFactory()` (works on 4.0 and later) or
`pyLike._pyLikelihood.SourceFactory_funcFactory()` (works on every
version, as `UnbinnedAnalysis.py` does).

To test the generated Python API without building, look at the installed
`site-packages/fermitools/pyLikelihood.py`. Its header records the SWIG
version that generated it.
