#!/usr/bin/gnuplot
reset

set terminal png size 1920,1080

set xdata time
set timefmt "%Y-%m-%dT%H:%M:%SZ"

set format x "%M:%S"
set xlabel "time"

set ylabel "whaaats"
set yrange [200:400]

set title "waats"
set key reverse Left outside
set grid

set style data lp

min(a,b) = a >= b ? b : a
samples(n) = min(int($0), n)
avg_data = ""

sum_n(data, n) = ( n <= 0 ? 0 : word(data, words(data) - n) + sum_n(data, n - 1))

avg(x, n) = ( avg_data = sprintf("%s %f", (int($0)==0)?"":avg_data, x), sum_n(avg_data, samples(n))/samples(n)) 


plot "toplot.txt" using 1:(avg(column(2), 10)) title "realwatt", \
"" using 1:3 title "Golden 0%", \
"" using 1:5 title "Golden 2%", \
"" using 1:8 title "Trainerroad"
#"" using 1:4 title "kFejkwatt", \
#"" using 1:6 title "kFejkwatttwo", \
#"" using 1:7 title "kFejkwatt3"
