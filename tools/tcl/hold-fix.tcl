if {[catch {
set report [lindex $argv 1]
set_param general.maxThreads 8
open_project [lindex $argv 0]
open_run impl_1
puts "HOLD_BEFORE=[get_property SLACK [get_timing_paths -delay_type min -max_paths 1]]"
phys_opt_design -aggressive_hold_fix
route_design -directive Explore
report_timing_summary -report_unconstrained -check_timing_verbose -file $report/timing.txt
report_timing -delay_type min -max_paths 5 -file $report/hold_paths.txt
report_drc -file $report/drc.txt
check_timing -verbose -file $report/check_timing.txt
write_checkpoint -force $report/routed.dcp
set setup [get_timing_paths -delay_type max -max_paths 1]
set hold [get_timing_paths -delay_type min -max_paths 1]
puts "SETUP_SLACK=[get_property SLACK $setup]"
puts "HOLD_SLACK=[get_property SLACK $hold]"
if {[get_property SLACK $setup] < 0 || [get_property SLACK $hold] < 0} {error "Post-route timing remains failing"}
if {[llength [get_drc_violations -filter {SEVERITY == Error}]]} {error "DRC errors remain"}
puts "POST_ROUTE_HOLD_FIX_OK"
close_project
} message]} {puts stderr $message; puts stderr $::errorInfo; exit 1}
exit 0
