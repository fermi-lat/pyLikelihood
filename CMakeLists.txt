####################################
# Create target and set properties #
####################################

include(UseSWIG)

set(UseSWIG_TARGET_NAME_PREFERENCE STANDARD)

### SWIG generates the python wrapper library
set_property(SOURCE src/pyLikelihood.i PROPERTY CPLUSPLUS ON)

swig_add_library(
  pyLikelihood
  TYPE SHARED
  LANGUAGE python
  SOURCES src/pyLikelihood.i
)

set_property(TARGET pyLikelihood PROPERTY SWIG_USE_TARGET_INCLUDE_DIRECTORIES TRUE)

target_include_directories(
  pyLikelihood PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
  $<INSTALL_INTERFACE:>
)

target_link_libraries(pyLikelihood PRIVATE Likelihood Python3::Python)


###############################################################
# Installation
###############################################################
install(DIRECTORY pyLikelihood DESTINATION ${FERMI_INSTALL_INCLUDEDIR})
install(DIRECTORY python/ DESTINATION ${PYTHON_SITE_PKGDIR})

install(
  TARGETS pyLikelihood
  EXPORT fermiTargets
  RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
  LIBRARY DESTINATION lib
  ARCHIVE DESTINATION lib
  INCLUDES DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)
install(
  FILES ${CMAKE_CURRENT_BINARY_DIR}/pyLikelihood.py
  DESTINATION ${PYTHON_SITE_PKGDIR}
)
