#!/usr/bin/env python3
"""Stage a pinned HDL reference and a disposable build on local storage."""
import argparse, json, pathlib, shutil, subprocess, xml.etree.ElementTree as ET
ROOT = pathlib.Path(__file__).resolve().parents[1]
def git(path, *args):
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--cache", type=pathlib.Path)
    args=parser.parse_args()
    lock=json.loads((ROOT/"project.lock.json").read_text())["hdl"]
    work=ROOT/".work"; work.mkdir(exist_ok=True)
    marker=work/"prepared.json"
    if marker.exists():
        existing=json.loads(marker.read_text())
        if existing["commit"]!=lock["commit"]: raise SystemExit("Existing reference has another revision; preserve it and use a new workspace.")
        if not (work/"build/zc702/zc702.xpr").is_file(): raise SystemExit("Prepared marker exists but build XPR is missing.")
        print("ALREADY_PREPARED",work/"build/zc702/zc702.xpr")
        return
    cache=args.cache
    if cache is None:
        cache=work/"upstream"
        if not cache.exists():
            subprocess.run(["git","clone","--filter=blob:none","--no-checkout","--depth","1",lock["repository"],str(cache)],check=True)
            subprocess.run(["git","-C",str(cache),"sparse-checkout","init","--cone"],check=True)
            subprocess.run(["git","-C",str(cache),"sparse-checkout","set",lock["subdirectory"]],check=True)
        subprocess.run(["git","-C",str(cache),"fetch","--depth","1","origin",lock["commit"]],check=True)
        subprocess.run(["git","-C",str(cache),"checkout","--detach",lock["commit"]],check=True)
    if git(cache,"rev-parse","HEAD")!=lock["commit"]: raise SystemExit("Cache revision differs from project.lock.json")
    if git(cache,"status","--porcelain","--",lock["subdirectory"]): raise SystemExit("Cached source has local changes")
    reference=work/"reference"; project=work/"build/zc702"
    if reference.exists() or project.exists(): raise SystemExit("Unmarked staging directories exist; refusing overwrite")
    shutil.copytree(cache/lock["subdirectory"],reference)
    shutil.copytree(reference/"projects/fmcomms2/zc702",project)
    # Drop generated outputs from the disposable copy; preserve the reference.
    for suffix in [".runs",".cache",".gen",".hw",".ip_user_files",".sim",".sdk"]:
        path=project/("zc702"+suffix)
        if path.exists(): shutil.rmtree(path)
    xpr=project/"zc702.xpr"
    tree=ET.parse(xpr);tree.getroot().set("Path",str(xpr))
    config=tree.find("Configuration")
    for item in list(config):
        if item.get("Name")=="IPRepoPath": config.remove(item)
    ET.SubElement(config,"Option",Name="IPRepoPath",Val=str(reference/"library"))
    tree.write(xpr,encoding="UTF-8",xml_declaration=True)
    marker.write_text(json.dumps({"commit":lock["commit"],"reference":str(reference),"project":str(xpr)},indent=2)+"\n")
    print("PREPARED",xpr)
if __name__=="__main__": main()
