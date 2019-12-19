"""
@brief Test harness for derivative evaluations
@author J. Chiang <jchiang@slac.stanford.edu>
"""
# $Header$

import pyLikelihood as pyLike

_funcFactory = pyLike.SourceFactory_funcFactory()

def compare_floats(x, y, tol=1e-4):
    if x == 0:
        return abs(x - y) < tol
    else:
        return abs((x - y)/x) < tol

class DerivTester(object):
    def __init__(self, function):
        self.func = _funcFactory.create(function)
    def __call__(self, xval=100, verbose=0):
        x = pyLike.dArg(xval)
        y0 = self.func.value(x)
        params = pyLike.DoubleVector()
        self.func.getFreeParamValues(params)
        
        eps = 1e-7
        num_derivs = []
        for i in range(len(params)):
            new_params = list(params)
            delta = new_params[i]*eps
            if delta == 0:
                delta = eps
            new_params[i] += delta
            self.func.setFreeParamValues(new_params)
            y1 = self.func.value(x)
            num_derivs.append((y1 - y0)/delta)

        derivs = pyLike.DoubleVector()

        self.func.setFreeParamValues(params)
        self.func.getFreeDerivs(x, derivs)

        for i, d0, d1 in zip(range(len(derivs)), num_derivs, derivs):
            try:
                assert(compare_floats(d0, d1))
                if verbose:
                    raise AssertionError
            except AssertionError:
                parnames = pyLike.StringVector()
                self.func.getFreeParamNames(parnames)
                print ("Parameter : ", i, parnames[i])
                print ("%.3e  "*len(num_derivs) % tuple(num_derivs))
                print ("%.3e  "*len(derivs) % tuple(derivs) + "\n")
        return tuple(params)
    def __getattr__(self, attrname):
        return getattr(self.func, attrname)

if __name__ == '__main__':
    funcs = ('AbsEdge',
             'BrokenPowerLaw',
             'BrokenPowerLawExpCutoff',
             'BrokenPowerLaw2',
             'ConstantValue',
             'ExpCutoff',
             'Gaussian',
             'LogParabola',
             'PowerLaw',
             'PowerLaw2',
             'FileFunction')

    for func in funcs:
        tester = DerivTester(func)
        print ("\n" + func)
        verbose = 0
        if (func == 'PowerLaw2'):
            tester.func.parameter('Index').setValue(-1)
        if (func == 'FileFunction'):
            tester.func = pyLike.FileFunction_cast(tester.func)
            tester.func.readFunction('foo.dat')
#            verbose = 1
        tester(100, verbose)
        tester(200, verbose)
        tester(1001, verbose)
        tester(2000, verbose)
