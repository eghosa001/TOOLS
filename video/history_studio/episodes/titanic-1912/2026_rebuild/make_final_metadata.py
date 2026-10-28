#!/usr/bin/env python3
"""Package evidence-led Titanic publishing copy, exact chapter timecodes and credits.
Never invent public URLs or assert YouTube publication. Sources and captions are
linked to actual scene ID and original 1912 report.
"""
from pathlib import Path
import json,csv
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"publishing_ready_to_review";OUT.mkdir(exist_ok=True)
TIME=ROOT/"audio_aligned_editorial"/"TIMED_SHOTS_REVIEW.json"
PHOTO=ROOT/"archive_intake"/"ARCHIVE_ASSET_LEDGER.json"
REPORT=ROOT/"master_review_export"/"FILM_COMPLETION_AND_QA.json"
TITLES={
1:"The Last 160 Minutes",
2:"The Engineering and Its Limits",
3:"Passengers, Crew and the Maiden Voyage",
4:"Why Twenty Lifeboats Weren't Enough",
5:"Warnings From the Ice",
6:"The Iceberg Collision",
7:"Why Titanic Could Not Stay Afloat",
8:"Wireless Distress Calls and Nearby Ships",
9:"The Lifeboat Evacuation",
10:"Who Survived?",
11:"Titanic's Final Minutes",
12:"The Carpathia Rescue and the Aftermath",
13:"The Official Investigations",
14:"The 1985 Wreck Discovery",
15:"Modern Wreck Evidence and the Lessons"
}
def ts(s):
    n=int(round(s));return f"{n//3600:02d}:{n%3600//60:02d}:{n%60:02d}"
def main():
    cuts=json.loads(TIME.read_text())
    qa=json.loads(REPORT.read_text())
    images=json.loads(PHOTO.read_text())
    assert qa["chapters"]==15 and qa["directed_shots"]==302
    assert 5100<qa["rendered_seconds"]<5350
    chapters=[f"{ts(cuts['chapters'][str(i)]['start_seconds'])} {TITLES[i]}" for i in range(1,16)]
    assert chapters[0].startswith("00:00:00")
    rights=[s for s in images["images"] if s["file"]]
    with (OUT/"individual_archival_credits.csv").open("w",newline="",encoding="utf8") as fp:
        w=csv.DictWriter(fp,fieldnames=["asset_id","source_url","caption","rights_notice","author","source_file","state"])
        w.writeheader()
        for x in rights:
            w.writerow({"asset_id":x["asset_id"],"source_url":x["source_url"],
             "caption":x.get("metadata_caption","")[:300],"rights_notice":x.get("license_notice","")[:220],
             "author":x.get("author","")[:180],"source_file":x["file"],
             "state":"CANDIDATE PENDING INDEPENDENT COMMERCIAL RIGHTS AND VISUAL IDENTIFICATION APPROVAL"})
    chaptersblock="\n".join(chapters)
    credits="\n".join(f"- {x['asset_id']}: {x['source_url']}" for x in rights)
    text=f"""# TITANIC — THE FINAL NIGHT, THE WARNINGS, AND WHAT THE WRECK REVEALS

Channel: Facts Uncovered: Stories & Evidence
Video status: EDITORIAL REVIEW MASTER — do not publish until full watching/listening, historical attribution, subtitles and visuals pass.

## Main YouTube title
Titanic: The Final Night, the Warnings, and What the Wreck Reveals

## Description
At 11:40 p.m. on 14 April 1912, RMS Titanic struck an iceberg in the North Atlantic. Roughly two hours and forty minutes later, the ocean had swallowed the ship.

What happened inside those final hours? Why were so few lifeboat places available, how did the wireless distress calls unfold, and what can the wreck tell us that testimony alone cannot?

In this evidence-led documentary, Facts Uncovered: Stories & Evidence follows Titanic from the Belfast shipyard through the maiden voyage, the ice warnings, the collision, the flooding, the evacuation and Carpathia's rescue. We examine the original American and British investigations and modern underwater studies while separating established facts from disputed interpretations.

Every illustrative diagram and reconstruction is original and must be distinguishable from genuine archival material. This film uses authentic historical records and source-identified archival photographs; publication rights require item-specific final checking.

Chapters:
{chaptersblock}

Historical starting sources:
British Wreck Commissioner's Inquiry (1912): https://www.titanicinquiry.org/BOTInq/BOTReport/botRep01.php
British report, boats: https://www.titanicinquiry.org/BOTInq/BOTReport/BOTRepBoats.php
U.S. Senate investigation: https://www.senate.gov/about/powers-procedures/investigations/titanic.htm
Woods Hole 1985 wreck discovery: https://www.whoi.edu/ocean-learning-hub/ocean-topics/ocean-human-lives/underwater-archaeology/rms-titanic/1985-discovery-of-rms-titanic/
RMS Titanic, Inc. expedition records: https://rmstitanicinc.com/titanic-expeditions/
NOAA records: https://www.noaa.gov/office-of-general-counsel/gc-international-section/rms-titanic-documents-and-references

Archival image attributions (individual rights must be confirmed against source metadata):
{credits}

Sound: Original narrated Kokoro voice and separately synthesized atmospheric score created for this production. No third-party commercial music used.

#Titanic #RMSTitanic #HistoryDocumentary

## YouTube tags
RMS Titanic, Titanic documentary, Titanic sinking, Titanic last night, Titanic final hours, Titanic lifeboats, Titanic iceberg, Titanic passengers, Titanic survivors, Titanic 1912, Titanic wreck discovery, Titanic investigation, Titanic 2024 expedition, Titanic history, White Star Line, Carpathia

## Short 1
Title: Why Titanic's 20 Lifeboats Could Never Save Everyone
Description: Titanic had room in its 20 lifeboats for only 1,178 people, according to the British inquiry, against a reported 2,201 aboard. Why were the arrangements inadequate? We follow the actual evidence and the evacuation. Watch the full Titanic documentary on Facts Uncovered: Stories & Evidence. [LINK AFTER MAIN DOCUMENTARY PUBLISHED]
Tags: #Titanic #HistoryShorts #RMSTitanic

## Short 2
Title: A Piece of Titanic's Wreck Fell Away — The 2024 Discovery
Description: Investigators documented the loss of a 15-foot section of Titanic's port-side bow railing during the 2024 expedition. The same expedition rediscovered the Diana of Versailles statuette. Explore the evidence in our full documentary. [LINK AFTER MAIN DOCUMENTARY PUBLISHED]
Tags: #Titanic #TitanicWreck #HistoryShorts

## YouTube settings
- Channel identity: verify Facts Uncovered: Stories & Evidence and its connected channel ID before upload.
- Audience: Not made for kids unless the creator's actual intended audience differs.
- Disclosure: Clearly identify any realistic synthetic reconstructions when YouTube requires it.
- Shorts: add the full-video link only after public main film publication.
- Do not schedule or duplicate upload. No claimed public URL yet.
- Do not publish this review candidate without continuous audiovisual review and historical-media licence signoff.
"""
    (OUT/"youtube_metadata_and_chapters_REVIEW.md").write_text(text,encoding="utf8")
    (OUT/"CHAPTER_TIMESTAMPS.txt").write_text(chaptersblock+"\n",encoding="utf8")
    (OUT/"PUBLISHING_GATE.json").write_text(json.dumps({"master_file":qa["filename"],
       "runtime_seconds":qa["rendered_seconds"],"chapters":15,
       "source_photo_count":len(rights),"archival_licence_final_review":False,
       "continuous_human_playback_review":False,"youtube_uploaded":False,
       "ready_for_public_upload":False},indent=2))
    print("TITANIC_PUBLISHING_MATERIALS_GENERATED",len(chapters),"chapter timestamps",len(rights),"archival citations",flush=True)
if __name__=="__main__":main()
