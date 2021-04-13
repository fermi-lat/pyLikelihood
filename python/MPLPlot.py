"""
Standard plotting interface for XY plots with matplotlib backend

@author T. Stephens <thomas.stephens@nasa.gov>
"""
#
# $Header: /glast/ScienceTools/glast/pyLikelihood/python/Attic/MPLPlot.py,v 1.1.2.3 2014/08/26 18:23:52 areustle Exp $
#
import sys
from array import array
import numpy as num
    
_symbols = {'line' : '-',
            'dashed' : '--', 
            'dotted' : ':', 
            'dash-dot' : '-.',
#             'Ldash-dot' : ('C', 0, 5 ),
#             'poly-line' : ('L',0, 1),
            'point' : '.',
            'nopoint' : ' ',  # matplot lib doesn't have a no-point option
            'plus' : '+',
            'times' : '*'}

_colors = {'white' : 'w',
           'black' : 'k',
           'red' : 'r',
           'green' : 'g',
           'blue' : 'b',
           'yellow' : 'y',
           'magenta' : 'm',
           'cyan' : 'c'}
        
class MPLPlot(object):
    def __init__(self, x, y, dx=None, dy=None, xlog=0, ylog=0,
                 xtitle="x", ytitle="y", MainTitle='', symbol='plus',
                 color='black', xrange=None, yrange=None):
        import matplotlib.pyplot as plt
        self.plt = plt
        self.plt.ion()
        
        self.fig = plt.figure()
        self.ax=self.fig.add_subplot(111)
        format = self._generateFormatString(symbol,color)
        self.ax.errorbar(x,y,xerr=dx,yerr=dy,fmt=format)
        self.ax.set_xlabel(xtitle)
        self.ax.set_ylabel(ytitle)
        if (xlog):
            self.ax.set_xscale('log')
        if (ylog):
            self.ax.set_yscale('log')
        self.ax.set_xlim(xrange)
        self.ax.set_ylim(yrange)
        self.ax.set_title(MainTitle)
        self.fig.show()
    def setTitle(self, title):
        self.ax.set_title(title)
    def getRange(self, axis):
        if ('x' == axis):
            return self.ax.get_xlim()
        else:
            return self.ax.get_ylim()
    def overlay(self, x, y, dx=None, dy=None, symbol='plus', color='black'):
        format = self._generateFormatString(symbol,color)
        self.ax.errorbar(x,y,xerr=dx,yerr=dy,fmt=format)
        self.fig.show()
    def _generateFormatString(self,symbol,color):
        format = _symbols[symbol]+_colors[color]
        return format

if __name__ == '__main__':
    x = num.arange(1, 50)
    y = x**2

    plot0 = MPLPlot(x, y, xlog=0, ylog=0, xtitle='x values',
                      ytitle='y values', MainTitle='Example')
    plot1 = MPLPlot(x, y, dy=num.sqrt(y), xlog=0, ylog=1, color='blue')
    plot2 = MPLPlot(x, y, xlog=1, ylog=1, yrange=(10, 1000), color='magenta')
 
    plot0.overlay(x, y/2., symbol='point')
    plot2.overlay(x, 2*y, symbol='line', color='red')
    import matplotlib.pyplot as plt
    plt.show(block=True)
