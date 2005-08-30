"""
Package-dependent shared libraries and environment variables that will
be added to python_setup.[c]sh by SwigPolicy/v*/src/startup_scripts.py.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header$
#

from swig_setup import packageroot

stlibs = ['st_graph', 'optimizers', 'xmlBase']

extra_paths = [('LIKELIHOODROOT', '${INST_DIR}/%s'%packageroot('Likelihood')),
               ('EVTBINROOT', '${INST_DIR}/%s' % packageroot('evtbin')),
               ('CALDB', '${INST_DIR}/irfs/%s/CALDB' % packageroot('caldb')), 
               ('CALDBCONFIG', '${CALDB}/software/tools/caldb.config'),
               ('CALDBALIAS', '${CALDB}/software/tools/alias_caldb.fits')]
