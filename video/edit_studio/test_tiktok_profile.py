#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path
gate=Path(__file__).with_name("tiktok_profile.py")
spec=importlib.util.spec_from_file_location("tiktok_profile",gate)
policy=importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)

base=Path(__file__).with_name("test_release_gate.py")
spec2=importlib.util.spec_from_file_location("universal_test_manifest",base)
mtest=importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(mtest)

class TikTokPolicyTests(unittest.TestCase):
    def test_short_edit_can_be_posting_candidate(self):
        x=policy.evaluate(mtest.valid("anime","music_sync"),objective="publish",duration_sec=25)
        self.assertEqual(x["status"],"PLAN_CHECKS_ONLY")

    def test_short_edit_not_eligible_for_creator_rewards(self):
        x=policy.evaluate(mtest.valid("anime","music_sync"),objective="creator_rewards",duration_sec=25)
        self.assertIn("under TikTok Creator Rewards", " ".join(x["eligibility_blocks"]))

    def test_nigerian_account_not_creator_rewards_eligible(self):
        account={"country":"NG","creator_rewards_available_in_tiktok_studio":False,
                 "personal_account":True,"account_in_good_standing":True,"age_at_least_18":True,
                 "followers":25000,"views_last_30_days":500000}
        x=policy.evaluate(mtest.valid("gaming","analysis"),objective="creator_rewards",duration_sec=90,account=account)
        self.assertEqual(x["status"],"NOT_ELIGIBLE_OR_UNVERIFIED")

    def test_third_party_movie_risk_even_with_cc_by_license(self):
        account={"country":"GB","creator_rewards_available_in_tiktok_studio":True,
                 "personal_account":True,"account_in_good_standing":True,"age_at_least_18":True,
                 "followers":30000,"views_last_30_days":500000}
        x=policy.evaluate(mtest.valid("movie","character_study"),objective="creator_rewards",duration_sec=90,account=account)
        self.assertEqual(x["status"],"ORIGINALITY_REVIEW_RISK")

    def test_unlicensed_footage_cannot_auto_approve_posting(self):
        m=mtest.valid("tv","music_sync")
        m["media_sources"][0]["rights_status"]="unclear"
        x=policy.evaluate(m,objective="publish",duration_sec=35)
        self.assertEqual(x["status"],"REVIEW_REQUIRED_NO_AUTOMATIC_PUBLICATION")

    def test_eligible_account_still_not_guaranteed(self):
        m=mtest.valid("gaming","analysis")
        m["media_sources"][0]["rights_status"]="owned"
        account={"country":"GB","creator_rewards_available_in_tiktok_studio":True,
                 "personal_account":True,"account_in_good_standing":True,"age_at_least_18":True,
                 "followers":25000,"views_last_30_days":300000}
        x=policy.evaluate(m,objective="creator_rewards",duration_sec=73,account=account)
        self.assertEqual(x["status"],"POTENTIAL_ACCOUNT_VIDEO_MATCH_TIKTOK_DECIDES")
        self.assertFalse(x["monetization_guaranteed"])

if __name__=="__main__":
    unittest.main()
