# Local SDR development
This branch supplies reusable local development scripts. It contains no host inventory or private execution reports.

## Setup
Requirements: Python with venv, Git, a native Vivado installation, and Codex CLI signed in using the user's existing account.
The selected HDL source revision and FPGA part are in project.lock.json. This profile uses Vivado 2025.2.

```bash
python3 -m venv .venv
.venv/bin/python tools/prepare_hdl.py
tools/codex-project
```

An optional --cache argument to prepare_hdl.py can reuse an existing clean checkout at the pinned revision. The script refuses to overwrite unknown staging directories.
Codex uses a project configuration layer and a workspace sandbox; the Python venv supplies the audit environment. This is not an operating-system VM.
Project .codex/config.toml applies to trusted projects. The launcher also explicitly selects workspace-write/on-request; it retains existing model and authentication settings.

## Native checks
Provide the intended vendor XSA at .work/inputs/system_top.xsa.

```bash
.venv/bin/python tools/audit_hardware.py
tools/run-vivado smoke
tools/run-vivado validate
tools/run-vivado synth
tools/run-vivado implement
tools/run-vivado signoff
```

Run stages sequentially and inspect failures. Validation upgrades locked native IP in the disposable build copy.
For a routed design with a diagnosed hold failure, tools/run-vivado hold-fix performs a targeted post-route physical optimization and writes a separate checkpoint plus reports.
Default signoff examines the original implementation run. The hold-fix stage writes its own timing coverage reports for its separate artifact.
Positive setup/hold slack does not establish complete external IO timing coverage or physical hardware readiness. Review every check_timing, DRC and board-specific gate.
No board programming or firmware deployment is performed.

Vivado discovery first uses PATH, then common local/removable AMDDesignTools installation patterns. No account-wide library settings are changed.
For an existing standalone workspace, tools/run-xsct can use genuine ABI-5 ncurses/tinfo libraries bundled with the AMD host GNU toolchain. It verifies SONAME and sets library paths only for the XSCT child process. XSCT is deprecated; native firmware build compatibility must be checked independently.

## ADI source roles
- https://github.com/analogdevicesinc/linux : Linux/IIO drivers and device-tree integration.
- https://github.com/analogdevicesinc/no-OS/tree/main/projects/ad9361 : standalone AD936x control and bring-up.
- https://analogdevicesinc.github.io/hdl/ : FPGA IP, interfaces, Tcl build and porting documentation.

Linux and no-OS are alternative control/runtime paths. Board pinout, DDR/MIO configuration and IO voltages must be verified for the intended board.
Generated sources, tool environments and run reports stay under ignored local directories.
