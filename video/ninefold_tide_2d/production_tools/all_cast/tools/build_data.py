#!/usr/bin/env python3
"""Generate canonical engineering-only, private-art-free cast and set records.
Names, age and known heights from the Google Drive visual design Bible (31 October 2026).
"""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
# id, display name, age, height cm, silhouette, art direction key, current source status
CAST=[
('naya_venn','Naya Venn',16,164,'wiry/forward','low braided knot + two side braids; left brow scar; storm-blue/teal workwear','phase20_cutout_reference'),
('kito_vale','Kito Vale',12,145,'small/round/mobile','compact curls; ochre raincape, rolled sleeves; thin messenger rope ONLY','concept_reference'),
('iri_sol','Iri Sol',17,172,'tall/erect/controlled','short top braid; off-white cadet jacket; separate certified safety line','concept_reference'),
('tovan_rusk','Tovan Rusk',43,188,'broad/heavy','working foreman; stiff right ring finger; toolbag has weight','concept_reference'),
('serin_hal','Serin Hal',46,169,'narrow/contained','low coil with single right temple silver streak; archive keychain','concept_reference'),
('maela_venn','Maela Venn',41,166,'strong/working','dark tightly coiled short twists; single silver strand; engineer','concept_reference'),
('asha_renn','Asha Renn',19,171,'athletic/asymmetric','marine headcloth, jade sleeveless coat, medicine-roll pouch','concept_reference'),
('corven_thane','Corven Thane',56,181,'square/formal','silver hair and tidy beard; civic coat and brass route insignia','concept_reference'),
('esra_pell','Esra Pell',52,175,'slender/vertical','gray-black short hair, technical overcoat, clipboard','concept_reference'),
('jessa_vale','Jessa Vale',38,168,'sturdy/practical','tight dark curls; maroon dispatch waistcoat; whistle','concept_reference'),
('auntie_rima','Auntie Rima',62,157,'compact/broad','silver wrap, heavy cardigan and work apron','concept_reference'),
('mina_strake','Mina Strake',35,175,'lean/coastal','sea-green oilskin cape, salt-stained boots, water charts','concept_reference'),
('belen','Belen',34,176,'broad/industrial','patched vest, permanent reduced hand function after E106','concept_reference'),
('daro','Daro',22,None,'narrow/fast','indigo scarf, orange vest, re-sewn satchel, receipt book','concept_reference'),
('calen_oris','Calen Oris',39,179,'mobile/working','slate Warden uniform with thin copper piping; wrist rope-burn','concept_reference'),
('emmet','Emmet',47,168,'narrow/slightly stooped','ochre shirt, blue archive vest, ferry drawing pin','concept_reference'),
('elen','Elen',14,153,'slim/teen','cornrows with mustard cloth, tan tunic, brace/tender arm after E103','concept_reference'),
('captain_fara','Captain Fara',42,174,'broad/steady','grey-blue captain jacket; rope-work scar; heavy bow hawser','concept_reference'),
('mari','Mari',6,112,'small/young child','two short coiled puffs, sun-yellow vest, green socks, red shoes','concept_reference'),
('supervisor_ren','Supervisor Ren',None,None,'lean/unheroic','appearance PROPOSAL only; spectacles on cord, school supervisor','proposed_design_only'),
]
# These are *engineering staging slots*, not an assertion that the fifteen old sets are identified.
SET_STAGES=[
('SET01','North Dock fixed quay / berth'),('SET02','Switching bridge and operating machinery'),
('SET03','Mastmarket roofs and walkway'),('SET04','Bellward emergency brake tower'),
('SET05','Survey school / supervisor office'),('SET06','Saltglass archive'),
('SET07','Sound gallery fixed shaft and landing'),('SET08','Ferry deck and bow station'),
('SET09','Clinic launch / patient hold'),('SET10','Lighthouse optical relay'),
('SET11','Cableway / headland'),('SET12','Morrow Reach outer coast'),
('SET13','Relief docks / sea passage'),('SET14','Public assembly / signal square'),
('SET15','Pressure-seal gate / flood buffer'),
]
REQUIRED_VIEWS=['front','front_three_quarter','profile','rear_three_quarter','rear']
REQUIRED_PARTS=['pelvis','torso','head','upper_arm_left','forearm_left','hand_left','upper_arm_right','forearm_right','hand_right','thigh_left','shin_left','foot_left','thigh_right','shin_right','foot_right']
REQUIRED_EXPRESSIONS=['neutral','joy','fear','anger','grief','resolve','doubt','surprise']
REQUIRED_MOUTHS=['closed','rest','A','E','O','U','M_BP','FV','smile','shout']
REQUIRED_BG_LAYERS=['sky_distant','far_architecture','mid_structure','playable_ground','contact_shadows','foreground_occluders']
def data():
    people=[]
    for i,(id,name,age,cm,sil,notes,source) in enumerate(CAST,1):
        people.append({'number':i,'id':id,'name':name,'age':age,'height_cm':cm,'silhouette':sil,
        'canon_notes':notes,'source_status':source,'reference_design_approved':source!='proposed_design_only',
        'turnaround_approved':False,'rig_art_approved':False,'audio_performance_approved':False,
        'rig_method':'naya_source_kit' if id=='naya_venn' else 'engineering_cutout_template',
        'views_required':REQUIRED_VIEWS,'part_slots':REQUIRED_PARTS,'expression_slots':REQUIRED_EXPRESSIONS,
        'mouth_slots':REQUIRED_MOUTHS,
        'approval_rule':'Independent drawings, layered source, rights, engine motion and human director review required'})
    sets=[{'id':id,'staging_target':name,'asset_mapping_status':'not_matched_to_legacy_background_structure',
    'final_painted_set_approved':False,'layer_slots':REQUIRED_BG_LAYERS,'fixed_geography_requires_review':True}
    for id,name in SET_STAGES]
    return {'series':'The Ninefold Tide','spec_revision':'2026-10-31','artifact_status':'engineering_framework_only',
    'character_bible':'https://docs.google.com/document/d/1TnnN33aXBXqhjNeAPzdwZeduLPOzFajGCDYL8NwkSBY/edit',
    'art_index':'https://docs.google.com/document/d/1roYu1Frb2awFvwSI7mms2_llnag58qDVCmnUEfb5F24/edit',
    'story_bible':'https://docs.google.com/document/d/1tv4qvdlG6F7EV5EI822OdYgDVbNBwauqiKvNJ2_86Is/edit',
    'release_ready':False,'characters':people,'set_staging_slots':sets,
    'nonnegotiable':['No copied franchise artwork','No fake five-view rotations',
      'Three rescue ropes must remain separate','Eight public wards + concealed Morrow Reach',
      'Hero drawings must be originally approved; structural rig tests are not animation approval',
      'No video, no unlicensed audio, no auto-approval']}
if __name__=='__main__':
    out=ROOT/'godot/data/production_inventory.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data(),ensure_ascii=False,indent=2)+'\n')
    print('Wrote',out)