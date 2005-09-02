"""
Package-dependent shared libraries and environment variables that will
be added to python_setup.([c]sh, bat) by
SwigPolicy/v*/src/startup_scripts.py.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/pyLikelihood/python/package_paths.py,v 1.1 2005/08/30 21:19:54 jchiang Exp $
#

import os

if os.name == 'posix':
    inst_dir = '${INST_DIR}'
    caldb = '${CALDB}'
else:
    inst_dir = '%INST_DIR%'
    caldb = '%CALDB%'

from swig_setup import packageroot

stlibs = ['st_graph', 'optimizers', 'xmlBase', 'Likelihood', 'evtbin',
          'dc1Response', 'g25Response', 'testResponse', 'tip']

extra_paths = [('LIKELIHOODROOT',
                os.path.join(inst_dir, '%s' % packageroot('Likelihood'))),
               ('EVTBINROOT',
                os.path.join(inst_dir, '%s' % packageroot('evtbin'))),
               ('CALDB',
                os.path.join(inst_dir, 'irfs',
                             '%s' % packageroot('caldb'), 'CALDB')), 
               ('CALDBCONFIG',
                os.path.join(caldb, 'software', 'tools', 'caldb.config')),
               ('CALDBALIAS',
                os.path.join(caldb, 'software', 'tools', 'alias_caldb.fits'))]
