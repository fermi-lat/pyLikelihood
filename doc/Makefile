all:
	touch Doxyfile
	cat ${GLASTPOLICYROOT}/doc/Doxyfile Doxyfile > Doxyfile.tmp
	rm -f ../${BINDIR}/*_wrap.cxx
	doxygen Doxyfile.tmp
	rm -f Doxyfile.tmp
