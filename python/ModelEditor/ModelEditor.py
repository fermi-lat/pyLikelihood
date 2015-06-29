# $Id: ModelEditor.py,v 1.4.6.4 2014/05/29 20:29:08 tstephen Exp $

# Python program to allow editing of models for the GLAST LAT
# likelihood estimator.

#******************************************************************************

# Import external modules.

# Standard modules
import os
from tkFileDialog import Open, SaveAs
from tkMessageBox import askyesno, showwarning
import Tkinter
import sys
from xml.parsers.expat import ExpatError
import thread

# Third-party modules
import Pmw

# Project modules
from HelpWindow import HelpWindow
from Source import Source
from SourceLibraryDocument import SourceLibraryDocument
from SourceLibraryDocumentEditor import SourceLibraryDocumentEditor
from Spectrum import Spectrum
from SpatialModel import SpatialModel
from AddCatalogSourcesDialog import AddCatalogSourcesDialog
from CatalogSourceExtractor import CatalogSourceExtractor
from DS9Connector import DS9Connector


#******************************************************************************

class ModelEditorApp(Tkinter.Frame):

    # Class variables.

    # Increment this counter each time a Source is created.
    _nextSourceID = 0

    # Path to the file of EGRET diffuse source data.
    _EgretDiffuseSourcePath = \
                            '$(FERMI_DIR)/refdata/fermi/EGRET_diffuse_cel.fits'

    # Path to the file of GALPROP diffuse source data.
    _GalpropDiffuseSourcePath = \
                              '$(FERMI_DIR)/refdata/fermi/GP_gamma.fits'

    #--------------------------------------------------------------------------

    def __init__(self, parent = None, path   = None, *args, **kwargs):

        # Initialize the Frame base class.
        Tkinter.Frame.__init__(self, parent, *args, **kwargs)

        # Create the main menubar.
        self._createMenubar()

        # Read the model file (if specified).
        if path:
            sourceLibraryDocument = SourceLibraryDocument(path = path)
        else:
            sourceLibraryDocument = SourceLibraryDocument()

        # Create and grid the source library document editor component.
        sourceLibraryDocumentEditor = \
            SourceLibraryDocumentEditor(self, sourceLibraryDocument,
                                        borderwidth = 2, relief = 'ridge')
        sourceLibraryDocumentEditor.grid(row = 0, column = 0)
        self._sourceLibraryDocumentEditor = sourceLibraryDocumentEditor

        # Save the path to the document.
        self._path = path
        
        # set default ROI center to 0,0
        self.ROI_ra = -1
        self.ROI_dec = 0
        self.catParams = None
        self.docLock = thread.allocate_lock()
        self.ds9 = DS9Connector(self._sourceLibraryDocumentEditor)
        self._sourceLibraryDocumentEditor.setDS9Connector(self.ds9)

    #--------------------------------------------------------------------------

    def _createMenubar(self):

        # Create and attach the menu bar for the root window.
        menuBar = Tkinter.Menu(self.master)
        self.master.config(menu = menuBar)

        # Create the individual menus and attach to the menu bar.
        self._createFileMenu(menuBar)
        self._createEditMenu(menuBar)
        self._createSourceMenu(menuBar)
        self._createSortMenu(menuBar)
        self._createDS9Menu(menuBar)
        self._createHelpMenu(menuBar)

    #--------------------------------------------------------------------------

    def _createFileMenu(self, menuBar):
        fileMenu = Tkinter.Menu(menuBar)
        fileMenu.add_command(label = 'New', command = self._onFileNew)
        fileMenu.add_command(label = 'Open...', command = self._onFileOpen)
        fileMenu.add_command(label = 'Close', command = self._onFileClose)
        fileMenu.add_command(label = 'Save', command = self._onFileSave)
        fileMenu.add_command(label = 'Save As...',
                             command = self._onFileSaveAs)
        fileMenu.add_separator()
        fileMenu.add_command(label = 'Export to ObsSim...',
                             command = self._onFileExportToObsSim)
        fileMenu.add_separator()
        fileMenu.add_command(label = 'Exit', command = self._onFileExit)
        menuBar.add_cascade(label = 'File', menu = fileMenu)

    def _onFileNew(self):
        if debug: print 'File/New'

        # If the current document has changed, prompt to save it.
        self._saveIfChanged()

        # Create a new, blank SourceLibraryDocument.
        self._new()

    def _onFileOpen(self):
        if debug: print 'File/Open...'

        # If the current document has changed, prompt to save it.
        self._saveIfChanged()

        # Fetch the path to the new file. If found, load the document and
        # save the path.
        path = Open().show()
        if path == ():
            return
        self._open(path)

    def _onFileClose(self):
        if debug: print 'File/Close'

        # If the current document has changed, prompt to save it.
        self._saveIfChanged()

        # Create a new, blank SourceLibraryDocument.
        self._new()

    def _onFileSave(self):
        if debug: print 'File/Save'

        # If no path is associated with the current document, prompt the
        # user for a path.
        if self._path is None:
            self._onFileSaveAs()
        else:
            self._save(self._path)

    def _onFileSaveAs(self):
        if debug: print 'File/Save As...'

        # Get the new path for this document. If none, return.
        path = SaveAs().show()
        if path == ():
            return

        # Save the document.
        self._save(path)

    def _onFileExportToObsSim(self):
        if debug: print 'File/Export to ObsSim...'

        # Get the new path for this document. If none, return.
        path = SaveAs().show()
        if path == ():
            return

        # Export the file.
        self._exportToObsSim(path)

    def _onFileExit(self):
        if debug: print 'File/Exit'

        # If the current document has changed, prompt to save it.
        self._saveIfChanged()

        # Exit from the application.
        self.master.destroy()

    def _new(self):
        """
        Create a new, blank document and use it to initialize the editor.
        """
        
        # Create a new, blank SourceLibraryDocument.
        sourceLibraryDocument = SourceLibraryDocument()

        # Populate the editor with the blank document.
        self._sourceLibraryDocumentEditor.set(sourceLibraryDocument)

        # Commit the new document.
        self._sourceLibraryDocumentEditor.commit()

        # Clear the document path.
        self._path = None

        # Change the window title to reflect the new path.
        self.master.title('ModelEditor (%s)' % self._path)

    def _open(self, path):
        """
        Open the specified document.
        """
        assert path is not None

        # Open the specified document.
        try:
            sourceLibraryDocument = SourceLibraryDocument(path = path)
            self._sourceLibraryDocumentEditor.set(sourceLibraryDocument)
            self._sourceLibraryDocumentEditor.commit()
            self._path = path
            self.master.title('ModelEditor (%s)' % self._path)
        except ExpatError as e:
            showwarning("XML error!", "In " + path + ": " + str(e))

    def _save(self, path):
        """
        Save the document to the specified path.
        """
        assert path is not None

        # Commit the current document.
        self._sourceLibraryDocumentEditor.commit()

        # Save the document to the current path.
        sourceLibraryDocument = self._sourceLibraryDocumentEditor.get()
        sourceLibraryDocument.toFile(path)

        # Update the current path.
        self._path = path

        # Change the window title to reflect the new path.
        self.master.title('ModelEditor (%s)' % path)

    def _saveIfChanged(self):
        """
        Check to see if the current document has changed. If so, ask the
        user if it should be saved. If so, prompt for a path and save the
        file to that path. If the user does not want to save the file, or
        the Cancel button is pressed in the Save As dialog, do nothing.
        """

        # If the current document is unchanged, return.
        changed = self._sourceLibraryDocumentEditor.getChanged()
        if not changed: return

        # The current document has changed, so ask the user if it
        # should be saved. If not, return.
        path = self._path
        if path is None:
            message = 'The document has been modified.'
        else:
            message = 'The document "%s" has been modified. ' % path
        message += ' Do you want to save your changes?'
        saveFile = askyesno(title = 'ModelEditor', message = message)
        if not saveFile:
            return

        # If the file has no associated path, get one. If the Cancel button
        # is pressed, return without saving the file.
        if path is None:
            path = SaveAs().show()
            if path == '':
                return

        # Save the document.
        self._save(path)

    def _exportToObsSim(self, path):
        """
        Export the file in ObsSim format.
        """

        # Convert the document to obssim format.
        sourceLibraryDocument = self._sourceLibraryDocumentEditor.get()
        obssimDom = sourceLibraryDocument.toObssimDom()

        # Create the output file.
        out = open(path, 'w')

        # Save the converted document.
        obssimDom.writexml(out, indent = '', addindent = '  ', newl = '\n')
        
        # Close the output file.
        out.close()

    #--------------------------------------------------------------------------

    def _createEditMenu(self, menuBar):
        editMenu = Tkinter.Menu(menuBar)
        editMenu.add_command(label = 'Cut', command = self.onEditCut)
        editMenu.add_command(label = 'Copy', command = self.onEditCopy)
        editMenu.add_command(label = 'Paste', command = self.onEditPaste)
        editMenu.add_command(label = 'Undo', command = self.onEditUndo)
        menuBar.add_cascade(label = 'Edit', menu = editMenu)

        # Disable all Edit menu commands for now.
        editMenu.entryconfigure(1, state = 'disabled')
        editMenu.entryconfigure(2, state = 'disabled')
        editMenu.entryconfigure(3, state = 'disabled')
        editMenu.entryconfigure(4, state = 'disabled')

    def onEditCut(self):
        if debug: print 'Edit/Cut'

    def onEditCopy(self):
        if debug: print 'Edit/Copy'

    def onEditPaste(self):
        if debug: print 'Edit/Paste'

    def onEditUndo(self):
        if debug: print 'Edit/Undo'

    #--------------------------------------------------------------------------

    def _createSourceMenu(self, menuBar):
        sourceMenu = Tkinter.Menu(menuBar)
        sourceMenu.add_command(label = 'Add Source',
                               command = self._onSourceAddSource)
        sourceMenu.add_command(label = 'Remove Source',
                               command = self._onSourceRemoveSource)
        sourceMenu.add_separator()
        sourceMenu.add_command(label = 'Add Point Source',
                               command = self._onSourceAddPointSource)
        sourceMenu.add_command(label = 'Add Diffuse Source',
                               command = self._onSourceAddDiffuseSource)
        sourceMenu.add_separator()
        sourceMenu.add_command(label = 'Add Fermi Catalog Sources',
                               command = self._onSourceAddCatalogSources)
        sourceMenu.add_separator()
        sourceMenu.add_command(label = 'Add EGRET Diffuse Source',
                               command = self._onSourceAddEGRETDiffuseSource)
        sourceMenu.add_command(label = 'Add GALPROP Diffuse Source',
                               command = \
                               self._onSourceAddGALPROPDiffuseSource)
        sourceMenu.add_command(label = 'Add Extragalactic Diffuse Source',
                               command = \
                               self._onSourceAddExtragalacticDiffuseSource)
        menuBar.add_cascade(label = 'Source', menu = sourceMenu)

    def _onSourceAddSource(self):
        if debug: print 'Source/Add Source'

        # Create a new Source.
        name = 'Source %d' % self._getSourceID()
        source = Source(name = name)

        # Fetch the current SourceLibraryDocument.
        sourceLibraryDocument = self._sourceLibraryDocumentEditor.get()

        # Append the new Source to the list of Sources.
        sourceLibraryDocument.addSource(source)

        # Populate the editor with the changes.
        self._sourceLibraryDocumentEditor.set(sourceLibraryDocument)

    def _onSourceRemoveSource(self):
        if debug: print 'Source/Remove Source'

        # Fetch the current SourceLibraryDocument.
        sourceLibraryDocument = self._sourceLibraryDocumentEditor.get()

        # Display a warning and abort if the user tries to delete the
        # last Source.
        nSources = sourceLibraryDocument.getNumSources()
        if nSources == 1:
            showwarning('Warning!', 'Cannot delete only source!')
            return

        # Get the index of the currently selected Source.
        currentSourceIndex = \
            self._sourceLibraryDocumentEditor.getCurrentSourceIndex()

        # Confirm the source deletion.
        deleteSource = askyesno('Are you sure?',
                                'Are you sure you want to delete the source?')
        if not deleteSource:
            return

        # Remove the current Source.
        sourceLibraryDocument.removeSource(currentSourceIndex)

        # Populate the editor with the changes.
#         lock = thread.allocate_lock()
#         with lock:
        self._sourceLibraryDocumentEditor.set(sourceLibraryDocument)
        self.ds9.plotSources()

    def _onSourceAddPointSource(self):
        if debug: print 'Source/Add Point Source'

        # Create a new point Source.
        name = 'Point Source %d' % self._getSourceID()
        source = Source(name = name, type = 'PointSource')

        # Fetch the current SourceLibraryDocument.
        sourceLibraryDocument = self._sourceLibraryDocumentEditor.get()

        # Append the new Source to the list of Sources.
        sourceLibraryDocument.addSource(source)

        # Populate the editor with the changes.
        self._sourceLibraryDocumentEditor.set(sourceLibraryDocument)

    def _onSourceAddDiffuseSource(self):
        if debug: print 'Source/Add Diffuse Source'

        # Create a new diffuse Source.
        name = 'Diffuse Source %d' % self._getSourceID()
        source = Source(name = name, type = 'DiffuseSource')

        # Fetch the current SourceLibraryDocument.
        sourceLibraryDocument = self._sourceLibraryDocumentEditor.get()

        # Append the new Source to the list of Sources.
        sourceLibraryDocument.addSource(source)

        # Populate the editor with the changes.
        self._sourceLibraryDocumentEditor.set(sourceLibraryDocument)

    def _onSourceAddCatalogSources(self):
        if debug: print 'Source/Add Catalog Sources'
        # Open the dialog to prompt for the necessary input
        win = AddCatalogSourcesDialog()
        self.catParams = win.getData()
        
        # make sure something was returned.  If not we're done.
        if (None == self.catParams):
            return

        # Extract the sources from the catalog file
        # Create SourceCatalogExtractor class, passing in catalog parameters
        extractor = CatalogSourceExtractor(self.catParams)
        # Get a list of sources from the SourceCatalogExtractor
        (sources,self.ROI_ra,self.ROI_dec) = extractor.getSources()
        
        #make sure there is something to add
        if (None == sources):
            return
        # Fetch the current SourceLibraryDocument.
        with self.docLock:
            sourceLibraryDocument = self._sourceLibraryDocumentEditor.get()
            # Loop over list of sources, adding them to the existing list of sources
            for src in sources:
                sourceLibraryDocument.addSource(src)
            # Populate the editor with the changes.
            self._sourceLibraryDocumentEditor.set(sourceLibraryDocument)
            self._sourceLibraryDocumentEditor.commit()

        if (None != self.ds9):
            self.ds9.plotSources()

    def _onSourceAddEGRETDiffuseSource(self):
        if debug: print 'Source/Add EGRET Diffuse Source'

        # Create a new EGRET diffuse Source.
        name = 'EGRET Diffuse Source %d' % self._getSourceID()

        # Create a power law spectrum for the EGRET diffuse source.
        spectrum = Spectrum(type = 'PowerLaw')

        # Adjust the Prefactor parameter.
        parameter = spectrum.getParameterByName('Prefactor')
        parameter.setValue(11.0)
        parameter.setScale(0.001)
        parameter.setMin(0.001)
        parameter.setMax(1000.0)
        parameter.setFree(True)
        spectrum.setParameterByName('Prefactor', parameter)

        # Adjust the Index parameter.
        parameter = spectrum.getParameterByName('Index')
        parameter.setValue(-2.1)
        parameter.setScale(1.0)
        parameter.setMin(-3.5)
        parameter.setMax(-1.0)
        parameter.setFree(False)
        spectrum.setParameterByName('Index', parameter)

        # Adjust the Scale parameter.
        parameter = spectrum.getParameterByName('Scale')
        parameter.setValue(100.0)
        parameter.setScale(1.0)
        parameter.setMin(50.0)
        parameter.setMax(200.0)
        parameter.setFree(False)
        spectrum.setParameterByName('Scale', parameter)

        # Create a spatial map spatial model.
        spatialModel = SpatialModel(type = 'SpatialMap',
                                    file = ModelEditorApp._EgretDiffuseSourcePath)
        source = Source(name = name, type = 'DiffuseSource',
                        spectrum = spectrum, spatialModel = spatialModel)

        # Assemble the source.
        source = Source(name = name, type = 'DiffuseSource',
                        spectrum = spectrum, spatialModel = spatialModel)

        # Fetch the current SourceLibraryDocument.
        sourceLibraryDocument = self._sourceLibraryDocumentEditor.get()

        # Append the new Source to the list of Sources.
        sourceLibraryDocument.addSource(source)

        # Populate the editor with the changes.
        self._sourceLibraryDocumentEditor.set(sourceLibraryDocument)

        # Select the new source.
        self._sourceLibraryDocumentEditor.selectSource(name)

    def _onSourceAddGALPROPDiffuseSource(self):
        if debug: print 'Source/Add GALPROP Diffuse Source'

        # Create a new GALPROP diffuse Source.
        name = 'GALPROP Diffuse Source %d' % self._getSourceID()

        # Create a constant value spectrum for the GALPROP source.
        spectrum = Spectrum(type = 'ConstantValue')

        # Adjust the Value parameter.
        parameter = spectrum.getParameterByName('Value')
        parameter.setValue(1.0)
        parameter.setScale(1.0)
        parameter.setMin(0.0)
        parameter.setMax(10.0)
        parameter.setFree(True)
        spectrum.setParameterByName('Value', parameter)

        # Create a map cube spatial model.
        spatialModel = SpatialModel(type = 'MapCubeFunction',
                                    file = ModelEditorApp._GalpropDiffuseSourcePath)

        # Adjust the Normalization parameter.
        parameter = spatialModel.getParameterByName('Normalization')
        parameter.setValue(1.0)
        parameter.setScale(1.0)
        parameter.setMin(0.001)
        parameter.setMax(1000.0)
        parameter.setFree(False)
        spatialModel.setParameterByName('Normalization', parameter)

        # Assemble the source.
        source = Source(name = name, type = 'DiffuseSource',
                        spectrum = spectrum, spatialModel = spatialModel)

        # Fetch the current SourceLibraryDocument.
        sourceLibraryDocument = self._sourceLibraryDocumentEditor.get()

        # Append the new Source to the list of Sources.
        sourceLibraryDocument.addSource(source)

        # Populate the editor with the changes.
        self._sourceLibraryDocumentEditor.set(sourceLibraryDocument)

        # Select the new source.
        self._sourceLibraryDocumentEditor.selectSource(name)

    def _onSourceAddExtragalacticDiffuseSource(self):
        if debug: print 'Source/Add Extragalactic Source'

        # Create a new extragalactic diffuse Source.
        name = 'Extragalactic Diffuse Source %d' % self._getSourceID()

        # Create a power law spectrum for the extragalactic
        # background.
        spectrum = Spectrum(type = 'PowerLaw')

        # Adjust the Prefactor parameter.
        parameter = spectrum.getParameterByName('Prefactor')
        parameter.setValue(1.6)
        parameter.setScale(1.0e-7)
        parameter.setMin(1.0e-5)
        parameter.setMax(100.0)
        parameter.setFree(True)
        spectrum.setParameterByName('Prefactor', parameter)

        # Adjust the Index parameter.
        parameter = spectrum.getParameterByName('Index')
        parameter.setValue(-2.1)
        parameter.setScale(1.0)
        parameter.setMin(-3.5)
        parameter.setMax(-1.0)
        parameter.setFree(False)
        spectrum.setParameterByName('Index', parameter)

        # Adjust the Scale parameter.
        parameter = spectrum.getParameterByName('Scale')
        parameter.setValue(100.0)
        parameter.setScale(1.0)
        parameter.setMin(50.0)
        parameter.setMax(200.0)
        parameter.setFree(False)
        spectrum.setParameterByName('Scale', parameter)

        # Create a constant value (all-sky) location model.
        spatialModel = SpatialModel(type = 'ConstantValue')

        # Assemble the source.
        source = Source(name = name, type = 'DiffuseSource',
                        spectrum = spectrum, spatialModel = spatialModel)

        # Fetch the current SourceLibraryDocument.
        sourceLibraryDocument = self._sourceLibraryDocumentEditor.get()

        # Append the new Source to the list of Sources.
        sourceLibraryDocument.addSource(source)

        # Populate the editor with the changes.
        self._sourceLibraryDocumentEditor.set(sourceLibraryDocument)

        # Select the new source.
        self._sourceLibraryDocumentEditor.selectSource(name)

    #--------------------------------------------------------------------------

    def _createSortMenu(self,menuBar):
        sortMenu = Tkinter.Menu(menuBar)
        self.sortAscending = True
        self.sortMethod = None
        sortMenu.add_command(label = "Sort Ascending", foreground="red", activeforeground="red", command = (lambda: self._toggleSorting(True,sortMenu)))
        sortMenu.add_command(label = "Sort Descending", command = (lambda: self._toggleSorting(False,sortMenu)))
        sortMenu.add_command(label = "Clear Sorting", command = self._clearSorting)
        sortMenu.add_separator()
        sortMenu.add_command(label = "Sort by Name", command = (lambda: self._sortSources("Name")))
        sortMenu.add_command(label = "Sort by RA/Dec", command = (lambda: self._sortSources("Position")))
        sortMenu.add_command(label = "Sort by Distance from ROI center", command = (lambda: self._sortSources("Center")))
        sortMenu.add_command(label = "Sort by Source Type", command = (lambda: self._sortSources("SourceType")))
        sortMenu.add_command(label = "Sort by Spectral Type", command = (lambda: self._sortSources("SpectralType")))
        sortMenu.add_separator()
        sortMenu.add_command(label = "Sort by Primary Index", command = (lambda: self._sortSources("Index")))
        sortMenu.add_command(label = "Sort by Integral Flux", command = (lambda: self._sortSources("Flux")))
        menuBar.add_cascade(label = 'Sort', menu=sortMenu)

    def _toggleSorting(self,ascend,menu):
        resort = False
        if (self.sortAscending != ascend):  # we only have to do anything if we're changing the sorting direction
            resort = True
            self.sortAscending = ascend
            if (ascend):
                menu.entryconfig(1,foreground="red", activeforeground="red")
                menu.entryconfig(2,foreground="black", activeforeground="black")
            else:
                menu.entryconfig(1,foreground="black", activeforeground="black")
                menu.entryconfig(2,foreground="red", activeforeground="red")
        if (None != self.sortMethod and resort):
            self._sortSources()

    def _clearSorting(self):
        self.sortMethod = None

    def _sortSources(self, type = None):
        if (None != type):  self.sortMethod = type
        # set up the sorting
        params = {'sortType':self.sortMethod,'ascending':self.sortAscending}
        if ("Center" == self.sortMethod):
            if (-1 == self.ROI_ra):
                showwarning("Insufficent Data","There is currently no ROI defined.  Unable to sort.")
                return
            params['ra'] = self.ROI_ra
            params['dec'] = self.ROI_dec
        # Fetch the current SourceLibraryDocument.
        sourceLibraryDocument = self._sourceLibraryDocumentEditor.get()
        # do the sorting
        sourceLibraryDocument.sortSources(params)
        # Populate the editor with the changes.
        self._sourceLibraryDocumentEditor.set(sourceLibraryDocument)
        self._sourceLibraryDocumentEditor.commit()
        
    #--------------------------------------------------------------------------

    def _createDS9Menu(self,menuBar):
        ds9Menu = Tkinter.Menu(menuBar)
        self.showDS9Sources = False
        self.showDS9TextLabels = False
        self.ds9 = None
        ds9Menu.add_command(label = "Connect", command = (lambda: self.ds9.connect()))
        ds9Menu.add_command(label = "Load Image", command = (lambda: self._loadDS9Image()))
        ds9Menu.add_command(label = "Plot Sources", command = (lambda: self.ds9.togglePlotSources(ds9Menu)))
        ds9Menu.add_command(label = "Text Labels", command = (lambda: self.ds9.toggleTextLabels(ds9Menu)))
        menuBar.add_cascade(label = 'DS9', menu=ds9Menu)
        
    def _loadDS9Image(self):
        (self.ROI_ra,self.ROI_dec,rad) = self.ds9.loadImage();
    #--------------------------------------------------------------------------

    def _createHelpMenu(self, menuBar):
        helpMenu = Tkinter.Menu(menuBar)
        helpMenu.add_command(label = 'Help', command = self._onHelpHelp)
        helpMenu.add_command(label = 'About...', command = self._onHelpAbout)
        menuBar.add_cascade(label = 'Help', menu = helpMenu)

    def _onHelpHelp(self):
        if debug: print 'Help/Help'
        path = os.environ['FERMI_INST_DIR'] + '/help/help.txt'
        helpWindow = HelpWindow(path = path)

    def _onHelpAbout(self):
        if debug: print 'Help/About...'

        # Create the 'about the program' dialog.
        Pmw.aboutversion('1.2')
        Pmw.aboutcopyright('Copyright NASA/GSFC 2008-2014')
        Pmw.aboutcontact('For more information, contact the ' + \
                         'FSSC Helpdesk\n(fermihelp@milkyway.gsfc.nasa.gov).')
        aboutDialog = Pmw.AboutDialog(self, applicationname = 'ModelEditor')

    #--------------------------------------------------------------------------

    def _getSourceID(self):
        """
        Return the next available Source ID.
        """
        newSourceID = ModelEditorApp._nextSourceID
        ModelEditorApp._nextSourceID += 1
        return newSourceID

#******************************************************************************

# Global execution flags.
debug = False
verbose = False

# If run as a script, build and run the application.
if __name__ == '__main__':

    # Check for global execution flags.
    if '--debug' in sys.argv:
        debug = True
        sys.argv.remove('--debug')
    if '--verbose' in sys.argv:
        verbose = True
        sys.argv.remove('--verbose')

    # Save any command-line options.
    path = None
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if debug:
            print 'path = ' + path

    # Create the root window.
    root = Tkinter.Tk()
    Pmw.initialise(root)
    root.title('ModelEditor (%s)' % path)

    # Create and grid the application object, passing it the path to
    # the model file (if any).
    modelEditor = ModelEditorApp(root, path)
    modelEditor.grid(sticky = 'nsew')

    # Enter the main program loop.
    root.mainloop()
