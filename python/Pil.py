#!/usr/bin/env python
"""
Interface to .par files.

@author J. Chiang
"""
#
#$Header: /nfs/slac/g/glast/ground/cvs/pyLikelihood/python/Pil.py,v 1.1 2006/06/27 03:16:12 jchiang Exp $
#

import os, sys, re
import string

ParFileError = 'ParFileError'
def pfilesPath(parfile=None):
    try:
        if os.name == 'posix':
            pattern = re.compile(";*:*")
        else:
            pattern = re.compile("#*;*")
        paths = re.split(pattern, os.environ['PFILES'])
        paths = [path for path in paths if path != '']
    except KeyError:
        print "Your PFILES environment variable is not set."
        raise KeyError
    if parfile is None:
        return paths[0]
    for path in paths:
        try:
            if parfile in os.listdir(path):
                return path
        except OSError:
            pass
    raise ParFileError, ".par file " + parfile + " not found."

def accept(line):
    if (line.find('#') == 0 or len(line.split()) == 0):
        return 0
    return 1

def name(line):
    return line.split(',')[0].strip()

def fields(line):
    tokens = [item.strip() for item in line.split(',')[1:]]
    x = tokens[:5]
    x.append(', '.join(tokens[5:]))
    return x

def havePathToFile(file):
    basename = os.path.basename(file)
    path = file.split(basename)[0]
    return path != "" and basename in os.listdir(path)

class Pil(object):
    def __init__(self, pfile, raiseKeyErrors=True, preserveQuotes=False):
        self.raiseKeyErrors = raiseKeyErrors
        self.preserveQuotes = preserveQuotes
        self.params = {}
        self.names = []
        if not havePathToFile(pfile):
            self.parfile = os.path.join(pfilesPath(pfile), pfile)
        else:
            self.parfile = pfile
        file = open(self.parfile, 'r')
        self.lines = []
        for line in file:
            self.lines.append(line)
            if accept(line):
                self.params[name(line)] = fields(line)
                self.names.append(name(line))
        file.close()
    def keys(self):
        return self.names
    def __getitem__(self, name):
        value = (self.params[name][2]).strip('"').strip("'")
        if self.params[name][0] == 'r':
            return string.atof(value)
        elif self.params[name][0] == 'i':
            return string.atoi(value)
        else:
            if self.preserveQuotes:
                return self.params[name][2]
            else:
                return value
    def __setitem__(self, name, value):
        if name in self.names:
            self.params[name][2] = `value`
        elif self.raiseKeyErrors:
            raise KeyError, name
    def __call__(self):
        args = ''
        for name in self.keys():
            try:
                args += ' ' + ''.join(('', name, '=%s' % self[name]))
            except ValueError:
                pass
        return args
    def write(self, filename=None):
        if filename is None:
            filename = self.parfile
        file = open(filename, 'w')
        for line in self.lines:
            item = name(line)
            if item in self.names:
                params = self.params[item]
                for i in range(len(params)):
                    params[i] = params[i].strip("'")
                file.write("%s,%s\n" % (item, ",".join(params)))
            else:
                file.write(line)
        file.close()
    def prompt(self, item):
        if self.params[item][1] != 'h':
            sys.stdout.write(self.params[item][-1].strip('"')
                             + " [" + self.params[item][2].strip('"')
                             + "]: ")
            x = sys.stdin.readline().strip()
            if x is not '':
                self.__setitem__(item, x)
    def copy(self, rhs):
        for name in self.names:
            if name in rhs.names:
                self[name] = rhs[name]

if __name__ == '__main__':
    pars = Pil('likelihood.par')
    print pars['event_file']
    pars['event_file'] = "foo"
    print pars()
    pars.write()
