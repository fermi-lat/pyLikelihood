# $Id: FitsFile.py,v 1.1.2.3 2015/04/07 19:05:25 areustle Exp $

#******************************************************************************

# Import external modules.
from tkMessageBox import showerror

# Standard modules

# Third-party modules
import pyfits

# Project modules

# set up some aliases and constants
ROITypes = ['FT1','image']
validCatTypes = ['3FGL','2FGL','1FGL']

#******************************************************************************

class FitsFile():
    """Class to handle FITS file for use by the ModelEditor

    Usage:
         file = FitsFile(filename)

         where filename is the FITS file to be worked with

    Description:
        This class is primarily intended for use with the routines that
    import the source lists from the Fermi Catalog or display images on
    ds9.  It is designed to determine the file type and return the necessary
    information from the provided file.

    """
    def __init__(self,file):
        self.filename = file;
        self._ROI_RA = -1
        self._ROI_Dec = 0
        self._ROI_radius = 0
        self.fileType=None

        if not self._isFITS(): return None
        if not self._determineType(): return None
        if self.fileType in ROITypes:
            self._extractROIData()
            if -1 == self._ROI_RA : return None


    def _isFITS(self):
        """Check that the provided file exists and is a FITS file

        Description:
            This method checks to see if the specified file exits and if so if it
        is a valid FITS file.  If not, the internal FITS file pointer is set to
        a None object and the method returns False.  If the file is good, it is opened
        and pointed to by the internal FITS file pointer and the method returns true.
        """
        try:
            self.fitsFilePtr = pyfits.open(self.filename)
        except:  # we get here only if the file doesn't even exist
            showerror("File Not Found", "Specified file doesn't exist.")
            self.fitsFilePtr = None
        if ([] == self.fitsFilePtr):  #the file either didn't exist or was not a valid FITS file
            showerror("Bad File Type", "Specified file is not a valid FITS file.")
            self.fitsFilePtr = None
        if (None == self.fitsFilePtr):
            return False
        else:
            return True

    def _determineType(self):
        """Determines the type of FITS file

        Description:
            This method looks for various specfic characteristics of FITS files
        needed by the ModelEditor and determines the type of file that has been
        loaded.  The currently supported file types are:
            * FT1 event files
            * image files created by gtbin
            * The 1FGL and 2FGL catalog files

            Once the type is detemined, it is stored in the self.fileType variable
        and this type determines how many of the other class methods respond.
        """
        # first we look to see if we've got an FT1 or image file.  Thise file types have the NDSKEYS
        # keyword in either the second (FT1) or first (image) headers.  We're using try/except blocks
        # becasue the pyfits library throws exceptions is you try to get a header keyword that doesn't
        # exist.
        try:
            #headers start at 0 index so we want the second one with the event data and DSS keys
            header = self.fitsFilePtr[1].header
            ndskeys = header['NDSKEYS']
            self.fileType = "FT1"
            return True
        except:
            try:
                header = self.fitsFilePtr[0].header
                ndskeys = header['NDSKEYS']
                self.fileType = "image"
                return True
            except:
                # Now we look for markers of the catalog files
                header = self.fitsFilePtr[1].header
                try:
                    catType=header['CDS-NAME']
                    if catType in validCatTypes:
                        self.fileType = catType
                        return True
                    else:
                        showerror("Invalid File", "The file specified is not a supported file type.")
                        return False
                except:
                    showerror("Invalid File", "The file specified is not a supported file type.")
                    return False

    def _getROIHeader(self):
        """Get the header with the ROI information

        Description:
            This method returns the proper header that contains the information needed to
        determine the Region of Interest from the specified file.
        """
        if 'FT1' == self.fileType:
            return self.fitsFilePtr[1].header
        else:
            return self.fitsFilePtr[0].header


    def _extractROIData(self):
        """ Check and extract ROI data

        Description:
            This method checks that the necessary DSS keywords exist for determining the
        Region of Interest and if so, extracts the ROI information
        """
        header = self._getROIHeader()
        ndskeys = header['NDSKEYS']
        i = 1
        keyPosition = 0
        isValid = False
        targetKey = 'POS(RA,DEC)'
        while i <= ndskeys:  # we look through all the keys since they don't always have to be in the same order
            key = 'DSTYP%i' %i
            test = header[key]
            if (targetKey == test):
                isValid = True
                keyPosition=i
                break  # we found it so we don't need to keep looking
            i += 1
        if (isValid):
            keyword='DSVAL%i' % keyPosition
            if ('circle' == header[keyword][:6]):  # The Science Tools only implement circular searches so just check for upper/lower case spelling
                ra,dec,rad=header[keyword].strip('circle()').split(',') #gets rid of the circle and parenthesis part and splits around the comma
            else:
                ra,dec,rad=header[keyword].strip('CIRCLE()').split(',')
            self._ROI_RA = float(ra)
            self._ROI_Dec = float(dec)
            self._ROI_radius = float(rad)
        else:
            showerror("Invalid File","No ROI position information found in file")

    def getROIData(self):
        if self.fileType in ROITypes:
            return self._ROI_RA, self._ROI_Dec, self._ROI_radius
        else:
            return None,None,None

    def hasROIData(self):
        if -1 == self._ROI_RA:
            return False
        else:
            return True

    def getType(self):
        return self.fileType
