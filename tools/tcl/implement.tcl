if {[catch {
set report [lindex $argv 1]
set_param general.maxThreads 8
open_project [lindex $argv 0]
if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} {error "Synthesis prerequisite not complete"}
reset_run impl_1
launch_runs impl_1 -to_step route_design -jobs 4
wait_on_run impl_1
puts "IMPL_STATUS=[get_property STATUS [get_runs impl_1]]"
if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {error "Implementation did not complete"}
open_run impl_1
report_timing_summary -file $report/timing.txt
report_route_status -file $report/route.txt
report_drc -file $report/drc.txt
set setup [get_timing_paths -delay_type max -max_paths 1]
set hold [get_timing_paths -delay_type min -max_paths 1]
if {![llength $setup] || ![llength $hold]} {error "No timing paths available"}
puts "SETUP_SLACK=[get_property SLACK $setup]"
puts "HOLD_SLACK=[get_property SLACK $hold]"
if {[get_property SLACK $setup] < 0 || [get_property SLACK $hold] < 0} {error "Timing failed"}
if {[llength [get_drc_violations -filter {SEVERITY == Error}]]} {error "DRC errors remain"}
puts "IMPLEMENTATION_TIMING_OK"
close_project
} message]} {puts stderr $message; puts stderr $::errorInfo; exit 1}
exit 0
