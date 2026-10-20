#!/usr/bin/env python3
"""Extract selected vendor sources locally and build a BSP-assisted ARM ELF. No device IO."""
import argparse, ctypes as C, ctypes.util, hashlib, json, pathlib, subprocess, os
ROOT=pathlib.Path(__file__).resolve().parents[1]
def sha(p): return hashlib.file_digest(open(p,"rb"),"sha256").hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--archive",type=pathlib.Path,required=True);ap.add_argument("--toolchain",type=pathlib.Path,required=True);ap.add_argument("--bsp-root",type=pathlib.Path,help="Regenerated processor BSP containing include/ and lib/");a=ap.parse_args()
 lock=json.loads((ROOT/"project.lock.json").read_text())
 if sha(a.archive)!=lock["vendor_rar"]["sha256"]:raise SystemExit("Vendor archive hash mismatch")
 dest=ROOT/".work/firmware/vendor";out=ROOT/".work/firmware/build";report=ROOT/".work/reports/firmware"
 if a.bsp_root:
  out=ROOT/".work/firmware/build-modern";report=ROOT/".work/reports/firmware-modern"
 for p in (dest,out,report):p.mkdir(parents=True,exist_ok=True)
 (report/"result.json").unlink(missing_ok=True)
 lib=C.CDLL(ctypes.util.find_library("archive"))
 sig={"archive_read_new":(C.c_void_p,[]),"archive_read_support_filter_all":(C.c_int,[C.c_void_p]),"archive_read_support_format_all":(C.c_int,[C.c_void_p]),"archive_read_open_filename":(C.c_int,[C.c_void_p,C.c_char_p,C.c_size_t]),"archive_read_next_header":(C.c_int,[C.c_void_p,C.POINTER(C.c_void_p)]),"archive_entry_pathname":(C.c_char_p,[C.c_void_p]),"archive_read_data":(C.c_ssize_t,[C.c_void_p,C.c_void_p,C.c_size_t]),"archive_read_data_skip":(C.c_int,[C.c_void_p]),"archive_read_free":(C.c_int,[C.c_void_p])}
 for n,(ret,args) in sig.items():getattr(lib,n).restype=ret;getattr(lib,n).argtypes=args
 arc=lib.archive_read_new();lib.archive_read_support_filter_all(arc);lib.archive_read_support_format_all(arc)
 if lib.archive_read_open_filename(arc,os.fsencode(a.archive),10240)!=0:raise RuntimeError("Archive open failed")
 records=[];entry=C.c_void_p();buf=C.create_string_buffer(65536)
 try:
  while True:
   rc=lib.archive_read_next_header(arc,C.byref(entry))
   if rc==1:break
   if rc<0:raise RuntimeError("Archive header error")
   name=lib.archive_entry_pathname(entry).decode();p=pathlib.PurePosixPath(name)
   source=name.startswith("AD936X/") and not any(x in p.parts for x in ("Debug","Release")) and p.suffix in (".c",".h",".ld",".spec")
   bsp=name.startswith("platform/export/platform/sw/platform/standalone_domain/") and ("/bspinclude/include/" in name or "/bsplib/lib/" in name) and not name.endswith("/")
   if source or bsp:
    if p.is_absolute() or ".." in p.parts:raise RuntimeError("Unsafe archive path")
    target=dest/pathlib.Path(*p.parts);target.parent.mkdir(parents=True,exist_ok=True)
    with target.open("wb") as f:
     while True:
      n=lib.archive_read_data(arc,buf,len(buf))
      if n==0:break
      if n<0:raise RuntimeError("Archive data error")
      f.write(buf.raw[:n])
    records.append({"path":name,"sha256":sha(target)})
   else:lib.archive_read_data_skip(arc)
 finally:lib.archive_read_free(arc)
 (report/"extracted.json").write_text(json.dumps(records,indent=2)+"\n")
 app=dest/"AD936X";bsp=dest/"platform/export/platform/sw/platform/standalone_domain"
 main_c=app/"src/main.c"
 original=main_c.read_text()
 needle="\tad9361_init(&ad9361_phy, &default_init_param);"
 replacement = r'''	status = ad9361_init(&ad9361_phy, &default_init_param);
	if (status < 0 || !ad9361_phy) {
		printf("ad9361_init failed: %"PRIi32"\n", status);
		return status < 0 ? status : -1;
	}'''
 if original.count(needle)!=1:raise RuntimeError("Expected one primary AD936x init call")
 main_c.write_text(original.replace(needle,replacement))
 (report/"applied-fixes.json").write_text(json.dumps({"fix":"Check init return and descriptor before FIR calls","original_main_sha256":hashlib.sha256(original.encode()).hexdigest(),"patched_main_sha256":sha(main_c)},indent=2)+"\n")
 addresses={"XPAR_AXI_AD9361_BASEADDR":0x79020000,"XPAR_AXI_AD9361_ADC_DMA_BASEADDR":0x7c400000,"XPAR_AXI_AD9361_DAC_DMA_BASEADDR":0x7c420000}
 import re
 bsp_inc=a.bsp_root/"include" if a.bsp_root else bsp/"bspinclude/include"
 params=(bsp_inc/"xparameters.h").read_text()
 for key,value in addresses.items():
  match=re.search(r"#define\s+"+key+r"\s+(0x[0-9a-fA-F]+)",params)
  if not match or int(match[1],16)!=value:raise RuntimeError("BSP address mismatch: "+key)
 gcc=a.toolchain/"arm-none-eabi-gcc";readelf=a.toolchain/"arm-none-eabi-readelf";size=a.toolchain/"arm-none-eabi-size"
 flags=["-mcpu=cortex-a9","-mfpu=vfpv3","-mfloat-abi=hard","-O0","-g3","-ffunction-sections","-fdata-sections"]
 bsp_inc=a.bsp_root/"include" if a.bsp_root else bsp/"bspinclude/include"
 bsp_lib=a.bsp_root/"lib" if a.bsp_root else bsp/"bsplib/lib"
 includes=[app/x for x in ("ad9361","api","AXI_Core","iio","include","src","util","xilinx")]+[bsp_inc]
 inc=[s for p in includes for s in ("-I",str(p))]
 commands=[];objects=[]
 with (report/"build.log").open("w") as log:
  def run(cmd):
   commands.append([str(x) for x in cmd]);log.write("\nCOMMAND "+repr(commands[-1])+"\n");log.flush()
   subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
  for src in sorted(dest/r["path"] for r in records if r["path"].startswith("AD936X/") and r["path"].endswith(".c")):
   obj=out/(str(src.relative_to(app)).replace("/","_")+".o")
   run([str(gcc),*flags,*inc,"-c",str(src),"-o",str(obj)]);objects.append(str(obj))
  elf=out/"plutosky-vendor-app.elf"
  run([str(gcc),*flags,"-specs="+str(app/"src/Xilinx.spec"),"-Wl,--gc-sections","-Wl,-Map="+str(out/"firmware.map"),"-T",str(app/"src/lscript.ld"),"-L"+str(bsp_lib),*objects,"-Wl,--start-group","-lxil",*(["-llwip4"] if not a.bsp_root else []),"-lgcc","-lc","-Wl,--end-group","-o",str(elf)])
  run([str(readelf),"-h",str(elf)]);run([str(size),str(elf)])
 (report/"commands.json").write_text(json.dumps(commands,indent=2)+"\n")
 result={"status":"PASS","scope":("Application + regenerated BSP from repaired hardware XSA" if a.bsp_root else "Application rebuilt from vendor C sources; linked with prebuilt vendor BSP, not regenerated BSP"),"readiness":"NOT_FOR_FLASH","elf":str(elf.relative_to(ROOT)),"sha256":sha(elf),"source_archive_sha256":sha(a.archive),"source_count":len(objects),"compiler":subprocess.check_output([str(gcc),"--version"],text=True).splitlines()[0]}
 result["bsp_libxil_sha256"]=sha(bsp_lib/"libxil.a")
 result["warning_count"]=(report/"build.log").read_text().count("warning:")
 result["init_guard"]="return before FIR on init error or null descriptor"
 if a.bsp_root:result["hardware_xsa_sha256"]=sha(a.bsp_root.parent/"hardware.xsa")
 (report/"result.json").write_text(json.dumps(result,indent=2)+"\n")
 print(json.dumps(result));print("FIRMWARE_ELF_OK")
if __name__=="__main__":main()
