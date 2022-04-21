####################################
# Create target and set properties #
####################################

include(UseSWIG)

set(UseSWIG_TARGET_NAME_PREFERENCE STANDARD)
set(CMAKE_SWIG_FLAGS -w362 -w389 -w401 -w402 -w503 -w509)

### SWIG generates the python wrapper library
set_property(SOURCE src/pyLikelihood.i PROPERTY CPLUSPLUS ON)
swig_add_library(pyLikelihood LANGUAGE python SOURCES src/pyLikelihood.i)
set_property(TARGET pyLikelihood PROPERTY SWIG_USE_TARGET_INCLUDE_DIRECTORIES TRUE)

target_include_directories(
  pyLikelihood PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
  $<INSTALL_INTERFACE:>
)

target_link_libraries(pyLikelihood PRIVATE Likelihood Python3::Python PkgConfig::f2c)

if(APPLE)
  target_link_options(pyLikelihood PRIVATE -bundle -flat_namespace)
endif()

###############################################################
# Installation
###############################################################
install(DIRECTORY pyLikelihood DESTINATION ${FERMI_INSTALL_INCLUDEDIR})
install(DIRECTORY python/ DESTINATION ${FERMI_INSTALL_PYTHON})

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
  DESTINATION ${FERMI_INSTALL_PYTHON}
)
