if {[catch {
set project [lindex $argv 0]
set report [lindex $argv 1]
set_param general.maxThreads 8
open_project $project
report_ip_status -file $report/ip_before.txt
set locked {}
foreach ip [get_ips -all] {if {[get_property IS_LOCKED $ip]} {lappend locked $ip}}
puts "LOCKED_BEFORE=[llength $locked]"
if {[llength $locked]} {upgrade_ip $locked}
set bd [get_files */system.bd]
open_bd_design $bd
validate_bd_design
save_bd_design
report_ip_status -file $report/ip_after.txt
set locked {}
foreach ip [get_ips -all] {if {[get_property IS_LOCKED $ip]} {lappend locked $ip}}
puts "LOCKED_AFTER=[llength $locked]"
if {[llength $locked]} {error "Locked IP remains: $locked"}
generate_target all $bd
write_bd_tcl -force $report/system_bd_2025_2.tcl
puts "BD_VALIDATE_OK"
close_project
} message]} {
puts stderr $message
puts stderr $::errorInfo
exit 1
}
exit 0
