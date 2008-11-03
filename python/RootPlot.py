"""
Standard plotting interface for XY plots with pyROOT backend

@author J. Chiang <jchiang@slac.stanford.edu>
"""
#
# $Header$
#
import sys
from array import array
import numpy as num
    
from ROOT import TCanvas, TGraphErrors, TH2F, gStyle

_ncanvas = -1

_symbols = {'line' : ('C', 0, 1),
            'dashed' : ('C', 0, 2), 
            'dotted' : ('C', 0, 3), 
            'dash-dot' : ('C', 0, 4),
            'poly-line' : ('L',0,1),
            'point' : ('P', 0, 1),
            'nopoint' : ('P',1,1),
            'plus' : ('P', 2, 1),
            'times' : ('P', 3, 1)}

_colors = {'white' : 0,
           'black' : 1,
           'red' : 2,
           'green' : 3,
           'blue' : 4,
           'yellow' : 5,
           'magenta' : 6,
           'cyan' : 7}

gStyle.SetPadLeftMargin(.20)
        
class RootPlot(object):
    def __init__(self, x, y, dx=None, dy=None, xlog=0, ylog=0,
                 xtitle="x", ytitle="y", MainTitle='', symbol='plus',
                 color='black', xrange=None, yrange=None):
        self._createCanvas(xlog, ylog)
        self._createBaseGraph(x, y, dx, dy)
        self._drawAxes(xrange, yrange)
        self._setTitles(xtitle, ytitle, MainTitle)
        self._drawData(self.graphs[0], symbol, color)

    def _createCanvas(self, xlog, ylog):
        global _ncanvas
        _ncanvas += 1
        self.canvas = TCanvas("c%i" % _ncanvas,
                              "plot %i" % _ncanvas, 400, 400)
        if xlog:
            self.canvas.SetLogx()
        if ylog:
            self.canvas.SetLogy()
    def _createBaseGraph(self, x, y, dx, dy):
        npts, xx, yy, dxx, dyy = self._fillArrays(x, y, dx, dy)
        self.graphs = [TGraphErrors(npts, xx, yy, dxx, dyy)]
    def _drawAxes(self, xrange, yrange):
        if xrange is None:
            xrange = self._getRange(self.graphs[0], 'x')
        if yrange is None:
            yrange = self._getRange(self.graphs[0], 'y')
        self.hist = TH2F("hist%i" % _ncanvas, "",
                         10, xrange[0], xrange[1],
                         10, yrange[0], yrange[1])
        self.hist.SetStats(0)
        self.hist.Draw()
    def _setTitles(self, xtitle, ytitle, MainTitle):
        self.hist.GetXaxis().SetTitle(xtitle)
        self.hist.GetXaxis().CenterTitle()
        self.hist.GetYaxis().SetTitle(ytitle)
        self.hist.GetYaxis().CenterTitle()
        self.hist.GetYaxis().SetTitleOffset(2.)
        self.hist.SetTitle(MainTitle)
    def _drawData(self, graph, key, color):
        symbol, marker, lineStyle = _symbols[key]
        if symbol in ['C','L']:
            graph.SetLineStyle(lineStyle)
        else:
            graph.SetMarkerStyle(marker)
        graph.SetLineColor(_colors[color])
        graph.SetMarkerColor(_colors[color])
        graph.Draw('%s' % symbol)
    def _getRange(self, graph, axis):
        if axis == 'x':
            my_axis = graph.GetXaxis()
        elif axis == 'y':
            my_axis = graph.GetYaxis()
        return my_axis.GetXmin(), my_axis.GetXmax()
    def _fillArrays(self, xp, yp, dxp, dyp):
        my_x = array('d')
        my_y = array('d')
        my_dx = array('d')
        my_dy = array('d')
        if dxp is None:
            dx = num.zeros(len(xp))
        else:
            dx = dxp
        if dyp is None:
            dy = num.zeros(len(yp))
        else:
            dy = dyp
        for xx, yy, dxx, dyy in zip(xp, yp, dx, dy):
            my_x.append(xx)
            my_y.append(yy)
            my_dx.append(dxx)
            my_dy.append(dyy)
        my_npts = len(my_x)
        return my_npts, my_x, my_y, my_dx, my_dy
    def overlay(self, x, y, dx=None, dy=None, symbol='plus', color='black'):
        npts, xx, yy, dxx, dyy = self._fillArrays(x, y, dx, dy)
        self.graphs.append(TGraphErrors(npts, xx, yy, dxx, dyy))
        self.canvas.cd()
        self._drawData(self.graphs[-1], symbol, color)

if __name__ == '__main__':
    x = num.arange(1, 50)
    y = x**2

    plot0 = RootPlot(x, y, xlog=0, ylog=0, xtitle='x values',
                      ytitle='y values')
    plot1 = RootPlot(x, y, dy=num.sqrt(y), xlog=0, ylog=1, color='blue')
    plot2 = RootPlot(x, y, xlog=1, ylog=1, yrange=(10, 1000), color='magenta')

    plot0.overlay(x, y/2., symbol='point')
    plot2.overlay(x, 2*y, symbol='line', color='red')
