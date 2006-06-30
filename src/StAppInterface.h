#ifndef pyLikelihood_StAppInterface_h
#define pyLikelihood_StAppInterface_h

#include "st_app/AppParGroup.h"
#include "st_app/StApp.h"

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

#endif // pyLikelihood_StAppInterface_h
