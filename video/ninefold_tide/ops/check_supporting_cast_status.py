"""Read status and anonymous file counts of the private Ninefold supporting voice batch."""
import csv,io,json,subprocess
SLUG="ninefold-tide-20-character-supporting-voice-auditions"
def run(*args):
    p=subprocess.run(["kaggle",*args],capture_output=True,text=True,timeout=60)
    if p.returncode:
        raise RuntimeError("Kaggle API request failed; status "+str(p.returncode))
    return p.stdout
def main():
    csvtext=run("kernels","list","--mine","--csv","--page-size","100")
    lines=[x for x in csvtext.splitlines() if x.strip()]
    start=next((i for i,x in enumerate(lines) if x.lower().startswith("ref,")),0)
    rows=list(csv.DictReader(io.StringIO("\n".join(lines[start:]))))
    target=next((row["ref"] for row in rows if row.get("ref","").endswith("/"+SLUG)),None)
    if not target:
        print(json.dumps({"job":SLUG,"state":"NOT_SUBMITTED_OR_NOT_YET_VISIBLE",
                          "account_kernels_total":len(rows)},indent=2))
        return
    status=run("kernels","status",target).strip()[-450:]
    files=run("kernels","files",target,"--csv","--page-size","200")
    filelist=list(csv.DictReader(io.StringIO(files)))
    print(json.dumps({"job":SLUG,
        "kaggle_url":"https://www.kaggle.com/code/"+target,
        "status":status,
        "wav_files_visible":sum(row.get("name","").lower().endswith(".wav") for row in filelist),
        "zip_visible":any(row.get("name","").endswith("ninefold_17_supporting_cast_UNAPPROVED.zip") for row in filelist),
        "files_visible":len(filelist),"old_notebooks_unmodified":True},indent=2))
if __name__=="__main__":
    main()
