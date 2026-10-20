# Standalone PlutoSky firmware workflow

This lane builds the supplied no-OS application for Cortex-A9. It does not provide a Linux/IIO image or program a board. Start with the pinned HDL and the repaired routed checkpoint described in DEVELOPMENT.md.

1. Export the hardware from the repaired checkpoint:
   `tools/run-vivado export-hardware`
2. Build using a locally staged vendor archive whose SHA-256 matches project.lock.json:
   `tools/build-firmware /local/cache/vendor_2021_1.rar`
3. Verify source and artifact consistency:
   `python3 tools/selftest.py`

The second command discovers the ARM toolchain for the pinned AMD release, generates a standalone BSP with XSCT/HSI, compiles libxil with the native ARM GCC, then builds all 38 application C files. All work is under .work on local disk. Genuine ABI-5 XSCT libraries are scoped to the child process through run-xsct.

Outputs:
- .work/reports/export-hardware/system_top.xsa: hardware-only export, no bitstream.
- .work/firmware/bsp2025/hardware.xsa: exact BSP input retained for hashing.
- .work/firmware/build-modern/plutosky-vendor-app.elf: standalone ARM ELF.
- .work/reports/firmware-modern/: logs, commands, source checksums, applied fix and result.
- .work/reports/selftest/result.json: artifact consistency result and open gates.

The application init call is guarded before FIR configuration. The script verifies the expected vendor call before patching the disposable source. It preserves the original archive and records both source hashes. Compilation and linking do not prove the error path on hardware.

The fallback `python3 tools/build_vendor_firmware.py --archive /local/cache/vendor_2021_1.rar --toolchain /path/to/arm/bin` uses the supplied prebuilt BSP. Its result explicitly records that narrower scope. Use the regenerated BSP lane above for the integrated candidate.

Readiness remains NOT_FOR_FLASH until board revision/RF part, CTRL_IN2 pin mapping, bank VCCO, source-synchronous RX/TX timing, CDC/clock methodology, boot integration and physical tests are addressed. The vendor application enables ADC/DAC DMA examples; IIO is disabled. The ELF is an engineering candidate, not a bootable SD/flash image. FSBL and boot packaging are separate work.

Acceleration order:
1. Resolve board pin/VCCO/RF-part evidence and review clock/CDC exceptions. Capture report_cdc and exception coverage from the accepted checkpoint.
2. Add board-supported source-synchronous IO constraints using actual AD936x mode and board timing; rerun only affected implementation/signoff stages.
3. Repair legacy IRQ callback types with a meaningful IRQ-path regression before enabling that path.
4. Build FSBL and boot package from the same hardware export; perform instrumented board bring-up before enabling streaming/RF tests.
5. Add Linux/IIO or optional DSP only after the baseline passes its physical acceptance tests.

A selftest PASS_WITH_OPEN_GATES means the files are internally consistent. It does not close any physical or timing-coverage gate.
