"""
Standard plotting interface for XY plots with hippoplotter backend.

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header: /nfs/slac/g/glast/ground/cvs/pyLikelihood/python/HippoPlot.py,v 1.2 2007/07/13 15:37:17 jchiang Exp $
#

import numpy as num

_symbols = {'line' : ('Line', 'Solid', 'filled_square', 1),
            'dashed' : ('Line', 'Dash', 'filled_square', 1),
            'dash-dot' : ('Line', 'DashDot', 'filled_square', 1),
            'dotted' : ('Line', 'Dot', 'filled_square', 1),
            'point' : ('Symbol', 'Solid', 'filled_square', 1),
            'plus' : ('Symbol', 'Solid', 'plus', 4),
            'times' : ('Symbol', 'Solid', 'times', 4)}

class HippoPlot(object):
    def __init__(self, x, y, dx=None, dy=None, xlog=0, ylog=0,
                 xtitle='x', ytitle='y', symbol='plus', color='black',
                 xrange=(), yrange=()):
        import hippoplotter as plot
        self.plot = plot
        self.nts = [self._fillArrays(x, y, dx, dy, xtitle, ytitle)]
        xerr, yerr = self._parseErrors(dx, dy)
        self.graphs = [plot.XYPlot(self.nts[0], xtitle, ytitle,
                                   xerr, yerr, xlog=xlog, ylog=ylog,
                                   xrange=xrange, yrange=yrange)]
        self._setPointRep(self.graphs[0].getDataRep(), symbol, color)
    def _setPointRep(self, rep, symbol, color):
        pointRep, lineStyle, sym, symsize = _symbols[symbol]
        rep.setPointRep(self.plot.prf.create(pointRep))
        if pointRep == 'Symbol':
            rep.setSymbol(sym, symsize)
        elif pointRep == 'Line':
            rep.setLineStyle(lineStyle)
        rep.setColor(color)
    def _parseErrors(self, dx, dy):
        if dx is not None:
            xerr = 'xerr'
        else:
            xerr = None
        if dy is not None:
            yerr = 'yerr'
        else:
            yerr = None
        return xerr, yerr
    def _fillArrays(self, xp, yp, dxp, dyp, xtitle, ytitle):
        xs, ys, dxs, dys = [], [], [], []
        if dxp is None:
            dx = num.zeros(len(xp))
        else:
            dx = dxp
        if dyp is None:
            dy = num.zeros(len(yp))
        else:
            dy = dyp
        for xx, yy, dxx, dyy in zip(xp, yp, dx, dy):
            xs.append(xx)
            ys.append(yy)
            dxs.append(dxx)
            dys.append(dyy)
        return self.plot.newNTuple((xs, ys, dxs, dys),
                                   (xtitle, ytitle, 'xerr', 'yerr'))
    def overlay(self, x, y, dx=None, dy=None, symbol='Line', color='black'):
        self.plot.canvas.selectDisplay(self.graphs[0])
        self.nts.append(self._fillArrays(x, y, dx, dy, 'x', 'y'))
        xerr, yerr = self._parseErrors(dx, dy)
        self.graphs.append(self.plot.XYPlot(self.nts[-1], 'x', 'y', 
                                            xerr, yerr, oplot=1))
        self._setPointRep(self.graphs[-1], symbol, color)

if __name__ == '__main__':
    x = num.arange(1, 50)
    y = x**2

    plot0 = HippoPlot(x, y, xlog=0, ylog=0, xtitle='x values',
                      ytitle='y values')
    plot1 = HippoPlot(x, y, dy=num.sqrt(y), xlog=0, ylog=1, color='blue')
    plot2 = HippoPlot(x, y, xlog=1, ylog=1, yrange=(10, 1000), color='magenta')

    plot0.overlay(x, y/2., symbol='point')
    plot2.overlay(x, 2*y, symbol='line', color='red')
