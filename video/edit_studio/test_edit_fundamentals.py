import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from edit_fundamentals import validate_edit_identity,EditIdentityError

def valid():
    return {"schema_version":3,"media_sources":[{"file":"sources/independent.mp4",
     "media_role":"independent_original_source"}],
     "edit_identity":{
     "format":"character_edit",
     "single_creative_idea":"A lonely character mistakes strength for independence until an unexpected act of kindness changes her",
     "character_or_subject":"The unnamed central character",
     "audience_emotion":"Tension shifting into bittersweet recognition",
     "before_state":"She believes she is alone and invincible",
     "after_state":"She accepts vulnerability instead of the need to win",
     "why_change_matters":"The climax changes how her earlier confidence and isolation are understood",
     "recognition_motif":"Repeated hand motion turns aggression into an offered hand",
     "opening_frame_meaning":"Her expression makes us expect another confrontation and danger",
     "music_interpretation":"First low note isolates her and a later accent reveals the changed meaning",
     "specific_last_frame":"A close reaction is held for the final downbeat",
     "sources_and_references_separate":True,"music_rights_verified":False,"text_not_substituting_story":True,
     "creative_timing":[
      {"role":"hook","at_sec":0,"what_viewer_newly_feels_or_learns":"Her intense expression suggests an imminent confrontation",
        "sound_picture_sync":"Quiet source audio establishes the first question"},
      {"role":"anticipation","at_sec":4,"what_viewer_newly_feels_or_learns":"The earlier display of confidence starts to crumble",
        "sound_picture_sync":"Low percussion arrives under a stopped gesture"},
      {"role":"visual_flip","at_sec":8,"what_viewer_newly_feels_or_learns":"The apparent enemy becomes a source of unexpected sympathy",
        "sound_picture_sync":"The musical impact lands on the exact reveal frame"},
      {"role":"reaction","at_sec":15,"what_viewer_newly_feels_or_learns":"She recognizes the kindness and changes her expression",
        "sound_picture_sync":"The last note breathes under a held reaction"}]}}
class GateTests(unittest.TestCase):
    def test_valid_concept(self):
        self.assertEqual(validate_edit_identity(valid())["status"],"concept_gate_passed_not_quality_approval")
    def test_no_vague_trailer(self):
        m=valid();m["edit_identity"]["format"]="trailer"
        with self.assertRaises(EditIdentityError):validate_edit_identity(m)
    def test_no_recycled_references(self):
        m=valid();m["media_sources"][0]["file"]="(1080p)(2).mp4"
        with self.assertRaises(EditIdentityError):validate_edit_identity(m)
    def test_reaction_must_follow_visual_flip(self):
        m=valid();m["edit_identity"]["creative_timing"][2]["role"]="reaction"
        m["edit_identity"]["creative_timing"][3]["role"]="visual_flip"
        with self.assertRaises(EditIdentityError):validate_edit_identity(m)
    def test_no_fake_template_pass(self):
        m=valid();m["edit_identity"]["specific_last_frame"]=""
        with self.assertRaises(EditIdentityError):validate_edit_identity(m)
if __name__=="__main__":unittest.main()
