set root [file normalize [lindex $argv 0]]
set out "$root/.work/firmware/bsp2025"
file mkdir $out
if {[catch {
hsi::open_hw_design "$root/.work/reports/export-hardware/system_top.xsa"
hsi::create_sw_design plutosky_standalone -proc ps7_cortexa9_0 -os standalone
hsi::generate_bsp -dir $out
file copy -force "$root/.work/reports/export-hardware/system_top.xsa" "$out/hardware.xsa"
puts "BSP_GENERATED_OK"
hsi::close_hw_design [hsi::current_hw_design]
} message]} {puts stderr $message; puts stderr $::errorInfo; exit 1}
exit 0
