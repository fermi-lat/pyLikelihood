# $Id: $

#******************************************************************************

# Import external modules.

# Standard modules
from Tkinter import Toplevel,Label,Button,Frame,LEFT,TOP,YES,RIGHT,X,E,ACTIVE,DISABLED,NORMAL
from tkFileDialog import askopenfilename,askdirectory
from os.path import isfile,dirname,isdir
from os import getenv

# Third-party modules
import Pmw

#******************************************************************************
FERMI_DIR = getenv("FERMI_DIR")

class AddCatalogSourcesDialog():
    """Class to gather input values for loading catalog sources

    This class presents a dialog box to the user allowing them to input values
    for the various filenames, model names, and other values needed to extract
    the Fermi Source Catalog sources from the relevant files and add them to
    their model.

    Usage:
         dialog = AddCatalogSourceDialog()
         data = dialog.getData()

    The getData() method returns a dictionary of the data values entered by the
    user.  The dictionary keys are listed below in the description of the values
    the user is prompted for.  If the dialog is canceled, it returns a None
    object.

    The user is prompted to input the following values
        - Source Catalog file (key => 'catalogFile') - This is the FITS file
          of the Fermi Source catalog.  This can be the 1FGL, 2FGL, or 3FGL (once
          published) catalog file.  This contains the sources to be added to the
          model.
        - LAT Event File (key => 'eventFile') - This is a valid FT1 LAT event
          FITS file.  This file is used to extract the region of interest (ROI)
          information to determine which sources should be selected from the
          catalog.
        - Source Significance Limit (key => 'sigLimit') - This is the significance
          limit threshold for selecting sources from the catalog.  Sources with
          significance values less than this limit will not be added to the model.
        - Galactic Diffuse Model file (key => 'galDiffFile') - This is the file
          containing the galactic diffuse model to use.  By default it points to
          the standard file provided with the Science Tools.
        - Galactic Diffuse Model Name (key => 'gdModelName') - This is the name
          of the model to use from the galactic diffuse model file.  By default
          it is set to ????????????.
        - Isotropic Template file (key => 'iosTempFile') - The name of the
          file containing the isotropic diffuse templates.  By default this is
          set to the standard file provided with the Science Tools.
        - Isotropic Template Name (key => 'isoTempName') - The name of the
          isotropic template to use.  By default this is set to ????????????.
        - Variable Source Radius - radius within which all sources should be set
          to allow their parameters to vary.  Outside of this radius parameters
          will be fixed to catalog values.  Values less than 0 are treated as
          meaning that the radius is the same as the extraction radius in the FT1
          event file.  Default is -1
        - Force Point Source flag - If set all extended sources in the catalog
          will be treated as point sources.  Default is false.
        - Extended Source Template Directory - Directory containing the extended
          source model files.  This is only needed if the Force Point Source flag
          is no.
    """

    def __init__(self):
        """Initialize the class

        Parameters:
        - self - This AddCatalogSourcesDialog object

        Return value:
        - none

        Description:
        This method simply creates the top level Tk window for holding the dialog box and
        initializes an empty dictionary to hold the return values.
        """
        self.win = Toplevel();
        self.win.title("Add Catalog Sources")
#        self.win.minsize(500, 100)
        self.values = {}
        # need access to these outside their creation function
        self.l9 = Label()
        self.b7 = Button()


    def _draw(self):
        """Create the dialog box

        Parameters:
        - self - This AddCatalogSourcesDialog object

        Return value:
        - none

        Description:
        This method creates the dialog box to be presented to the user.  It also creates
        the internal EntryField variables to hold the data values entered by the user.
        """
        labelWidth=32

        msg = Label(self.win,width=60,pady=5,text="To load catalog sources please provide the following information:")
        msg.pack(side=TOP)

        scFrame = Frame(self.win)
        l1 = Label(scFrame,text="Source Catalog File:",width=labelWidth,anchor=E)
        l1.pack(side=LEFT)
        self._catalogFileField = Pmw.EntryField(scFrame,value="")
        self._catalogFileField.pack(side=LEFT,expand=YES,fill=X)
        b1 = Button(scFrame,text="Browse...",command=(lambda: self._getFile(self._catalogFileField)))
        b1.pack(side=LEFT)
        scFrame.pack(side=TOP,expand=YES,fill=X)

        ft1Frame = Frame(self.win)
        l2 = Label(ft1Frame,text="Event File (for ROI):",width=labelWidth,anchor=E)
        l2.pack(side=LEFT)
        self._eventFileField = Pmw.EntryField(ft1Frame,value="")
        self._eventFileField.pack(side=LEFT,expand=YES,fill=X)
        b2 = Button(ft1Frame,text="Browse...",command=(lambda: self._getFile(self._eventFileField)))
        b2.pack(side=LEFT)
        ft1Frame.pack(side=TOP,expand=YES,fill=X)

        sigFrame = Frame(self.win)
        l3=Label(sigFrame,text="Source Significance Limit:",width=labelWidth,anchor=E)
        l3.pack(side=LEFT)
        self._sigLimitField = Pmw.EntryField(sigFrame,value=4)
        self._sigLimitField.pack(side=LEFT)
        sigFrame.pack(side=TOP,expand=YES,fill=X)

        galDiffFrame = Frame(self.win)
        l4=Label(galDiffFrame,text="Galactic Diffuse Model File:",width=labelWidth,anchor=E)
        l4.pack(side=LEFT)
        self._galDiffFileField = Pmw.EntryField(galDiffFrame,value=FERMI_DIR+"/refdata/fermi/galdiffuse/gll_iem_v06.fits")
        self._galDiffFileField.pack(side=LEFT,expand=YES,fill=X)
        b4 = Button(galDiffFrame,text="Browse...",command=(lambda: self._getFile(self._galDiffFileField)))
        b4.pack(side=LEFT)
        galDiffFrame.pack(side=TOP,expand=YES,fill=X)

        gdModelFrame = Frame(self.win)
        l5=Label(gdModelFrame,text="Galactic Diffuse Model Name:",width=labelWidth,anchor=E)
        l5.pack(side=LEFT)
        self._gdModelNameField = Pmw.EntryField(gdModelFrame,value="GAL_v06")
        self._gdModelNameField.pack(side=LEFT)
        gdModelFrame.pack(side=TOP,expand=YES,fill=X)

        isoTempFrame = Frame(self.win)
        l6=Label(isoTempFrame,text="Isotropic Template File:",width=labelWidth,anchor=E)
        l6.pack(side=LEFT)
        self._isoTempFileField = Pmw.EntryField(isoTempFrame,value=FERMI_DIR+"/refdata/fermi/galdiffuse/isotrop_4years_P7_v9_repro_source_v1.txt")
        self._isoTempFileField.pack(side=LEFT,expand=YES,fill=X)
        b6 = Button(isoTempFrame,text="Browse...",command=(lambda: self._getFile(self._isoTempFileField)))
        b6.pack(side=LEFT)
        isoTempFrame.pack(side=TOP,expand=YES,fill=X)

        itNameFrame = Frame(self.win)
        l7=Label(itNameFrame,text="Isotropic Template Name:",width=labelWidth,anchor=E)
        l7.pack(side=LEFT)
        self._isoTempNameField = Pmw.EntryField(itNameFrame,value="Extragalactic Diffuse")
        self._isoTempNameField.pack(side=LEFT)
        itNameFrame.pack(side=TOP,expand=YES,fill=X)

        radFrame = Frame(self.win)
        l8=Label(radFrame,text="Variable Source Radius:",width=labelWidth,anchor=E)
        l8.pack(side=LEFT)
        self._radLimitField = Pmw.EntryField(radFrame,value=-1)
        self._radLimitField.pack(side=LEFT)
        radFrame.pack(side=TOP,expand=YES,fill=X)

        extTempFrame = Frame(self.win)
        self.l9 = Label(extTempFrame,text="Extended Source Template Directory:",width=labelWidth,anchor=E,state=DISABLED)
        self.l9.pack(side=LEFT)
        self._extTempFileField = Pmw.EntryField(extTempFrame,value="",entry_state=DISABLED)
        self._extTempFileField.pack(side=LEFT,expand=YES,fill=X)
        self.b7 = Button(extTempFrame,text="Browse...",command=(lambda: self._getDir(self._extTempFileField)),state=DISABLED)
        self.b7.pack(side=LEFT)

        psFrame = Frame(self.win)
        l10=Label(psFrame,text="Force Point Sources ",width=labelWidth,anchor=E)
        l10.pack(side=LEFT)
        self._psFlagField = Pmw.RadioSelect(psFrame,buttontype='radiobutton', command = self._checkForcePointSource)
        self._psFlagField.pack(side=LEFT)
        self._psFlagField.add('Yes')
        self._psFlagField.add('No')
        self._psFlagField.invoke('No')
        psFrame.pack(side=TOP,expand=YES,fill=X)

        extTempFrame.pack(side=TOP,expand=YES,fill=X)

        buttonFrame = Frame(self.win,pady=5)
        b10 = Button(buttonFrame,text="Cancel",command=(lambda: self._cancel()))
        b10.pack(side=LEFT)
        b8 = Button(buttonFrame,text="Reset Fields",command=(lambda: self._resetFields()))
        b8.pack(side=LEFT)
        b9 = Button(buttonFrame,text="Import Sources",command=(lambda: self._importSources()))
        b9.pack(side=RIGHT)
        buttonFrame.pack(side=TOP,expand=YES,fill=X)

    def _checkForcePointSource(self,tag):
        if ("Yes" == tag):
            self.l9.config(state=ACTIVE)
            self.b7.config(state=ACTIVE)
            self._extTempFileField.configure(entry_state=NORMAL)
        else:
            self.l9.config(state=DISABLED)
            self.b7.config(state=DISABLED)
            self._extTempFileField.configure(entry_state=DISABLED)

    def _cancel(self):
        """Cancels the dialog

        Paramters:
        - self - This AddCatalogSources Dialog object

        Return value:
        - none

        Description:
        This method simply sets the self.values variable to a None object to
        signify that no action was taken and then destroys the dialog window
        causing the getData() method to return the None object to the caller.
        """
        self.values = None
        self.win.withdraw()
        self.win.quit()

    def _getFile(self,e):
        """Fill filename field using Open File dialog

        Parameters:
        - self - This AddCatalogSourcesDialog object
        - e - The EntryField object to store the filename in

        Return value:
        - none

        Description:
        This method uses the standard Tkinter Open File dialog to allow the user
        to select a file name to associate with the passed in entry field.  If the
        user selects a file, it is store in the field.  If not file is selected, the
        entry field is not updated.
        """
        f = e.getvalue()
        if ("" == f):
            d = "."
        else:
            d = dirname(f)
        filename = askopenfilename(initialfile=f,initialdir=d)
        if (() != filename):
            e.setvalue(filename)

    def _getDir(self,e):
        """Fill directory name using Open Directory dialog

        Parameters:
        - self - This AddCatalogSourcesDialog object
        - e - The EntryField object to store the directory in

        Return value:
        - none

        Description:
        This method uses the standard Tkinter Open File dialog to allow the user
        to select a file name to associate with the passed in entry field.  If the
        user selects a file, it is store in the field.  If not file is selected, the
        entry field is not updated.
        """
        d = e.getvalue()
        if ("" == d):
            d = "."
        dirName = askdirectory(initialdir=d)
        if (() != dirName):
            e.setvalue(dirName)

    def _resetFields(self):
        """Resets all the user field values

        Parameters:
        - self - This AddCatalogSourcesDialog object

        Return value:
        - none

        Description:
        This method clears all user input and resets them to their default values.
        This method is the click handler for the "Reset Fields" button on the
        dialog box and is invoked when the button is pressed.
        """
        self._catalogFileField.setvalue("")
        self._eventFileField.setvalue("")
        self._sigLimitField.setvalue(4)
        self._galDiffFileField.setvalue(FERMI_DIR+"/refdata/fermi/galdiffuse/gll_iem_v06.fits")
        self._gdModelNameField.setvalue("GAL_v06")
        self._isoTempFileField.setvalue(FERMI_DIR+"/refdata/fermi/galdiffuse/isotrop_4years_P7_v9_repro_source_v1.txt")
        self._isoTempNameField.setvalue("Extragalactic Diffuse")
        self._radLimitField.setvalue(-1)
        self._psFlagField.invoke('No')
        self._extTempFileField.setvalue("")

    def _importSources(self):
        """Prepares data for return to calling program

        Parameters:
        - self - This AddCatalogSourcesDialog object

        Return value:
        - none

        Description:
        This method reads the values of all the entry fields in the dialog and
        stores their values in the internal data dictionary.  It also validates
        the entries to see that 1) files exist and 2) other entries make sense.
        Validation is limited, however, and relies on upstream checking of data
        before final use.  Once the data is stored, this method closes the dialog
        box allowing the data to be returned.  This method is the click handler
        for the "Import Sources" button.
        """
        # Validate entries to make sure the files at least exist.  This should
        # only be a problem if the user typed in the entry instead of using the
        # file browser.
        validCF = isfile(self._catalogFileField.getvalue())
        validEF = isfile(self._eventFileField.getvalue())
        validGF = isfile(self._galDiffFileField.getvalue()) or ("" == self._galDiffFileField.getvalue())  #these are optional
        validIF = isfile(self._isoTempFileField.getvalue()) or ("" == self._isoTempFileField.getvalue())
        validETD = not (not isdir(self._extTempFileField.getvalue()) and ("Yes" == self._psFlagField.getvalue()))
        if (validCF and validEF and validGF and validIF):
            # They are all good so load up the values and return
            self.values["catalogFile"] = self._catalogFileField.getvalue()
            self.values["eventFile"] = self._eventFileField.getvalue()
            self.values["sigLimit"] = self._sigLimitField.getvalue()
            self.values["galDiffFile"] = self._galDiffFileField.getvalue()
            self.values["gdModelName"] = self._gdModelNameField.getvalue()
            self.values["isoTempFile"] = self._isoTempFileField.getvalue()
            self.values["isTempName"] = self._isoTempNameField.getvalue()
            self.values["radiusLimit"] = self._radLimitField.getvalue()
            flag = self._psFlagField.getvalue()
            if ('Yes' == flag):
                self.values["forcePointSource"] = True
            else:
                self.values["forcePointSource"] = False
            self.values["extTempDir"] = self._extTempFileField.getvalue()

            self.win.withdraw()
            self.win.quit()
        else:
            msg = "The files listed in the following fields do not exist.  Please correct them.\n\n"
            if (not validCF):
                msg += "Source Catalog File\n"
            if (not validEF):
                msg += "Event File\n"
            if (not validGF):
                msg += "Galactic Diffuse Model File\n"
            if (not validIF):
                msg += "Isotropic Template File\n"
            if (not validETD):
                msg += "Extended Source Template Directory\n"
            Pmw.MessageDialog(self.win, message_text=msg)

    def getData(self):
        """Public method to invoke the dialog

        Parameters:
        - self - This AddCatalogSourcesDialog object

        Return value:
        - self.values - a dictionary containing all the user entered (or default)
          values for the parameters needed to import sources from the Fermi LAT
          catalogs into the current model.

        Description:
        This method invokes the _draw() method to create the dialog box, starts it
        running, and returns the data values once the dialog is closed.
        """
        self._draw()
        self.win.mainloop()
        return self.values

if __name__ == '__main__':
    Pmw.initialise()
    dialog = AddCatalogSourcesDialog()
    data = dialog.getData()
    print data
