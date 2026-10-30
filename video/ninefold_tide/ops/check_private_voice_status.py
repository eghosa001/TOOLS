"""Read-only private Kaggle status for the newly created Ninefold voice audition.
Reports status and whether WAV output files exist. Never fetches credentials, or deletes data.
"""
import csv, io, json, os, subprocess
SLUG="ninefold-tide-qwen3-voice-cast-auditions"
def run(*args):
    x=subprocess.run(["kaggle",*args],capture_output=True,text=True,timeout=80)
    if x.returncode: raise RuntimeError("Kaggle query failed, code="+str(x.returncode))
    return x.stdout

def main():
    result={"job":"Ninefold Tide voice audition", "notebook_found":False,
            "kaggle_status":None, "wav_files_visible":0, "audio_files_visible":0}
    data=run("kernels","list","--mine","--csv","--page-size","100")
    lines=[row for row in data.splitlines() if row.strip()]
    start=next((i for i,x in enumerate(lines) if x.lower().startswith("ref,")),0)
    records=list(csv.DictReader(io.StringIO("\n".join(lines[start:]))))
    target=next((r for r in records if r.get("ref","").endswith("/"+SLUG)),None)
    if not target:
        result["kaggle_status"]="NOT_SUBMITTED_OR_NOT_YET_VISIBLE"
        print(json.dumps(result,indent=2));return
    ref=target["ref"]
    result["notebook_found"]=True
    result["url"]="https://www.kaggle.com/code/"+ref
    result["kaggle_status"]=run("kernels","status",ref).strip()[-500:]
    try:
        files=run("kernels","files",ref,"--csv","--page-size","200")
        rows=list(csv.DictReader(io.StringIO(files)))
        result["files_visible"]=len(rows)
        result["wav_files_visible"]=sum(str(row.get("name","")).lower().endswith(".wav") for row in rows)
        result["archive_available"]=any("UNAPPROVED.zip" in str(row.get("name","")) for row in rows)
    except RuntimeError:
        result["archive_available"]=False
    try:
        logs=run("kernels","logs",ref)
        result["execution_log_tail"]=logs[-4500:]
    except RuntimeError:
        result["execution_log_tail"]="Kaggle execution log not yet available"
    print(json.dumps(result,indent=2))
if __name__=="__main__":
    main()
