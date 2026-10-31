import json
from pathlib import Path
import pytest
import numpy as np
from stage_controller import parse_timeline,get_state,render_all,render

DIR=Path(__file__).resolve().parent


def test_stages_validate_and_sample():
    tl=parse_timeline(DIR/'foam_stage_plan.json')
    assert [s.name for s in tl.stages]==['initial','contact','compress_10','compress_25','hold']
    assert get_state(tl,0)['compression']==0.0
    assert get_state(tl,1)['contact'] is True
    assert get_state(tl,2.1)['compression']==pytest.approx(.1)
    assert get_state(tl,4)['compression']==pytest.approx(.25)
    assert get_state(tl,5)['compression']==pytest.approx(.25)
    assert get_state(tl,5)['contact_fraction']==1


def test_no_precontact_compression(tmp_path):
    plan=json.loads((DIR/'foam_stage_plan.json').read_text())
    plan['stages'][1]['compression']=.2
    plan['stages'][1]['press_contact']=False
    p=tmp_path/'bad.json';p.write_text(json.dumps(plan))
    with pytest.raises(ValueError,match='before tool contact'):
        parse_timeline(p)


def test_order_and_bounds(tmp_path):
    plan=json.loads((DIR/'foam_stage_plan.json').read_text())
    plan['stages'][2]['time_s']=1
    p=tmp_path/'bad.json';p.write_text(json.dumps(plan))
    with pytest.raises(ValueError,match='strictly ascending'):
        parse_timeline(p)
    plan['stages'][2]['time_s']=2.1
    plan['stages'][2]['compression']=.7
    p.write_text(json.dumps(plan))
    with pytest.raises(ValueError,match='outside'):
        parse_timeline(p)


def test_tool_contact_and_foam_geometry():
    tl=parse_timeline(DIR/'foam_stage_plan.json')
    src=np.full((864,480,3),36,dtype=np.uint8)
    pre,pre_m=render(src,get_state(tl,.0))
    cont,cont_m=render(src,get_state(tl,1.0))
    mid,mid_m=render(src,get_state(tl,2.1))
    deep,deep_m=render(src,get_state(tl,4.0))
    hold,hold_m=render(src,get_state(tl,5.0))
    assert pre.shape==cont.shape==mid.shape==deep.shape==hold.shape==(864,480,3)
    assert pre_m['gap_px']>0
    assert cont_m['gap_px']==mid_m['gap_px']==deep_m['gap_px']==hold_m['gap_px']==0
    assert pre_m['foam_height_px']>mid_m['foam_height_px']>deep_m['foam_height_px']
    assert abs(deep_m['foam_height_px']-hold_m['foam_height_px'])<1e-6
    assert pre_m['press_width_px']==cont_m['press_width_px']==deep_m['press_width_px']
    assert deep_m['camera_scale']==pre_m['camera_scale']==1
    assert deep_m['object_identity_sha256']==pre_m['object_identity_sha256']


def test_render_real_reference(tmp_path):
    ref=Path('/mnt/data/asmr_stagepilot/v3/foam_reference.png')
    if not ref.exists():pytest.skip('Reference only present in local Kaggle artifacts; repo uses existing AVIF')
    result=render_all(DIR/'foam_stage_plan.json',ref,tmp_path,preview=False)
    assert len(result['stages'])==5
    assert result['audio_cues']['contact_seconds']==1
    assert all((tmp_path/f'{i:02d}_{s}.png').exists() for i,s in enumerate(['initial','contact','compress_10','compress_25','hold']))
    assert (tmp_path/'stage_contact_sheet.jpg').exists()