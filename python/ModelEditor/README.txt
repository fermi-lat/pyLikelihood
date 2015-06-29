$Id: README.txt,v 1.1.1.1 2008/04/20 15:03:22 elwinter Exp $

The GLAST Science Tools Model Editor (HEADAS version)
-----------------------------------------------------

The Model Editor (ModelEditor) is a program developed to ease the
process of creating XML input files for the GLAST likelihood estimator
tool (gtlike). The current ModelEditor is based on an earlier design
by Jim Chiang at SLAC.

To increase the portability of the code, the ModelEditor was written
in Python. User interface elements were developed using the standard
Tk toolkit, as well as the freely-available Pmw toolkit. The HEADAS
version of the ModelEditor is currently being distributed on an
experimental basis.

Instructions for using the ModelEditor are in the file help.txt.

Building and installing the ModelEditor
---------------------------------------

0. Make sure you have properly installed the latest version of the
   GLAST Science Tools, set your HEADAS environment variable, and run
   the associated science tools setup script,
   e.g. sciencetools_setup_beta.sh.

1. Install the Tcl language.

   tar xzvf tcl8.4.15-src.tar.gz
   cd tcl8.4.15/unix # If using Linux; cd to tcl8.4.15/macosx if using Mac OS X
   ./configure --prefix=$HEADAS  # $HEADAS is the value of your HEADAS
                                 # environment variable.
   make
   make install

3. Install the Tk graphics toolkit:

   tar xzvf tk8.4.15-src.tar.gz
   cd tk8.4.15/unix # If using Linux; cd to tk8.4.15/macosx if using Mac OS X
   ./configure --prefix=$HEADAS  # $HEADAS is the value of your HEADAS
                                 # environment variable.
   make
   make install

4. Rebuild your Python to support Tk.

   cd $HEADAS/../external/python
   ./configure --prefix=$HEADAS
   make
   make install

5. Install the Pmw user interface toolkit:

   tar xzvf Pmw.1.3.tar.gz  # Unpacks into 'src'.
   cd src
   cp -r Pmw $HEADAS/lib/python2.5/site-packages

6. Unpack and run the ModelEditor:

   tar xzvf ModelEditor.tar.gz
   cd ModelEditor
   python ModelEditor.py

   Select the Help menu for more information on using the ModelEditor.

Please send any feedback to Eric Winter (Eric.L.Winter@nasa.gov).
