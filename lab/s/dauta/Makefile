all:
	xml2 < kbeckmann-2014-12-16-a-very-dark-place-pre-june-2013--1355129.tcx > xml.txt
	php parse.php  > toplot.txt
	./plot.gnuplot > fejk.png
	./plot_avg.gnuplot > fejk_avg.png			
