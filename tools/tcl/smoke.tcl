set target xc7z020clg400-2
puts "VIVADO_VERSION=[version -short]"
puts "PART_COUNT=[llength [get_parts]]"
if {[llength [get_parts $target]] != 1} {puts stderr "Target part missing: $target"; exit 1}
puts "SMOKE_OK"
exit 0
