import importlib.util
from pathlib import Path
import unittest

CORE = Path(__file__).parents[1] / "addon" / "globalPlugins" / "focusBreakTimerCore.py"
spec = importlib.util.spec_from_file_location("focusBreakTimerCore", CORE)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
import sys
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

FocusBreakEngine = mod.FocusBreakEngine
Phase = mod.Phase


class FocusBreakEngineTests(unittest.TestCase):
    def test_start_focus_then_break_then_next_focus(self):
        e = FocusBreakEngine(10, 5, 0)
        self.assertEqual([x.kind for x in e.start(100.0)], ["focus_started"])
        self.assertEqual(e.phase, Phase.FOCUS)
        self.assertEqual(e.remaining_seconds(105.0), 5)
        events = e.tick(110.0)
        self.assertEqual([x.kind for x in events], ["break_started"])
        self.assertEqual(e.phase, Phase.BREAK)
        events = e.tick(115.0)
        self.assertEqual([x.kind for x in events], ["break_finished", "focus_started"])
        self.assertEqual(e.cycle, 2)
        self.assertEqual(e.phase, Phase.FOCUS)

    def test_finite_cycles_complete_after_last_break(self):
        e = FocusBreakEngine(10, 5, 2)
        e.start(0.0)
        self.assertEqual([x.kind for x in e.tick(30.0)], [
            "break_started", "break_finished", "focus_started", "break_started", "break_finished", "completed"
        ])
        self.assertEqual(e.phase, Phase.STOPPED)

    def test_pause_and_resume_preserve_remaining(self):
        e = FocusBreakEngine(10, 5)
        e.start(0.0)
        e.pause(4.0)
        self.assertEqual(e.phase, Phase.PAUSED)
        self.assertEqual(e.remaining_seconds(100.0), 6)
        e.resume(100.0)
        self.assertEqual(e.phase, Phase.FOCUS)
        self.assertEqual(e.remaining_seconds(102.0), 4)

    def test_repetition_target_can_change_while_running(self):
        e = FocusBreakEngine(10, 5, 0)
        e.start(0.0)
        e.set_cycles_target(2)
        self.assertEqual(e.cycles_target, 2)
        self.assertEqual([x.kind for x in e.tick(30.0)], [
            "break_started", "break_finished", "focus_started", "break_started", "break_finished", "completed"
        ])

    def test_repetition_can_become_infinite_while_running(self):
        e = FocusBreakEngine(10, 5, 1)
        e.start(0.0)
        e.set_cycles_target(0)
        self.assertEqual([x.kind for x in e.tick(15.0)], ["break_started", "break_finished", "focus_started"])
        self.assertEqual(e.phase, Phase.FOCUS)
        self.assertEqual(e.cycle, 2)

    def test_invalid_runtime_cycle_target(self):
        e = FocusBreakEngine(10, 5, 0)
        with self.assertRaises(ValueError):
            e.set_cycles_target(-1)

    def test_stop_resets_state(self):
        e = FocusBreakEngine(10, 5)
        e.start(0.0)
        self.assertEqual([x.kind for x in e.stop()], ["stopped"])
        self.assertEqual(e.phase, Phase.STOPPED)
        self.assertEqual(e.cycle, 0)

    def test_invalid_values(self):
        with self.assertRaises(ValueError):
            FocusBreakEngine(0, 5)
        with self.assertRaises(ValueError):
            FocusBreakEngine(5, 0)
        with self.assertRaises(ValueError):
            FocusBreakEngine(5, 5, -1)


if __name__ == "__main__":
    unittest.main()
