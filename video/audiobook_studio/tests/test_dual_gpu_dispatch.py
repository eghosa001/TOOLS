"""CPU-only regression tests for real dual-T4 slot routing and durable queue."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

from video.audiobook_studio.manhua_pipeline import dual_gpu_dispatch as dispatch
from video.audiobook_studio.manhua_pipeline import kaggle_runner
from video.audiobook_studio.manhua_pipeline.core import VOICE


def story(number=1, name="approved-episode"):
    return dispatch.task_record(
        story_id=name, episode=number,
        private_dataset="private-owner/approved-private-source",
        source_sha256=f"{number:064x}", quality="quality", phase="assets")


class DualT4Tests(unittest.TestCase):
    def test_queue_is_stable_order_and_no_duplicate_or_revised_episode(self):
        q={"schema":dispatch.SCHEMA,"tasks":[]}
        q, added=dispatch.enqueue(q,story())
        self.assertTrue(added)
        q, added=dispatch.enqueue(q,story())
        self.assertFalse(added)
        self.assertEqual(len(q["tasks"]),1)
        revised=story()
        revised["source_sha256"]="a"*64
        with self.assertRaises(ValueError):
            dispatch.enqueue(q,revised)
        _, added=dispatch.enqueue(q,story(number=2))
        self.assertTrue(added)

    def test_rejects_unsafe_dataset_refs_unapproved_profile_and_phases(self):
        with self.assertRaises(ValueError):
            dispatch.task_record(story_id="good-story",episode=1,
                private_dataset="--invalid",source_sha256="b"*64)
        bad=story()
        bad["voice_profile"]="unapproved-female-narrator"
        with self.assertRaises(ValueError):
            dispatch.validate_task(bad)
        with self.assertRaises(ValueError):
            dispatch.task_record(story_id="good-story",episode=1,
                private_dataset="owner/dataset",source_sha256="b"*64,
                phase="publish")

    def test_physical_gpu_one_selected_without_touching_gpu_zero(self):
        fake=mock.MagicMock()
        fake.cuda.is_available.return_value=True
        fake.cuda.device_count.return_value=2
        with mock.patch.dict("sys.modules",{"torch":fake}):
            with mock.patch.dict("os.environ",{"MANHUA_GPU_SLOT":"1"}):
                self.assertEqual(kaggle_runner.selected_gpu(),(1,"cuda:1"))
            fake.cuda.set_device.assert_called_once_with(1)
            with mock.patch.dict("os.environ",{"MANHUA_GPU_SLOT":"2"}):
                with self.assertRaises(RuntimeError):
                    kaggle_runner.selected_gpu()
            fake.cuda.device_count.return_value=1
            with mock.patch.dict("os.environ",{"MANHUA_GPU_SLOT":"1"}):
                with self.assertRaises(RuntimeError):
                    kaggle_runner.selected_gpu()

    def test_one_process_each_gpu_and_separate_episode_outputs(self):
        with tempfile.TemporaryDirectory() as root:
            fake_proc=mock.MagicMock()
            with mock.patch.object(dispatch,"WORK",Path(root)), \
                 mock.patch.object(dispatch,"pull_input"), \
                 mock.patch.object(dispatch,"command") as cmd, \
                 mock.patch.object(dispatch.subprocess,"Popen",return_value=fake_proc) as pop:
                cmd.return_value.returncode=1
                first=dispatch.start_worker(story(name="first-episode"),0,"private-owner")
                env0=pop.call_args.kwargs["env"]
                second=dispatch.start_worker(story(name="second-episode"),1,"private-owner")
                env1=pop.call_args.kwargs["env"]
                self.assertEqual(env0["MANHUA_GPU_SLOT"],"0")
                self.assertEqual(env1["MANHUA_GPU_SLOT"],"1")
                self.assertNotEqual(env0["MANHUA_WORK_DIR"],env1["MANHUA_WORK_DIR"])
                self.assertNotEqual(first["progress_ref"],second["progress_ref"])

    def test_controller_schedules_third_story_after_first_gpu_releases(self):
        q={"schema":dispatch.SCHEMA,
           "tasks":[story(number=i,name=f"story-{i}") for i in (1,2,3)]}
        started=[]
        class Finished:
            def poll(self):
                return 0
        def worker(task,slot,owner):
            started.append((task["story_id"],slot))
            return {"task":task,"slot":slot,"process":Finished(),
                    "work":Path("/tmp/not-actually-created"),
                    "progress_ref":"owner/checkpoint","tries":1}
        gpu=mock.MagicMock()
        gpu.cuda.is_available.return_value=True
        gpu.cuda.device_count.return_value=2
        def get(ref,filename):
            return q if filename=="queue.json" else None
        with mock.patch.dict("sys.modules",{"torch":gpu}), \
             mock.patch.object(dispatch,"kaggle_secret"), \
             mock.patch.object(dispatch,"get_dataset_json",side_effect=get), \
             mock.patch.object(dispatch,"persist_dataset"), \
             mock.patch.object(dispatch,"save_private_progress"), \
             mock.patch.object(dispatch,"start_worker",side_effect=worker), \
             mock.patch.object(dispatch.time,"sleep"):
            report=dispatch.supervise("owner/queue","owner/results","owner",
                                      poll_seconds=10,idle_polls=1,retry_limit=0)
        self.assertEqual(len(started),3)
        self.assertEqual(started[0][1],0)
        self.assertEqual(started[1][1],1)
        self.assertEqual(report["completed"],3)
        self.assertEqual(len(set(x[0] for x in started)),3)

    def test_current_legacy_runner_stays_untouched(self):
        import inspect
        code=inspect.getsource(dispatch.supervise)
        self.assertNotIn("kernels push",code)
        self.assertNotIn("kernels delete",code)
        self.assertNotIn("ApiCancelKernel",code)
        self.assertTrue(dispatch.SCHEMA.startswith("manhua-dual-t4"))


if __name__ == "__main__":
    unittest.main()
