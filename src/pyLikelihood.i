// -*- mode: c++ -*-
// $Header: /nfs/slac/g/glast/ground/cvs/ScienceTools-scons/pyLikelihood/src/pyLikelihood.i,v 1.32 2015/01/08 21:40:32 jchiang Exp $
%module pyLikelihood
%{
#ifdef TRAP_FPE
#include <fenv.h>
#endif
#include <cstddef>
#include "CLHEP/Random/RandFlat.h"
#include "CLHEP/Random/Random.h"
#include "astro/SolarSystem.h"
#include "st_app/AppParGroup.h"
#include "st_app/StApp.h"
#include "st_stream/st_stream.h"
#include "irfLoader/Loader.h"
#include "irfInterface/IEfficiencyFactor.h"
#include "irfInterface/IrfsFactory.h"
#include "dataSubselector/BitMaskCut.h"
#include "dataSubselector/CutBase.h"
#include "dataSubselector/Cuts.h"
#include "healpix/CosineBinner.h"
#include "map_tools/Exposure.h"
#include "map_tools/SkyImage.h"
#include "optimizers/Optimizer.h"
#include "optimizers/OptimizerFactory.h"
#include "optimizers/Parameter.h"
#include "optimizers/ParameterNotFound.h"
#include "optimizers/Function.h"
#include "optimizers/FunctionFactory.h"
#include "optimizers/FunctionTest.h"
#include "optimizers/Mcmc.h"
#include "optimizers/Minuit.h"
#include "optimizers/NewMinuit.h"
#include "optimizers/Statistic.h"
#include "st_facilities/FitsImage.h"
#include "st_facilities/Util.h"
#include "Likelihood/AppHelpers.h"
#include "Likelihood/BinnedExposure.h"
#include "Likelihood/BrokenPowerLaw2.h"
#include "Likelihood/CompositeLikelihood.h"
#include "Likelihood/Composite2.h"
#include "Likelihood/Convolve.h"
#include "Likelihood/CountsSpectra.h"
#include "Likelihood/Source.h"
#include "Likelihood/DiffRespIntegrand.h"
#include "Likelihood/DiffuseSource.h"
#include "Likelihood/Drm.h"
#include "Likelihood/DMFitFunction.h"
#include "Likelihood/Drm.h"
#include "Likelihood/EquinoxRotation.h"
#include "Likelihood/Event.h"
#include "Likelihood/EventContainer.h"
#include "Likelihood/ExpCutoff.h"
#include "Likelihood/BrokenPowerLawExpCutoff.h"
#include "Likelihood/BrokenPowerLaw3.h"
#include "Likelihood/ExposureCube.h"
#include "Likelihood/ExposureMap.h"
#include "Likelihood/FileFunction.h"
#include "Likelihood/LogGaussian.h"
#include "Likelihood/LogNormalLog.h"
#include "Likelihood/LogParabola.h"
#include "Likelihood/MapBase.h"
#include "Likelihood/MapCubeFunction2.h"
#include "Likelihood/MeanPsf.h"
#include "Likelihood/ModelMap.h"
#include "Likelihood/Npred.h"
#include "Likelihood/OneSourceFunc.h"
#include "Likelihood/OptEM.h"
#include "Likelihood/PointSource.h"
#include "Likelihood/PowerLawSuperExpCutoff.h"
#include "Likelihood/PowerLaw2.h"
#include "Likelihood/ResponseFunctions.h"
#include "Likelihood/RoiCuts.h"
#include "Likelihood/ScaleFactor.h"
#include "Likelihood/ScData.h"
#include "Likelihood/SkyDirArg.h"
#include "Likelihood/SkyDirFunction.h"
#include "Likelihood/SourceFactory.h"
#include "Likelihood/SourceModel.h"
#include "Likelihood/SourceMap.h"
#include "Likelihood/SpatialMap.h"
#include "Likelihood/SrcArg.h"
#include "Likelihood/SummedLikelihood.h"
#include "Likelihood/TrapQuad.h"
#include "Likelihood/TiedParameter.h"
#include "Likelihood/Exception.h"
#include "Likelihood/LogLike.h"
#include "Likelihood/BinnedLikelihood.h"
#include "Likelihood/BinnedLikelihood2.h"
#include "Likelihood/Pixel.h"
#include "Likelihood/CountsMap.h"
#include "Likelihood/Observation.h"
#include "Likelihood/WcsMap2.h"
#include "pyLikelihood/Aeff.h"
#include "pyLikelihood/enableFPE.h"
#include <vector>
#include <string>
#include <exception>

class StAppInterface : public st_app::StApp {
public:
   StAppInterface(const std::string & appName)
      : st_app::StApp(), m_appName(appName) {}

   virtual ~StAppInterface() throw() {}

   virtual void run() {}

   st_app::AppParGroup & getParGroup() {
      return st_app::StApp::getParGroup(m_appName);
   }
private:
   const std::string m_appName;
};

using optimizers::Parameter;
using optimizers::ParameterNotFound;
using optimizers::Function;
using optimizers::Exception;
%}
%include stl.i
%exception {
   try {
      $action
   } catch (std::exception & eObj) {
      PyErr_SetString(PyExc_RuntimeError, const_cast<char *>(eObj.what()));
      return NULL;
   }
}
%template(DoublePair) std::pair<double, double>;
%template(IntPair) std::pair<int, int>;
%template(EventVector) std::vector<Likelihood::Event>;
%template(DoubleVector) std::vector<double>;
%template(FloatVector) std::vector<float>;
%template(DoubleVectorVector) std::vector< std::vector<double> >;
%template(DoubleVectorPair) std::vector< std::pair<double, double> >;
%template(FloatVectorVector) std::vector< std::vector<float> >;
%template(SizetVector) std::vector<size_t>;
//%template(UintVector) std::vector<unsigned int>;
%template(StringVector) std::vector<std::string>;
%include st_app/AppParGroup.h
%include st_app/StApp.h
%include astro/SkyProj.h
%include astro/SkyDir.h
%include astro/JulianDate.h
%include astro/SolarSystem.h
%template(SkyDirVector) std::vector<astro::SkyDir>;
%template(SkyDirPair) std::pair<astro::SkyDir, astro::SkyDir>;
%feature("autodoc", "1");
%include dataSubselector/CutBase.h
%include dataSubselector/BitMaskCut.h
%template(BitMaskCutVector) std::vector<dataSubselector::BitMaskCut *>;
%include dataSubselector/Cuts.h
%include healpix/CosineBinner.h
%include map_tools/Exposure.h
%include map_tools/SkyImage.h
%include optimizers/Arg.h
%include optimizers/dArg.h
%include optimizers/Parameter.h
%template(ParameterVector) std::vector<optimizers::Parameter>;
%include optimizers/Function.h
%include optimizers/Statistic.h
%include optimizers/FunctionTest.h
%include optimizers/FunctionFactory.h
%include optimizers/Optimizer.h
%include optimizers/OptimizerFactory.h
%include optimizers/Mcmc.h
%include optimizers/Minuit.h
%include optimizers/NewMinuit.h
%include st_facilities/FitsImage.h
%include st_facilities/Util.h
%include irfInterface/IEfficiencyFactor.h
%include Likelihood/EquinoxRotation.h
%template (FuncPair) std::pair<std::string, optimizers::Function *>;
%template (FuncMap) std::map<std::string, optimizers::Function *>;
%include Likelihood/Convolve.h
%include Likelihood/Exception.h
%include Likelihood/ExpCutoff.h
%include Likelihood/BrokenPowerLawExpCutoff.h
%include Likelihood/BrokenPowerLaw3.h
%include Likelihood/LogGaussian.h
%include Likelihood/ResponseFunctions.h
%include Likelihood/Event.h
%include Likelihood/Source.h
%include Likelihood/ExposureCube.h
%include Likelihood/ExposureMap.h
%include Likelihood/FileFunction.h
%include Likelihood/RoiCuts.h
%include Likelihood/ScData.h
%include Likelihood/EventContainer.h
%include Likelihood/Observation.h
%include Likelihood/Drm.h
%include Likelihood/BinnedExposure.h
%include Likelihood/AppHelpers.h
%include Likelihood/WcsMap2.h
%include Likelihood/MapBase.h
%include Likelihood/DiffuseSource.h
%include Likelihood/DiffRespIntegrand.h
%include Likelihood/DMFitFunction.h
%include Likelihood/Pixel.h
%template (PixelVector) std::vector<Likelihood::Pixel>;
%include Likelihood/CountsMap.h
%include Likelihood/SourceModel.h
%include Likelihood/LogLike.h
%template (ParamPair_t) std::pair<Likelihood::LogLike *, size_t>;
%template (ParVector_t) std::vector< std::pair<Likelihood::LogLike *, size_t> >;
%include Likelihood/CountsSpectra.h
%include Likelihood/MeanPsf.h
%include Likelihood/BinnedLikelihood.h
%include Likelihood/BinnedLikelihood2.h
%include Likelihood/ModelMap.h
%include Likelihood/Npred.h
%include Likelihood/OneSourceFunc.h
%include Likelihood/OptEM.h
%include Likelihood/PointSource.h
%include Likelihood/SourceMap.h
%include Likelihood/SpatialMap.h
%include Likelihood/SkyDirArg.h
%include Likelihood/SkyDirFunction.h
%include Likelihood/SourceFactory.h
%include Likelihood/SrcArg.h
%include Likelihood/TrapQuad.h
%include Likelihood/MapCubeFunction2.h
%include Likelihood/TiedParameter.h
%include Likelihood/Composite2.h
%include Likelihood/CompositeLikelihood.h
%include Likelihood/SummedLikelihood.h
%include pyLikelihood/Aeff.h
%include pyLikelihood/enableFPE.h
%extend Likelihood::LogLike {
   static void set_ScaleFactor_complement(optimizers::Function * func, 
                                          bool use_complement) {
      Likelihood::ScaleFactor * scaleFactor = 
         dynamic_cast<Likelihood::ScaleFactor *>(func);
      if (scaleFactor == 0) {
         throw std::runtime_error("Cannot cast to ScaleFactor object.");
      }
      scaleFactor->set_complement_flag(use_complement);
   }
}
%extend Likelihood::LogLike {
   static void enableFPE() {
      pyLikelihood::enableFPE();
   }
}
%extend st_facilities::Util {
   static std::vector<std::string> 
      resolveFitsFiles(const std::string & infile) {
      std::vector<std::string> outfiles;
      st_facilities::Util::resolve_fits_files(infile, outfiles);
      return outfiles;
   }
   static std::pair<double, double> 
      skyDir2pixel(const astro::SkyProj & proj,
                   const astro::SkyDir & dir) {
      double i, j;
      st_facilities::Util::skyDir2pixel(proj, dir, i, j);
      return std::make_pair(i, j);
   }
   static astro::SkyDir
      pixel2SkyDir(const astro::SkyProj & proj,
                   double i, double j) {
      astro::SkyDir dir;
      st_facilities::Util::pixel2SkyDir(proj, i, j, dir);
      return dir;
   }
   static void setRandomSeed(long seed) {
      CLHEP::HepRandom hepRandom(seed);
   }
   static double shoot() {
      return CLHEP::RandFlat::shoot();
   }
}
%extend Likelihood::ResponseFunctions {
   void load_with_event_types(const std::string & respFuncs, 
                              const std::string & respBase,
                              const std::string & filename,
                              const std::string & extname) {
      std::vector<unsigned int> evtTypes;
      Likelihood::AppHelpers::getSelectedEvtTypes(filename, extname, evtTypes);
      self->load(respFuncs, respBase, evtTypes);
   }
}
%extend Likelihood::EquinoxRotation {
   astro::SkyDir fromMapCoords(const astro::SkyDir & inDir) {
      astro::SkyDir outDir(0, 0);
      self->do_rotation(inDir, outDir, false);
      return outDir;
   }
   astro::SkyDir toMapCoords(const astro::SkyDir & inDir) {
      astro::SkyDir outDir(0, 0);
      self->do_rotation(inDir, outDir, true);
      return outDir;
   }
}
%extend Likelihood::SourceFactory {
   static optimizers::FunctionFactory * funcFactory() {
      optimizers::FunctionFactory * myFuncFactory 
         = new optimizers::FunctionFactory;
      Likelihood::AppHelpers::addFunctionPrototypes(myFuncFactory);
      return myFuncFactory;
   }
}
%extend Likelihood::SpatialMap {
   static Likelihood::SpatialMap * cast(optimizers::Function * func) {
      Likelihood::SpatialMap * spatial_map = 
         dynamic_cast<Likelihood::SpatialMap *>(func);
      if (spatial_map == 0) {
         throw std::runtime_error("Cannot cast to a SpatialMap.");
      }
      return spatial_map;
   }
}
%extend Likelihood::FileFunction {
   static Likelihood::FileFunction * cast(optimizers::Function * func) {
      Likelihood::FileFunction * file_func = 
         dynamic_cast<Likelihood::FileFunction *>(func);
      if (file_func == 0) {
         throw std::runtime_error("Cannot cast to a FileFunction.");
      }
      return file_func;
   }
}
%extend Likelihood::PointSource {
   static Likelihood::PointSource * cast(Likelihood::Source * src) {
      Likelihood::PointSource * ptsrc = 
         dynamic_cast<Likelihood::PointSource *>(src);
      if (ptsrc == 0) {
         throw std::runtime_error("Cannot cast to a PointSource.");
      }
      return ptsrc;
   }
}
%extend Likelihood::Source {
   double flux() {
      Likelihood::PointSource * ptsrc = 
         dynamic_cast<Likelihood::PointSource *>(self);
      if (ptsrc != 0) {
         return ptsrc->flux();
      }
      Likelihood::DiffuseSource * diffsrc = 
         dynamic_cast<Likelihood::DiffuseSource *>(self);
      return diffsrc->flux();
   }
   double flux(double emin, double emax, size_t npts=100) {
      Likelihood::PointSource * ptsrc = 
         dynamic_cast<Likelihood::PointSource *>(self);
      if (ptsrc != 0) {
         return ptsrc->flux(emin, emax, npts);
      }
      Likelihood::DiffuseSource * diffsrc = 
         dynamic_cast<Likelihood::DiffuseSource *>(self);
      return diffsrc->flux(emin, emax, npts);
   }
}
%extend Likelihood::DiffuseSource {
   static Likelihood::DiffuseSource * 
      downcastAsDiffuse(Likelihood::Source * src) {
      Likelihood::DiffuseSource * diffuse =
         dynamic_cast<Likelihood::DiffuseSource *>(src);
      if (diffuse == 0) {
         throw std::runtime_error("Cannot downcast as DiffuseSource.");
      }
      return diffuse;
   }
}
%extend Likelihood::LogLike {
   void initOutputStreams(unsigned int maxChatter=2) {
      st_stream::OStream::initStdStreams();
      st_stream::SetMaximumChatter(maxChatter);
   }
   void print_source_params() {
      std::vector<std::string> srcNames;
      self->getSrcNames(srcNames);
      std::vector<Parameter> parameters;
      for (unsigned int i = 0; i < srcNames.size(); i++) {
         Likelihood::Source *src = self->getSource(srcNames[i]);
         Likelihood::Source::FuncMap srcFuncs = src->getSrcFuncs();
         srcFuncs["Spectrum"]->getParams(parameters);
         std::cout << "\n" << srcNames[i] << ":\n";
         for (unsigned int j = 0; j < parameters.size(); j++) {
            std::cout << parameters[j].getName() << ": "
                      << parameters[j].getValue() << std::endl;
         }
         if (!dynamic_cast<Likelihood::BinnedLikelihood *>(self)) {
            std::cout << "Npred: "
                      << src->Npred() << std::endl;
         }
      }
   }
   void src_param_table() {
      std::vector<std::string> srcNames;
      self->getSrcNames(srcNames);
      std::vector<Parameter> parameters;
      for (unsigned int i = 0; i < srcNames.size(); i++) {
         Likelihood::Source *src = self->getSource(srcNames[i]);
         Likelihood::Source::FuncMap srcFuncs = src->getSrcFuncs();
         srcFuncs["Spectrum"]->getParams(parameters);
         for (unsigned int j = 0; j < parameters.size(); j++) {
            std::cout << parameters[j].getValue() << "  ";
         }
         std::cout << src->Npred() << "  ";
         std::cout << srcNames[i] << std::endl;
      }
   }
   int getNumFreeParams() {
      return self->getNumFreeParams();
   }
   void getFreeParamValues(std::vector<double> & params) {
      self->getFreeParamValues(params);
   }
   std::vector<std::string> srcNames() {
      std::vector<std::string> my_names;
      self->getSrcNames(my_names);
      return my_names;
   }
   optimizers::Mcmc * Mcmc() {
      return new optimizers::Mcmc(*self);
   }
}
%extend Likelihood::BinnedLikelihood {
   std::vector<double> modelCounts(const std::string & srcName) {
      const Likelihood::Source * src(self->getSource(srcName));
      const Likelihood::SourceMap & srcMap(self->sourceMap(srcName));
      const std::vector<float> & model(srcMap.model());
      const std::vector<float> & counts(self->countsMap().data());
      const std::vector<double> & energies(self->energies());

      size_t numpix(self->countsMap().pixels().size());
      std::vector<double> model_counts(numpix*(energies.size() - 1), 0);
      for (size_t k(0); k < energies.size() - 1; k++) {
         for (size_t j(0); j < numpix; j++) {
            size_t imin(k*numpix + j);
            if (counts.at(imin) > 0) {
               size_t imax(imin + numpix);
               model_counts.at(imin) += src->pixelCounts(energies.at(k),
                                                         energies.at(k+1),
                                                         model.at(imin),
                                                         model.at(imax));
            }
         }
      }
      return model_counts;
   }
}
%extend Likelihood::BinnedLikelihood2 {
   std::vector<double> modelCounts(const std::string & srcName) {
      const Likelihood::Source * src(self->getSource(srcName));
      const Likelihood::SourceMap & srcMap(self->sourceMap(srcName));
      const std::vector<float> & model(srcMap.model());
      const std::vector<float> & counts(self->countsMap().data());
      const std::vector<double> & energies(self->energies());

      size_t numpix(self->countsMap().pixels().size());
      std::vector<double> model_counts(numpix*(energies.size() - 1), 0);
      for (size_t k(0); k < energies.size() - 1; k++) {
         for (size_t j(0); j < numpix; j++) {
            size_t imin(k*numpix + j);
            if (counts.at(imin) > 0) {
               size_t imax(imin + numpix);
               model_counts.at(imin) += src->pixelCounts(energies.at(k),
                                                         energies.at(k+1),
                                                         model.at(imin),
                                                         model.at(imax));
            }
         }
      }
      return model_counts;
   }
 }
%extend Likelihood::Event {
   std::pair<double, double> ra_dec() const {
      return std::make_pair(self->getDir().ra(), self->getDir().dec());
   }
   std::pair<double, double> sc_dir() const {
      return std::make_pair(self->getScDir().ra(), self->getScDir().dec());
   }
}

%extend Likelihood::DiffRespIntegrand {
   static astro::SkyDir srcDir(double mu, double phi, 
                               const Likelihood::EquinoxRotation eqRot) {
      astro::SkyDir srcDir;
      Likelihood::DiffRespIntegrand::getSrcDir(mu, phi, eqRot, srcDir);
      return srcDir;
   }
}
%extend st_app::StApp {
   static st_app::AppParGroup parGroup(const std::string & appName) {
      char * argv[] = {const_cast<char *>("dummy_app")};
      int argc(1);
      st_app::StApp::processCommandLine(argc, argv);
      StAppInterface foo(appName);
      return foo.getParGroup();
   }
}
%extend st_app::AppParGroup {
   std::string __getitem__(const std::string & parname) {
      std::string my_string = self->operator[](parname);
      return my_string;
   }
   double getDouble(const std::string & parname) {
      double my_value = self->operator[](parname);
      return my_value;
   }
   int getInt(const std::string & parname) {
      int my_value = self->operator[](parname);
      return my_value;
   }
   bool getBool(const std::string & parname) {
      bool  my_value = self->operator[](parname);
      return my_value;
   }
   void Save() {
      self->Save();
   }
}
%extend map_tools::Exposure {
   healpix::CosineBinner data(const astro::SkyDir & srcDir) {
      healpix::HealpixArray<healpix::CosineBinner> skyBinner(self->data());
      return skyBinner[srcDir];
   }
}
%extend healpix::CosineBinner {
   double costheta(size_t i) {
      if (i < 0 || i >= self->size()) {
         throw std::runtime_error("IndexError");
      }
      std::vector<float>::const_iterator it(self->begin() + i);
      return self->costheta(it);
   }
   float __getitem__(size_t i) {
      if (i < 0 || i >= self->size()) {
         throw std::runtime_error("IndexError");
      }
      return *(self->begin() + i);
   }
}
%extend optimizers::Parameter {
   void setEquals(const optimizers::Parameter & rhs) {
      self->operator=(rhs);
   }
}
