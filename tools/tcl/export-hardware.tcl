if {[catch {
set report [lindex $argv 1]
set root [file normalize "$report/../../.."]
open_checkpoint "$root/.work/reports/hold-fix/routed.dcp"
report_methodology -file "$report/methodology.txt"
write_hw_platform -fixed -force -file "$report/system_top.xsa"
puts "HARDWARE_XSA_OK"
close_design
} message]} {puts stderr $message; puts stderr $::errorInfo; exit 1}
exit 0
