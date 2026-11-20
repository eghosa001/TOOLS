from pathlib import Path
import pytest
from quality_probe import probe_media,inspect

HERE=Path(__file__).resolve().parent


def test_observed_real_kandinsky_mp4():
    v=Path('/mnt/data/asmr_stagepilot/v3/foam_asmr_pilot_UNAPPROVED.mp4')
    if not v.exists():pytest.skip('Local Kaggle artifact not available in GitHub CI')
    meta=probe_media(v)
    assert meta['audio_codec'] is not None
    assert 4.8<meta['duration']<5.4
    assert meta['width']==480
    r=inspect(v,HERE/'foam_stage_plan.json')
    assert not r['publish_approved']
    assert r['target_compression_fraction']==.25
    assert 'FAIL_LITTLE_MEASURABLE_FOAM_SHRINKAGE' in r['flags']