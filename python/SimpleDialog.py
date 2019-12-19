"""
@brief Class for creating simple dialog boxes that are launchable from the
       Python command line.

@author J. Chiang
"""
# @file SimpleDialog.py
# $Header: /nfs/slac/g/glast/ground/cvs/ScienceTools-scons/pyLikelihood/python/SimpleDialog.py,v 1.1.1.1 2005/08/22 16:19:27 jchiang Exp $
#

import os
import sys
import glob
import Tkinter
from FileDialog import LoadFileDialog

class ParamDoubleEntry:
    def __init__(self, parent, label, row, default=0):
        self.parent = parent
        self.variable = Tkinter.DoubleVar()
        self.variable.set(default)
        name = Tkinter.Label(parent, text=label)
        name.grid(column=0, row=row, sticky=Tkinter.E)
        entry = Tkinter.Entry(parent, textvariable=self.variable,
                              state=Tkinter.NORMAL, width=30)
        entry.grid(column=1, row=row)
    def value(self):
        return self.variable.get()

class ParamStringEntry:
    def __init__(self, parent, label, row, default=''):
        self.parent = parent
        self.variable = Tkinter.StringVar()
        self.variable.set(default)
        name = Tkinter.Label(parent, text = label)
        name.grid(column=0, row=row, sticky=Tkinter.E)
        entry = Tkinter.Entry(parent, textvariable=self.variable,
                              width=30, state=Tkinter.NORMAL)
        entry.grid(column=1, row=row)
    def value(self):
        return self.variable.get()

class ParamFileEntry:
    def __init__(self, parent, label, row, default='', expand=False,
                 pattern="*"):
        self.parent = parent
        if default.find("*") != -1:
            self.pattern = default
        else:
            self.pattern = pattern
        self.expand = expand
        self.variable = Tkinter.StringVar()
        self.variable.set(default)
        file = Tkinter.Button(parent, text=label, command=self.getFile, bd=1)
        file.grid(column=0, row=row, sticky=Tkinter.E)
        entry = Tkinter.Entry(parent, textvariable=self.variable,
                              width=30, state=Tkinter.NORMAL)
        entry.grid(column=1, row=row)
    def value(self):
        return self.variable.get()
    def getFile(self):
        pattern = self.variable.get()
        if pattern.find('*') != -1:
            self.pattern = pattern
        if self.pattern is None:
            file = LoadFileDialog(self.parent).go()
        else:
            file = LoadFileDialog(self.parent).go(pattern=self.pattern)
        if file:
            if not self.expand:
                file = os.path.basename(file)
            self.variable.set(file)

class SimpleDialog(Tkinter.Tk):
    _entryMap = {"file": ParamFileEntry,
                 "double": ParamDoubleEntry,
                 "string": ParamStringEntry}
    def __init__(self, paramDict, title="Parameter Dialog"):
        Tkinter.Tk.__init__(self)
        self.paramDict = paramDict
        self.title(title)
        row = 0
        for item in paramDict.ordered_keys:
            type = paramDict[item].type
            default = paramDict[item].value
            paramDict[item].value = self._entryMap[type](self, item, row,
                                                         default=default).value
            row += 1
        done = Tkinter.Button(self, text='ok', command=lambda: self.ok(None))
        done.grid(column=0, row=row)
        self.bind("<Return>", self.ok)
        self.bind("<Control_L>q", self.abort)
    def ok(self, event):
        self.destroy()
    def abort(self, event):
        paramDict = self.paramDict
        for item in paramDict.ordered_keys:
            type = paramDict[item].type
            paramDict[item].value = Null()
        self.destroy()

class Null(object):
    def __call__(self):
        return None

class MyOrderedDict(dict):
    def __init__(self):
        dict.__init__(self)
        self.ordered_keys = []
    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self.ordered_keys.append(key)
    
class Param(object):
    def __init__(self, type, value=None):
        self.type = type
        self.value = value
    
def answers():
    paramDict = MyOrderedDict()
    paramDict['infile'] = Param('file', '*.py')
    paramDict['outfile'] = Param('file', 'bar')
    paramDict['value'] = Param('double', 10.)
    root = SimpleDialog(paramDict)
    root.mainloop()
    return paramDict

if __name__ == '__main__':
    foo = answers() 
    print (foo["infile"].value())
    print (foo["outfile"].value())
    print (foo["value"].value())
