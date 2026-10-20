if {[catch {
set report [lindex $argv 1]
set_param general.maxThreads 8
open_project [lindex $argv 0]
open_run impl_1
check_timing -verbose -file $report/check_timing.txt
report_timing_summary -report_unconstrained -check_timing_verbose -file $report/timing_full.txt
report_timing -delay_type min -max_paths 5 -file $report/hold_paths.txt
report_timing -delay_type max -max_paths 5 -file $report/setup_paths.txt
report_drc -file $report/drc.txt
puts "TIMING_COVERAGE_REPORTS_WRITTEN"
close_project
} message]} {puts stderr $message; puts stderr $::errorInfo; exit 1}
exit 0
