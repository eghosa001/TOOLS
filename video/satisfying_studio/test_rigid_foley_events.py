import unittest
from production.rigid_foley_events import first_impact_events,RELEASES

class RigidFoleyTests(unittest.TestCase):
    def positions(self):
        rows=[]
        for frame in range(1,121):
            # Designed unit fixture: every marble moves from z1.2 through the
            # ceramic-bowl threshold after its distinct release frame.
            points=[]
            for i,rel in enumerate(RELEASES):
                z=max(.34,1.2-max(0,frame-rel)*.13)
                points.append([.02*i,0.0,z])
            rows.append({"frame":frame,"marble_centers_xyz":points})
        return rows

    def test_detects_seven_nonidentical_real_frame_events(self):
        events=first_impact_events(self.positions())
        self.assertEqual(len(events),7)
        self.assertEqual(len({v["impact_frame"] for v in events}),7)
        self.assertLess(events[0]["impact_frame"],events[1]["impact_frame"])
        self.assertTrue(all(v["approx_inbound_velocity_m_s"]>0 for v in events))

    def test_no_impact_never_receives_fake_sound(self):
        rows=self.positions()
        for f in rows:
            f["marble_centers_xyz"][3][2]=1.2
        with self.assertRaisesRegex(ValueError,"never reaches"):
            first_impact_events(rows)

    def test_incomplete_physics_sequence_fails(self):
        with self.assertRaisesRegex(ValueError,"120 consecutive"):
            first_impact_events(self.positions()[:20])

    def test_invalid_physics_geometry_fails(self):
        rows=self.positions()
        rows[38]["marble_centers_xyz"][1][2]=float("nan")
        with self.assertRaisesRegex(ValueError,"Invalid physical"):
            first_impact_events(rows)

if __name__=="__main__":
    unittest.main()
