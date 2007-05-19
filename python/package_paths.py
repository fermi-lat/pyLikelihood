"""
Package-dependent shared libraries and environment variables that will
be added to python_setup.([c]sh, bat) by
SwigPolicy/v*/src/startup_scripts.py.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/pyLikelihood/python/package_paths.py,v 1.3 2006/12/06 16:14:19 jchiang Exp $
#

import os

if os.name == 'posix':
    inst_dir = '${INST_DIR}'
    caldb = '${CALDB}'
else:
    inst_dir = '%INST_DIR%'
    caldb = '%CALDB%'

from swig_setup import packageroot

extra_paths = [('CALDB',
                os.path.join(inst_dir, 'irfs',
                             '%s' % packageroot('caldb'), 'CALDB',
                             'data', 'glast', 'lat')), 
               ('CALDBCONFIG',
                os.path.join(caldb, 'software', 'tools', 'caldb.config')),
               ('CALDBALIAS',
                os.path.join(caldb, 'software', 'tools', 'alias_caldb.fits'))]
