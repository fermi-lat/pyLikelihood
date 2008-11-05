/**
 * @file Aeff.h
 * @brief Interface to effective area.
 * @author J. Chiang
 *
 * $Header$
 */

#ifndef pyLikelihood_Aeff_h
#define pyLikelihood_Aeff_h

#include "irfInterface/Irfs.h"
#include "irfInterface/IrfsFactory.h"

#include "irfLoader/Loader.h"

namespace pyLikelihood {

/**
 * @class Aeff
 *
 */

class Aeff {
public:
   Aeff(const std::string & irfName) : m_front(0), m_back(0) {
      irfLoader::Loader_go();
      m_front = irfInterface::IrfsFactory::instance()
         ->create(irfName+"::FRONT");
      m_back = irfInterface::IrfsFactory::instance()->create(irfName+"::BACK");
   }
   ~Aeff() throw() {
      try {
         delete m_front;
         delete m_back;
      } catch (...) {
      }
   }
   double operator()(double energy, double theta, int convtype, 
                     double phi=0) const {
      if (convtype == 0) {
         return m_front->aeff()->value(energy, theta, phi);
      } else if (convtype == 1) {
         return m_back->aeff()->value(energy, theta, phi);
      }
      throw std::runtime_error("invalid conversion type");
   }
private:
   irfInterface::Irfs * m_front;
   irfInterface::Irfs * m_back;
};

} // namespace pyLikelihood 

#endif pyLikelihood_Aeff_h
