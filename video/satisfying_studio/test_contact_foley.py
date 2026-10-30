import unittest
from production.contact_foley import measured_contact_schedule,attenuation_only_gain

class PhysicalFoleyTests(unittest.TestCase):
    def rows(self):
        phases={1:(.16,.53),20:(.12,.53),38:(.012,.53),
                52:(.003,.512),67:(-.008,.505),80:(-.012,.505),
                92:(.001,.517),108:(.030,.52),120:(.08,.53)}
        return [{"frame":f,"surface_gap_m":v[0],"gel_surface_z":v[1]}
                for f,v in phases.items()]

    def test_real_contact_makes_ordered_sound_cue_times(self):
        values=measured_contact_schedule(self.rows())
        self.assertEqual(values["first_touch"],38)
        self.assertEqual(values["peak_pressure"],80)
        self.assertEqual(values["release"],92)
        self.assertTrue(38<values["compression"]<80)
        self.assertTrue(values["manual_headphone_review_required"])

    def test_no_contact_is_silent_not_faked(self):
        rows=self.rows()
        for row in rows:row["surface_gap_m"]=.08
        with self.assertRaisesRegex(ValueError,"Not enough real touch"):
            measured_contact_schedule(rows)

    def test_impossible_intersection_blocks_audio(self):
        rows=self.rows()
        rows[5]["surface_gap_m"]=-.18
        with self.assertRaisesRegex(ValueError,"impossible collider penetration"):
            measured_contact_schedule(rows)

    def test_no_release_blocks_audio(self):
        rows=self.rows()
        rows[-1]["surface_gap_m"]=.004
        with self.assertRaisesRegex(ValueError,"does not audibly release"):
            measured_contact_schedule(rows)

    def test_no_deformation_blocks_audio(self):
        rows=self.rows()
        for row in rows:row["gel_surface_z"]=.53
        with self.assertRaisesRegex(ValueError,"did not visibly compress"):
            measured_contact_schedule(rows)

    def test_peak_normalizer_only_attenuates(self):
        self.assertEqual(attenuation_only_gain(.01),1.0)
        self.assertEqual(attenuation_only_gain(0),1.0)
        self.assertLess(attenuation_only_gain(.9),1.0)

    def test_reject_invalid_audio_peak(self):
        with self.assertRaises(ValueError):
            attenuation_only_gain(float("nan"))

if __name__=="__main__":
    unittest.main()
