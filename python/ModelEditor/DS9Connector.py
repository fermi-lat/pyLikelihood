# $Id: DS9Connector.py,v 1.1.2.4 2015/05/14 17:49:42 areustle Exp $

#******************************************************************************

# Import external modules.
from Source import Source
from Parameter import Parameter
from SpatialModel import SpatialModel
from FitsFile import FitsFile

# Standard modules
from tkMessageBox import askyesno, showwarning
from tkFileDialog import Open
import thread
from time import sleep
import Queue
import re

# Third-party modules
from ds9 import *

#******************************************************************************

class DS9Connector():
    """
    """
    def __init__(self,srcLibDocEditor):
        """Initialize the class

        Parameters:
        - self - This DS9Connector object
        - srcLibDocEditor - Reference to the main SourceLibraryDocumentEditor
                            Object containing the list of sources.

        Return value:
        - none

        Description:
            This method initializes all the necessary variables for the interaction
        with ds9.
        """
        self.showDS9Sources = False
        self.showDS9TextLabels = False
        self.ds9 = None
        self.sourceLibraryDocumentEditor = srcLibDocEditor
        self.sourceRaDexRegex = re.compile('(\d+[.\d+]*),(\d+[.\d+]*),\d+"')
#        self.sourceRaDexRegex = re.compile('\((\d*),(\d*),')
        self.docLock = thread.allocate_lock()#lock
        self.tolerance = 0.0001
        pass

    def connect(self):
        """Establish connection to ds9 instance

        Parameters:
        - self - This DS9Connector object

        Return value:
        - none

        Description:
            After checking to establish that no ds9 connection already exists,
        this method invokes pyds9's ds() constructor which will connect to an
        existing ds9 program or launch one if none are running.  The connection
        is stored as the self.ds9 variable that is used for communication with
        the ds9 program.
            This method also starts another thread that will monitor ds9 to look
        for changes to the regions there to capture the creation or selection of
        new regions and create or highlight the appropriate source in the
        ModelEditor
        """
        if (not self._isConnected()):
            try:
                self.ds9 = ds9()
    #            print "Setting wcs"
                self.ds9.set("regions system wcs")
    #            print "Clearing existing regions in display"
                self.ds9.set("regions delete all")
    #            print "Creating communication queue"
                self.queue = Queue.Queue()
    #            print "Starting monitoring thread"
                self.monitorThread = thread.start_new_thread(self._ds9Monitor, (self.sourceLibraryDocumentEditor,))
    #            print "Thread started"
                self._update()
            except ErrorValue:
                showerror("DS9 Connection Failed: {}".format(ErrorValue.strerror))


    def _checkConnection(self):
        """Check ds9 connection and prompt to establish if not connected

        Parameters:
        - self - This DS9Connector object

        Return value:
        - none

        Description:
            This method invokes the private _isConnected() method to validate
        the ds9 connection.  If not connected it prompts the user to see if
        they want to connect and if so, calles the connect() method to do so.
        """
        if (not self._isConnected()):
            open = askyesno("DS9 not connected!","The ModelEditor is not connected\nto a ds9 instance.\n\nWould you like to connect?")
            if (open):
                self.connect()

    def loadImage(self):
        """Load an image into ds9

        Parameters:
        - self - This DS9Connector object

        Return value:
        - ra - the ROI center RA coordinate
        - dec - the ROI center Dec coordinate

        Description:
            After checking for a connection to ds9, if connected the method
        launches and Open File dialog to allow the user to select an image
        file to display.  Once selected it attempts to display the file in
        ds9.  If the file type is unsupported, the user is warned of such.
            If the file is supported, the program attempts to load and
        extract the images ROI data and passes it back to the calling
        method.
        """
        noROIData = (-1,0,0)
        self._checkConnection()
        if (self._isConnected()):
            # open file dialog to get name
            path = Open().show()
            if path == ():
                return noROIData
            # open the file in window
            try:
                self.ds9.set("fits " + path)
                file = FitsFile(path)
                if file.hasROIData():
                    return file.getROIData()
                else:
                    return noROIData
            except:
                showwarning("File Type Error!", "The specified file is not a valid FITS image")
                return noROIData

    def togglePlotSources(self,menu,check = True):
        """Toggle whether or not to display the sources in the ds9 window.

        Parameters:
        - self - This DS9Connector object

        Return value:
        - none

        Description:
            This method toggles the display of the sources on the image
        in ds9.  When active, the menu item is set to be red.
        """
        self.menu = menu
        if check:
            self._checkConnection()
        self.showDS9Sources = not self.showDS9Sources
        if (self.showDS9Sources):
            menu.entryconfig(3,foreground="red", activeforeground="red")
        else:
            menu.entryconfig(3,foreground="black", activeforeground="black")
        self.plotSources()

    def toggleTextLabels(self,menu):
        """Toggle wheter or not to display the source labels

        Parameters:
        - self - This DS9Connector object

        Return value:
        - none

        Description:
            This method toggles the display of the sources' text labels
        on the image in ds9.  When active, the menu item is set to be red.
        """
        self._checkConnection()
        self.showDS9TextLabels = not self.showDS9TextLabels
        if (self.showDS9TextLabels):
            menu.entryconfig(4,foreground="red", activeforeground="red")
        else:
            menu.entryconfig(4,foreground="black", activeforeground="black")
        self.plotSources()

    def _isConnected(self):
        """Validate ds9 connection

        Parameters:
        - self - This DS9Connector object

        Return value:
        - True or false depending on connection state

        Description:
            This method check the state of the ds9 connection.  If the
        self.ds9 object is None, it returns false indicating no ds9
        connection.  If not false, it attempts an access operation to
        verify that ds9 has not been closed externally.  If the command
        works, the connection is valid and the method returns True.  If
        not, the self.ds9 object is set to None and the method returns
        False.
        """
        if (None == self.ds9):
            return False
        else:
            try:
                self.ds9.access()
                return True
            except:
                self.ds9=None
                return False

    def plotSources(self):
        """Draw the source regions in ds9

        Parameters:
        - self - This DS9Connector object

        Return value:
        - none

        Description:
            This method runs through the list of sources in the model
        and draws circular regions around them in the ds9 window.
        the currently selected region is highlighted in red while all
        the other regions are white.
            Thread locks are set on all access to the ds9 object as well
        as access to the SourceLibraryDocumentEditor object to prevent
        race conditions that cause the application to become hung and
        stop responding.
        """
        if(not self._isConnected()): return
        with self.docLock:
            self.ds9.set("regions delete all")
        # first check if we should even be plotting the sources
        if (self.showDS9Sources):
            # this gives us an array of Source Objects
            with self.docLock:
                srcListDoc = self.sourceLibraryDocumentEditor.get()
                srcList = srcListDoc.getSourceLibrary().getSources()
                selected = self.sourceLibraryDocumentEditor.getCurrentSourceIndex() #get the index of selected source
            i=0;
            for src in srcList:
                try: # we do this all in a try block as not all sources have the correct spatial model,
                    #extract source parameters
                    ra = src.getSpatialModel().getParameterByName("RA").getValue()
                    dec = src.getSpatialModel().getParameterByName("DEC").getValue()
                    #create ds9 region command
                    cmd = "fk5; circle("+str(ra)+","+str(dec)+", 1) #color = "
                    if (i==selected):
                        cmd += "red"
                    else:
                        cmd += "white"
                    # do we want labels?
                    if (self.showDS9TextLabels):
                        cmd += " text = {"+src.getName()+"}"
                    #draw region
                    with self.docLock:
                        self.ds9.set("regions",cmd)
                except: # we just skip those that don't have a position
                    pass
                i += 1
        else:  #if not, clear them
            pass

    def _ds9Monitor(self,docEditor):
        """Watch ds9 instance for changes

        Parameters:
        - self - This DS9Connector object

        Return value:
        - none

        Description:
            This is the main loop that runs in a separate thread
        to regularly poll ds9 for changes to its region list to
        look for a change in region selection as well as new regions
        being created.
            This method and all methods it calls must not access
        any of the Tkinter widgets as they are not thread safe and
        will cause exceptions to be thrown.  All actions that require
        access to the GUI must be run on the main thread.  This is
        realized by submitting the function and its arguments to the
        communication queue (self.queue) which is polled regularly by
        the main thread.
            The check is currently set to run up to 10 times a second.
        In practice it doesn't repeat that often as the processing time
        for the called functions is slower than that.
        """
        while (None != self.ds9):
            if (self.showDS9Sources): # we only do these tasks if we're displaying sources
                # look to see if any are new and add them
                self._checkForNewDS9Regions()
                # Get selected ds9 region (if any)
                self._checkForSelectedDS9Region()
            sleep(0.1)

    def _getDS9Regions(self,type):
        """Retrieve specified list of regions from ds9

        Parameters:
        - self - This DS9Connector object
        - type - The type of region list to retrieve.  Allowed options are "selected" and "all"

        Return value:
        - regionList - a list of strings containing the ds9 region designations

        Description:
            This method queries ds9 for the requested region list.  The
        list returned by ds9 is stripped of its header information and just
        the actual region entries are returned.  If there is an error or no
        regions exist in ds9 an empty list is returned.
            As this method is the main query method to retrieve information
        from ds9 it also guards against a disconnected ds9 instance caused by
        the user closing the ds9 window.  In that case, it sets the internal
        ds9 object to a None object so that a reconnection attempt may be
        performed by the user.  It also turns off the plot sources flag.
            Access to the ds9 object is controlled with a thread log to prevent
        program lockup.  This method runs in the alternate thread and thus
        must pass the command to toggle the plot sources flag to the main
        thread as that method creates a change in the GUI (changes menu option
        text color).
        """
        regionList = []
        # first some error guards
        validTypes = ["selected","all"]
        if not type in validTypes: return regionList  # make sure we're looking for a valid region list
        if self.ds9 == None: return regionList        # make sure we have a ds9 connection

        cmd = "regions " + type
        try:
            with self.docLock:
                regions = self.ds9.get(cmd)
                regionList = regions.split("\n")[3:]  # first 3 lines hold no information that we need
        except:
            self.ds9 = None # we've been disconnected
            if self.showDS9Sources:
                self.queue.put((self.togglePlotSources,[self.menu,False]),False)
        return regionList

    def _checkForSelectedDS9Region(self):
        """Check list of ds9 regions to see if a new one has been selected

        Parameters:
        - self - This DS9Connector object

        Return value:
        - none

        Description:
            This method polls ds9 for the list of selected regions.  If
        one (or more) exist, the first one is set as the selected region
        in the model editor.
            The RA and Dec of the selected region is extracted from
        the ds9 region list and then the method runs through the list
        of sources looking for the source with matching coordinates.
        Coordinate matching is done to within a tolerance (self.tolerance)
        to handle rounding in the ds9 data representation.
            Matching of the RA/Dec is handled in a try block as not all
        sources have spatial models that include RA/Dec and those that don't
        will throw an exception.  Since those models are not displayed as
        sources on the image the caught exception is ignored and processing
        simply continues on.
            Once a match is found the source is passed to the
        _setDS9SelectedSrc() method on the main thread via the communication
        queue to trigger the interface update and then the method returns.
            Access to the SourceLibraryDocumentEditor object is controlled
        via a thread lock to prevent race conditions.
        """
#        print "entering _checkForSelectedDS9Region"
        regionList = self._getDS9Regions("selected")
        # find the region in the list of sources
        if (len(regionList) > 0):
            match = self.sourceRaDexRegex.search(regionList[0])
            if (None != match):  #good source
                targetRA = float(match.group(1))
                targetDec = float(match.group(2))
            with self.docLock:
                srcList = self.sourceLibraryDocumentEditor.getSourceLibrary().getSources()
            foundSrc = None
            for src in srcList:
                try: # we do this all in a try block as not all sources have the correct spatial model,
                    #extract source parameters
                    ra = float(src.getSpatialModel().getParameterByName("RA").getValue())
                    dec = float(src.getSpatialModel().getParameterByName("DEC").getValue())
                    if (abs(targetRA - ra) < self.tolerance and abs(targetDec - dec) < self.tolerance):
#                        print "New Source Selected:",ra,",",dec
                        self.queue.put((self._setDS9SelectedSrc,[src]),False)
                        return  # we found it so we're done
                except: # we just skip those that don't have a position
                    pass

    def _setDS9SelectedSrc(self,src):
        """Update selected source in model editor GUI

        Parameters:
        - self - This DS9Connector object
        - src - The Source object of the source selected in the ds9 window

        Return value:
        - none

        Description:
            This method simply calls the SourceLibraryDocumentEditor object's
        selectSource() method with the name of the source that was picked
        in the ds9 window.
            As this method updates the model editor GUI it must run in the
        main thread.
        """
        self.sourceLibraryDocumentEditor.selectSource(src.getName())

    def _checkForNewDS9Regions(self):
        """Check list of ds9 regions to see if a new one has been added

        Parameters:
        - self - This DS9Connector object

        Return value:
        - none

        Description:
            This method polls ds9 for the list of all regions.  If
        one (or more) exist, they are compared against the list of
        sources in the model editor to see if any are new.
            The RA and Dec of each region is extracted from
        the ds9 region list and then the method runs through the list
        of sources looking for the source with matching coordinates.
        Coordinate matching is done to within a tolerance (self.tolerance)
        to handle rounding in the ds9 data representation.
            Matching of the RA/Dec is handled in a try block as not all
        sources have spatial models that include RA/Dec and those that don't
        will throw an exception.  Since those models are not displayed as
        sources on the image the caught exception is ignored and processing
        simply continues on.
            If a match is found the inner loop running over all the sources
        is terminated and the method moves on to the next ds9 region.  If all
        of the sources have been checked and no match has been found, the
        region is considered to be a new source and a call to the _addNewSource()
        method is placed on the communication queue to be executed by the main
        thread.
            Access to the SourceLibraryDocumentEditor object is controlled
        via a thread lock to prevent race conditions.  This method runs in the
        alternate thread and thus must not execute functions that update the
        GUI directly.

        NOTE:  This method is currently very slow, O(N^2) as it potentially
        loops over every entry in both the region and source lists.  As such
        is bogs down the interface somewhat making it not as responsive as
        would be desired.  Work should go into looking at ways to optimize
        this method, probably involving additional data structures to hold
        the data searched over to improve search performace.
        """
#        print "entering _checkForNewDS9Regions"
        # get full list of ds9 regions
        regionList = self._getDS9Regions("all")

        with self.docLock:
            srcList = self.sourceLibraryDocumentEditor.getSourceLibrary().getSources()
        for region in regionList:
            # extract ra/dec from ds9 region entry
            match = self.sourceRaDexRegex.search(region)
            if (None != match):  #good source
                targetRA = float(match.group(1))
                targetDec = float(match.group(2))
                newSrc = True
                for src in srcList:
                    try: # we do this all in a try block as not all sources have the correct spatial model,
                        #extract source parameters
                        ra = float(src.getSpatialModel().getParameterByName("RA").getValue())
                        dec = float(src.getSpatialModel().getParameterByName("DEC").getValue())
                        if (abs(targetRA - ra) < self.tolerance and abs(targetDec - dec) < self.tolerance):
                            newSrc = False
                            break  # bust out of for src loop if we match
                    except: # we just skip those that don't have a position
                        pass
                if (newSrc):
                    #now we need to queue up a function to create the new source and add it to the source model
                    self.queue.put((self._addNewSource,[targetRA,targetDec]),False)

    def _addNewSource(self,ra,dec):
        """Add new source to the model

        Parameters:
        - self - This DS9Connector object
        - ra - The RA of the center of the ds9 region to be added as a source
        - dec - The Dec of the cetner of the ds9 region to be added as a source

        Return value:
        - none

        Description:
            This method adds a default Source object (PowerLaw spectrum) at
        the RA and Dec passed to it.  The source name is constructed from the
        RA and Dec and proceeded with the 'ME_' designation to show it was
        added via ds9 and the model editor.
            Access to the SourceLibraryDocumentEditor object is controlled
        via a thread lock to prevent race conditions.  As this method causes
        modifications in the GUI, it must be run on the main thread.
        """
#        print "Entering _addNewSource"
        # create a name
        name = "ME_" + str(ra) + "_" + str(dec)
        # make a default PL source
        source = Source(name=name)
        # set the RA/dec
        raParam = Parameter(name="RA",value = ra, scale = 1.0, min = 0.0, max = 360.0, free = False)
        decParam = Parameter(name="DEC",value = dec, scale = 1.0, min = -90.0, max = 90.0, free = False)
        spatialModel = SpatialModel(type="SkyDirFunction",parameters=[raParam,decParam])
        source.setSpatialModel(spatialModel)

#        print "Locking editor"
        # add source to model list
        with self.docLock:
            sourceLibraryDocument = self.sourceLibraryDocumentEditor.get()
            sourceLibraryDocument.addSource(source)
            self.sourceLibraryDocumentEditor.set(sourceLibraryDocument)
            self.sourceLibraryDocumentEditor.commit()
#        print "Unlocked editor"
        #get Source index of new source and set as selected source
        self.sourceLibraryDocumentEditor.selectSource(name)
#        print "Leaving _addNewSource"

    def _update(self):
        """Poll communication queue for ds9 changes.

        Parameters:
        - self - This DS9Connector object

        Return value:
        - none

        Description:
            This method is the consumer of the messages placed on
        the communications queue (self.queue).  As such it runs in the
        main GUI thread to process method calls that must run on that
        thread.
            This method works by poling the communication queue for
        new messages.  Messages consist of a tuple containing two items.
        The first is a callable object, typically class method.  The
        second is a list of values that are the arguments to the passed
        method.
            For each message the method and arguments are called via
        the after_idle() method to be executed at the next pause of
        GUI activity.
            The method reads up to ten messages off the queue at a time.
        Once all messages have been processed, the method reschedules
        itself for execution after a short time (currently 30 milliseconds)
        """
        for i in xrange(10):
            try:
                (func,args) =  self.queue.get(False)
            except Queue.Empty:
                break

            self.sourceLibraryDocumentEditor.after_idle(func, *args)
        self.sourceLibraryDocumentEditor.after(30, self._update)

