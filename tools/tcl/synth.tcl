if {[catch {
set report [lindex $argv 1]
set_param general.maxThreads 8
open_project [lindex $argv 0]
reset_run synth_1
launch_runs synth_1 -jobs 4
wait_on_run synth_1
puts "SYNTH_STATUS=[get_property STATUS [get_runs synth_1]]"
if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} {error "Synthesis did not complete"}
open_run synth_1
report_utilization -file $report/utilization.txt
report_timing_summary -file $report/timing.txt
report_drc -file $report/drc.txt
write_checkpoint -force $report/synth.dcp
puts "SYNTHESIS_OK"
close_project
} message]} {puts stderr $message; puts stderr $::errorInfo; exit 1}
exit 0
