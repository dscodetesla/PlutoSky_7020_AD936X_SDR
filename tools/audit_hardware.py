#!/usr/bin/env python3
"""Compare current source BD with the vendor XSA; this is not hardware approval."""
import argparse, hashlib, json, pathlib, xml.etree.ElementTree as ET, zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
def quantity(value):
    units={"K":1024,"M":1024**2,"G":1024**3}
    if value[-1] in units: return int(value[:-1],0)*units[value[-1]]
    return int(value,0)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-root",type=pathlib.Path,default=ROOT/".work/reference")
    p.add_argument("--bd",type=pathlib.Path,help="Override BD path, e.g. the migrated disposable design")
    p.add_argument("--vendor-xsa",type=pathlib.Path,default=ROOT/".work/inputs/system_top.xsa")
    p.add_argument("--output",type=pathlib.Path,default=ROOT/".work/reports/source_alignment.json")
    args=p.parse_args()
    bdpath=args.bd or args.source_root/"projects/fmcomms2/zc702/zc702.srcs/sources_1/bd/system/system.bd"
    bd=json.loads(bdpath.read_text())["design"]
    with zipfile.ZipFile(args.vendor_xsa) as z:
        if z.testzip() is not None: raise SystemExit("Vendor XSA member CRC failed")
        vendor=ET.fromstring(z.read("system.hwh"))
        sysdef=ET.fromstring(z.read("sysdef.xml"))
    ps=next(x for x in vendor.iter("MODULE") if x.get("MODTYPE")=="processing_system7")
    vp={x.get("NAME"):x.get("VALUE") for x in ps.iter("PARAMETER")}
    raw_sp={k:x["value"] for k,x in bd["components"]["sys_ps7"]["parameters"].items()}
    # Vivado 2025.2 may serialize a long string as whitespace-separated chunks.
    sp={k:(" ".join(x) if isinstance(x,list) and all(isinstance(y,str) for y in x) else x) for k,x in raw_sp.items()}
    required={"PCW_UIPARAM_DDR_PARTNO","PCW_UIPARAM_DDR_MEMORY_TYPE","PCW_DDR_RAM_HIGHADDR","PCW_DQ_WIDTH","PCW_USB0_RESET_IO","PCW_UART1_UART1_IO","PCW_ENET0_ENET0_IO","PCW_ENET0_GRP_MDIO_IO","PCW_MIO_0_IOTYPE","PCW_MIO_16_IOTYPE"}
    missing=sorted(required-(set(vp)&set(sp)))
    if missing: raise SystemExit("Critical PS7 parameters missing: "+str(missing))
    shared=sorted(set(vp)&set(sp))
    delta={k:{"vendor":vp[k],"source":sp[k]} for k in shared if vp[k]!=sp[k]}
    mem={(x.get("INSTANCE"),x.get("SLAVEBUSINTERFACE"),x.get("ADDRESSBLOCK")):x for x in vendor.iter("MEMRANGE")}
    checks=[]
    for master, m in bd["addressing"].items():
        for space, s in m["address_spaces"].items():
            for name, seg in s["segments"].items():
                key=tuple(seg["address_block"].strip("/").split("/"))
                item=mem.get(key)
                lo=int(seg["offset"],0); hi=lo+quantity(seg["range"])-1
                checks.append({"master":master,"space":space,"segment":name,"base":hex(lo),"high":hex(hi),
                    "match":item is not None and int(item.get("BASEVALUE"),0)==lo and int(item.get("HIGHVALUE"),0)==hi})
    core_checks={}
    modules={m.get("INSTANCE"):m for m in vendor.iter("MODULE")}
    for name, comp in bd["components"].items():
        if not comp["vlnv"].startswith("analog.com:"): continue
        if name not in modules:
            core_checks[name]={"missing_vendor_module":True}
            continue
        params={x.get("NAME"):x.get("VALUE") for x in modules[name].iter("PARAMETER")}
        source={k:x["value"] for k,x in comp.get("parameters",{}).items()}
        overlap=sorted(params.keys()&source.keys())
        core_checks[name]={"shared_parameters":len(overlap),"differences":{k:{"vendor":params[k],"source":source[k]} for k in overlap if params[k]!=source[k]}}
    part=sysdef.find(".//SYSTEMINFO").get("PART")
    result={"source_commit":json.loads((ROOT/"project.lock.json").read_text())["hdl"]["commit"],
        "vendor_xsa_sha256":hashlib.sha256(args.vendor_xsa.read_bytes()).hexdigest(),
        "source_bd_sha256":hashlib.sha256(bdpath.read_bytes()).hexdigest(),
        "vendor_part":part,"ps7_shared_parameters":len(shared),"ps7_differences":delta,
        "source_serialized_string_chunks":{k:x for k,x in raw_sp.items() if isinstance(x,list)},
        "source_components":sorted(bd["components"]),"address_checks":checks,"adi_core_checks":core_checks,
        "open_gates":["gpio_ctl[2]: source L17 vs schematic CTRL_IN2 R14","Physical board revision and fitted transceiver","VCCO and IOSTANDARD verification","Native implementation, timing and board validation"],
        "scope":"Compare explicitly stored source BD parameters and address ranges, not stale generated SDK exports"}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    print("SOURCE_ALIGNMENT",len(shared),"PS7 parameters;",len(delta),"differences;",sum(x["match"] for x in checks),"/",len(checks),"address ranges")
    expected=json.loads((ROOT/"project.lock.json").read_text())
    if part!=expected["part_from_vendor_xsa"] or delta or len(checks)!=5 or not all(x["match"] for x in checks) or any(x.get("missing_vendor_module") or x.get("differences") for x in core_checks.values()): raise SystemExit(1)
if __name__=="__main__": main()
