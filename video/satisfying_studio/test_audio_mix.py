"""Actually exercise the edit-ready ASMR audio mixer with two original test clicks."""
from __future__ import annotations
import hashlib,json,math,shutil,struct,subprocess,tempfile,unittest,wave
from pathlib import Path
import audio_mix

class ASMRMixerTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg and FFprobe are required on the production runner")
    def test_frame_aligned_real_pcm_mix(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            clips=[]
            for j in range(2):
                path=root/f"click{j}.wav"
                sr=48000
                with wave.open(str(path),"wb") as wav:
                    wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(sr)
                    data=bytearray()
                    for i in range(int(.13*sr)):
                        t=i/sr
                        amp=.35*math.sin(2*math.pi*(650+j*200)*t)*math.exp(-35*t)
                        data.extend(struct.pack("<h",int(amp*32767)))
                    wav.writeframes(data)
                clips.append(path)
            cues=[]
            for i,path in enumerate(clips):
                cues.append({"file":path.name,"source_url":"https://example.org/recordings/original",
                             "license":"original",
                             "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                             "frame":12+i*24,"gain_db":-8,"max_length_seconds":.13})
            manifest=root/"cues.json"
            manifest.write_text(json.dumps({"fps":24,"duration_seconds":3,"cues":cues}))
            output=root/"mix.wav"
            audio_mix.mix(manifest,output)
            self.assertGreater(output.stat().st_size,300000)
            result=subprocess.run(["ffprobe","-v","error","-of","json",
                       "-show_entries","format=duration:stream=sample_rate,channels,codec_name",str(output)],
                       capture_output=True,text=True,check=True)
            data=json.loads(result.stdout)
            stream=data["streams"][0]
            self.assertEqual(stream["sample_rate"],"48000")
            self.assertEqual(stream["channels"],2)
            self.assertEqual(stream["codec_name"],"pcm_s24le")
            self.assertAlmostEqual(float(data["format"]["duration"]),3,delta=.05)
            cues[0]["sha256"]="0"*64
            manifest.write_text(json.dumps({"fps":24,"duration_seconds":3,"cues":cues}))
            with self.assertRaises(ValueError):audio_mix.mix(manifest,root/"invalid.wav")
            self.assertFalse((root/"invalid.wav").exists())

if __name__=="__main__":unittest.main()
