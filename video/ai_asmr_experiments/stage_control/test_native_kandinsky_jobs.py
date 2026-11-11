from pathlib import Path
import pytest
from native_kandinsky_jobs import gpu_check,make_jobs

HERE=Path(__file__).resolve().parent

def test_gpu_safety():
    with pytest.raises(RuntimeError,match='SM 7.5'):
        gpu_check(7,5)
    gpu_check(8,0)
    gpu_check(9,0)

def test_native_job_specs(tmp_path):
    frames=Path('/mnt/data/asmr_stagepilot/out')
    if not frames.exists():pytest.skip('local visual references unavailable')
    d=make_jobs(HERE/'foam_stage_plan.json',frames,tmp_path)
    assert len(d['first_last_segments'])==4
    assert '--last-image' in d['first_last_segments'][0]['command']
    assert '--image' in d['first_last_segments'][0]['command']
    assert '--video-file' in d['video_to_audio_command']
    assert d['kaggle_t4_native_support'] is False
    assert d['video_to_audio_preserves_input_frames'] is True
    assert (tmp_path/'native_kandinsky_jobs.json').exists()