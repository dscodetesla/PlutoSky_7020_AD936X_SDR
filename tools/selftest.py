#!/usr/bin/env python3
"""Quick local artifact selftest. It does not run Vivado, program hardware or certify RF."""
import ast, hashlib, json, pathlib, struct, subprocess, sys, zipfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
def digest(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()
def main():
    (ROOT / ".work/reports/selftest/result.json").unlink(missing_ok=True)
    checks = []
    def check(name, condition):
        checks.append({"check": name, "pass": bool(condition)})
    lock = json.loads((ROOT / "project.lock.json").read_text())
    prepared = json.loads((ROOT / ".work/prepared.json").read_text())
    check("pinned_source", prepared["commit"] == lock["hdl"]["commit"])
    check("vivado_project_exists", (ROOT / ".work/build/zc702/zc702.xpr").is_file())
    for name in ("prepare_hdl.py", "audit_hardware.py", "build_vendor_firmware.py"):
        ast.parse((ROOT / "tools" / name).read_text())
        check("python_syntax:" + name, True)
    for name in ("run-vivado", "run-xsct", "build-firmware", "codex-project"):
        check("bash_syntax:" + name, subprocess.run(["bash", "-n", str(ROOT / "tools" / name)]).returncode == 0)
    result = json.loads((ROOT / ".work/reports/firmware-modern/result.json").read_text())
    elf = ROOT / result["elf"]
    check("firmware_hash", digest(elf) == result["sha256"])
    data = elf.read_bytes()[:52]
    check("arm_elf32_little_endian", data[:6] == b"\x7fELF\x01\x01" and struct.unpack_from("<H", data, 18)[0] == 40)
    check("entry_in_expected_ddr", struct.unpack_from("<I", data, 24)[0] == 0x100000)
    bsp = ROOT / ".work/firmware/bsp2025"
    check("bsp_library_hash", digest(bsp / "ps7_cortexa9_0/lib/libxil.a") == result["bsp_libxil_sha256"])
    check("bsp_input_xsa_hash", digest(bsp / "hardware.xsa") == result["hardware_xsa_sha256"])
    xsa = ROOT / ".work/reports/export-hardware/system_top.xsa"
    check("export_matches_bsp_input", digest(xsa) == result["hardware_xsa_sha256"])
    with zipfile.ZipFile(xsa) as z:
        check("export_xsa_crc", z.testzip() is None)
        check("hardware_only_export", "system.hwh" in z.namelist() and not any(n.endswith(".bit") for n in z.namelist()))
    fixes = json.loads((ROOT / ".work/reports/firmware-modern/applied-fixes.json").read_text())
    check("patched_source_hash", digest(ROOT / ".work/firmware/vendor/AD936X/src/main.c") == fixes["patched_main_sha256"])
    check("routed_checkpoint_exists", (ROOT / ".work/reports/hold-fix/routed.dcp").is_file())
    check("export_completion_marker", "HARDWARE_XSA_OK" in (ROOT / ".work/reports/export-hardware/vivado.log").read_text())
    output = {
        "status": "PASS_WITH_OPEN_GATES" if all(c["pass"] for c in checks) else "FAIL",
        "scope": "Local source/artifact consistency only; prior native timing evidence is not rerun",
        "checks": checks,
        "firmware": result,
        "readiness": "NOT_FOR_FLASH",
        "open_gates": ["Physical RF part/revision, CTRL_IN2 L17/R14 and VCCO", "External RX/TX IO timing", "Scoped timing exceptions, clock topology and CDC review", "Legacy IRQ callback type warnings", "FSBL/boot package and physical board/RF tests"]
    }
    target = ROOT / ".work/reports/selftest/result.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2) + "\n")
    print(output["status"], str(sum(c["pass"] for c in checks)) + "/" + str(len(checks)))
    return 0 if all(c["pass"] for c in checks) else 1
if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("SELFTEST_FAIL:", exc, file=sys.stderr)
        sys.exit(1)
