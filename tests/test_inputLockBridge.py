import builtins
import importlib.util
from pathlib import Path
import sys
import types
import unittest

ROOT = Path(__file__).parents[1]
PLUGIN = ROOT / "addon" / "globalPlugins" / "focusBreakTimer.py"
CORE = ROOT / "addon" / "globalPlugins" / "focusBreakTimerCore.py"


def install_stubs():
    builtins._ = lambda s: s

    addonHandler = types.ModuleType("addonHandler")
    addonHandler.initTranslation = lambda: None
    sys.modules["addonHandler"] = addonHandler

    class Conf(dict):
        def __init__(self):
            super().__init__()
            self.spec = {}
            self["focusBreakTimer"] = {
                "focusMinutes": 30,
                "breakMinutes": 5,
                "cycles": 0,
                "finiteCycles": 4,
                "announceEverySeconds": 300,
                "beeps": True,
                "lockDuringBreak": True,
            }
    config = types.ModuleType("config")
    config.conf = Conf()
    sys.modules["config"] = config

    core = types.ModuleType("core")
    core.callLater = lambda *a, **k: None
    sys.modules["core"] = core

    globalPluginHandler = types.ModuleType("globalPluginHandler")
    class BaseGlobalPlugin:
        def __init__(self):
            self._gestureMap = dict(getattr(self, "_GlobalPlugin__gestures", {}))
        def terminate(self): pass
        def bindGesture(self, gesture, scriptName):
            self._gestureMap[gesture] = scriptName
        def bindGestures(self, gestures):
            self._gestureMap.update(gestures)
        def clearGestureBindings(self):
            self._gestureMap.clear()
        def getScript(self, gesture):
            identifier = getattr(gesture, "identifier", None)
            scriptName = self._gestureMap.get(identifier)
            return getattr(self, f"script_{scriptName}", None) if scriptName else None
    globalPluginHandler.GlobalPlugin = BaseGlobalPlugin
    globalPluginHandler.runningPlugins = []
    sys.modules["globalPluginHandler"] = globalPluginHandler

    class Manager:
        def __init__(self): self.mappings = {}
        def getAllGestureMappings(self): return self.mappings
    inputCore = types.ModuleType("inputCore")
    inputCore.manager = Manager()
    sys.modules["inputCore"] = inputCore

    tones = types.ModuleType("tones")
    tones.beep = lambda *a, **k: None
    sys.modules["tones"] = tones

    ui = types.ModuleType("ui")
    ui.messages = []
    ui.message = lambda message, *a, **k: ui.messages.append(message)
    sys.modules["ui"] = ui

    wx = types.ModuleType("wx")
    class Dummy:
        def __init__(self, *a, **k):
            self.value = k.get("initial", False)
            self.enabled = True
            self.bound = {}
        def SetValue(self, value): self.value = value
        def GetValue(self): return self.value
        def Enable(self, enabled=True): self.enabled = bool(enabled)
        def Bind(self, event, handler): self.bound[event] = handler
    wx.SpinCtrl = Dummy
    wx.CheckBox = Dummy
    wx.StaticText = Dummy
    wx.EVT_CHECKBOX = object()
    wx.CallAfter = lambda func, *a, **k: func(*a, **k)
    sys.modules["wx"] = wx

    gui = types.ModuleType("gui")
    class BoxSizerHelper:
        def __init__(self, *a, **k): pass
        def addLabeledControl(self, label, controlClass, **kwargs): return controlClass(**kwargs)
        def addItem(self, x): return x
    class MainFrame:
        def __init__(self):
            self.settingsCalls = []
        def popupSettingsDialog(self, dialogClass, initialCategory=None):
            self.settingsCalls.append((dialogClass, initialCategory))
    gui.guiHelper = types.SimpleNamespace(BoxSizerHelper=BoxSizerHelper)
    gui.mainFrame = MainFrame()
    sys.modules["gui"] = gui

    settingsDialogs = types.ModuleType("gui.settingsDialogs")
    class SettingsPanel: pass
    class NVDASettingsDialog:
        categoryClasses = []
    settingsDialogs.SettingsPanel = SettingsPanel
    settingsDialogs.NVDASettingsDialog = NVDASettingsDialog
    sys.modules["gui.settingsDialogs"] = settingsDialogs

    keyboardHandler = types.ModuleType("keyboardHandler")
    class Gesture:
        def __init__(self, name):
            self.name = name
            self.displayName = name
            self.identifier = name if name.startswith("kb:") else f"kb:{name}"
    class KeyboardInputGesture:
        @classmethod
        def fromName(cls, name): return Gesture(name)
    keyboardHandler.KeyboardInputGesture = KeyboardInputGesture
    sys.modules["keyboardHandler"] = keyboardHandler

    logHandler = types.ModuleType("logHandler")
    class Log:
        def exception(self, *a, **k): pass
        def debugWarning(self, *a, **k): pass
    logHandler.log = Log()
    sys.modules["logHandler"] = logHandler

    scriptHandler = types.ModuleType("scriptHandler")
    def script(description=None, category=None, **kwargs):
        def deco(fn):
            fn.__doc__ = description
            fn.category = category
            return fn
        return deco
    scriptHandler.script = script
    sys.modules["scriptHandler"] = scriptHandler

    # Make the core module available under the relative globalPlugins package import.
    pkg = types.ModuleType("globalPlugins")
    pkg.__path__ = [str(PLUGIN.parent)]
    sys.modules["globalPlugins"] = pkg
    cspec = importlib.util.spec_from_file_location("globalPlugins.focusBreakTimerCore", CORE)
    cmod = importlib.util.module_from_spec(cspec)
    sys.modules[cspec.name] = cmod
    cspec.loader.exec_module(cmod)
    return globalPluginHandler, inputCore


GLOBAL_HANDLER, INPUT_CORE = install_stubs()
spec = importlib.util.spec_from_file_location("globalPlugins.focusBreakTimer", PLUGIN)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class FakeInputLock:
    __module__ = "globalPlugins.inputLock"
    def __init__(self):
        self.locked = False
        self.gesture = None
        self.lastGesture = None
    def script_inputLock(self, gesture):
        self.locked = not self.locked
        self.lastGesture = gesture
        self.gesture = gesture if self.locked else None


class Info:
    def __init__(self, cls, gestures):
        self.cls = cls
        self.scriptName = "inputLock"
        self.gestures = gestures


class InputLockBridgeTests(unittest.TestCase):
    def setUp(self):
        self.plugin = FakeInputLock()
        GLOBAL_HANDLER.runningPlugins[:] = [self.plugin]
        INPUT_CORE.manager.mappings = {
            "Input": {"Toggle input lock": Info(FakeInputLock, ["kb:NVDA+alt+t"])}
        }
        self.bridge = mod.InputLockBridge()

    def test_discovers_configured_input_lock(self):
        self.assertTrue(self.bridge.available())
        self.assertFalse(self.bridge.is_locked())

    def test_locks_and_unlocks_with_users_gesture(self):
        token = self.bridge.lock_for_timer()
        self.assertIsNotNone(token)
        self.assertTrue(self.plugin.locked)
        self.assertIs(self.plugin.gesture, token)
        self.assertEqual(self.plugin.lastGesture.name, "NVDA+alt+t")
        self.assertTrue(self.bridge.owns_lock(token))
        self.assertTrue(self.bridge.unlock_if_owned(token))
        self.assertFalse(self.plugin.locked)

    def test_refuses_to_claim_preexisting_lock(self):
        self.plugin.locked = True
        self.plugin.gesture = object()
        self.assertIsNone(self.bridge.lock_for_timer())
        self.assertTrue(self.plugin.locked)

    def test_fails_safe_without_assigned_gesture(self):
        INPUT_CORE.manager.mappings = {
            "Input": {"Toggle input lock": Info(FakeInputLock, [])}
        }
        self.assertFalse(self.bridge.available())
        self.assertIsNone(self.bridge.lock_for_timer())
        self.assertFalse(self.plugin.locked)

    def test_manual_unlock_relock_is_not_released_by_timer(self):
        token = self.bridge.lock_for_timer()
        self.assertIsNotNone(token)
        # User unlocks with their own new gesture, then locks again.
        manual_unlock = mod.KeyboardInputGesture.fromName("NVDA+alt+t")
        self.plugin.script_inputLock(manual_unlock)
        self.assertFalse(self.plugin.locked)
        manual_lock = mod.KeyboardInputGesture.fromName("NVDA+alt+t")
        self.plugin.script_inputLock(manual_lock)
        self.assertTrue(self.plugin.locked)
        self.assertIs(self.plugin.gesture, manual_lock)
        self.assertFalse(self.bridge.owns_lock(token))
        self.assertTrue(self.bridge.unlock_if_owned(token))
        self.assertTrue(self.plugin.locked)
        self.assertIs(self.plugin.gesture, manual_lock)

    def test_fails_safe_without_input_lock(self):
        GLOBAL_HANDLER.runningPlugins[:] = []
        self.assertFalse(self.bridge.available())
        self.assertIsNone(self.bridge.is_locked())
        self.assertIsNone(self.bridge.lock_for_timer())


class GlobalPluginInputLockOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.inputLock = FakeInputLock()
        GLOBAL_HANDLER.runningPlugins[:] = [self.inputLock]
        INPUT_CORE.manager.mappings = {
            "Input": {"Toggle input lock": Info(FakeInputLock, ["kb:NVDA+alt+t"])}
        }
        sys.modules["config"].conf["focusBreakTimer"]["lockDuringBreak"] = True
        self.timer = mod.GlobalPlugin()

    def tearDown(self):
        self.timer.terminate()
        GLOBAL_HANDLER.runningPlugins[:] = []

    def test_break_lock_is_released_when_still_owned(self):
        self.timer._beginBreakLock()
        token = self.timer._inputLockToken
        self.assertIsNotNone(token)
        self.assertTrue(self.inputLock.locked)
        self.timer._releaseOwnedInputLock()
        self.assertFalse(self.inputLock.locked)
        self.assertIsNone(self.timer._inputLockToken)

    def test_preexisting_lock_is_never_claimed(self):
        manual = mod.KeyboardInputGesture.fromName("NVDA+alt+t")
        self.inputLock.script_inputLock(manual)
        self.timer._beginBreakLock()
        self.assertIsNone(self.timer._inputLockToken)
        self.timer._releaseOwnedInputLock()
        self.assertTrue(self.inputLock.locked)
        self.assertIs(self.inputLock.gesture, manual)

    def test_manual_relock_replaces_timer_ownership(self):
        self.timer._beginBreakLock()
        timerToken = self.timer._inputLockToken
        self.assertIsNotNone(timerToken)
        self.inputLock.script_inputLock(mod.KeyboardInputGesture.fromName("NVDA+alt+t"))
        manual = mod.KeyboardInputGesture.fromName("NVDA+alt+t")
        self.inputLock.script_inputLock(manual)
        self.timer._releaseOwnedInputLock()
        self.assertTrue(self.inputLock.locked)
        self.assertIs(self.inputLock.gesture, manual)


class SettingsPanelTests(unittest.TestCase):
    def setUp(self):
        conf = sys.modules["config"].conf["focusBreakTimer"]
        conf.update({
            "focusMinutes": 30,
            "breakMinutes": 5,
            "cycles": 0,
            "finiteCycles": 4,
            "announceEverySeconds": 300,
            "beeps": True,
            "lockDuringBreak": True,
        })
        self.conf = conf
        self.panel = mod.FocusBreakSettingsPanel()
        self.panel.makeSettings(object())

    def test_defaults_are_exposed_as_nvda_settings(self):
        self.assertEqual(self.panel.focusMinutes.GetValue(), 30)
        self.assertEqual(self.panel.breakMinutes.GetValue(), 5)
        self.assertTrue(self.panel.repeatIndefinitely.GetValue())
        self.assertFalse(self.panel.cycles.enabled)
        self.assertTrue(self.panel.lockDuringBreak.GetValue())

    def test_finite_cycle_configuration_is_saved(self):
        self.panel.focusMinutes.SetValue(45)
        self.panel.breakMinutes.SetValue(10)
        self.panel.repeatIndefinitely.SetValue(False)
        self.panel._updateCyclesControl()
        self.panel.cycles.SetValue(3)
        self.panel.lockDuringBreak.SetValue(False)
        self.panel.announceEverySeconds.SetValue(600)
        self.panel.beeps.SetValue(False)
        self.panel.onSave()
        self.assertEqual(self.conf["focusMinutes"], 45)
        self.assertEqual(self.conf["breakMinutes"], 10)
        self.assertEqual(self.conf["cycles"], 3)
        self.assertFalse(self.conf["lockDuringBreak"])
        self.assertEqual(self.conf["announceEverySeconds"], 600)
        self.assertFalse(self.conf["beeps"])
        self.assertTrue(self.panel.cycles.enabled)

    def test_repeat_indefinitely_is_stored_as_zero_cycles(self):
        self.panel.repeatIndefinitely.SetValue(True)
        self.panel.cycles.SetValue(7)
        self.panel.onSave()
        self.assertEqual(self.conf["cycles"], 0)


class GlobalPluginSettingsBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.inputLock = FakeInputLock()
        GLOBAL_HANDLER.runningPlugins[:] = [self.inputLock]
        INPUT_CORE.manager.mappings = {
            "Input": {"Toggle input lock": Info(FakeInputLock, ["kb:NVDA+alt+t"])}
        }
        self.conf = sys.modules["config"].conf["focusBreakTimer"]
        self.conf["lockDuringBreak"] = True
        self.timer = mod.GlobalPlugin()

    def tearDown(self):
        self.timer.terminate()
        GLOBAL_HANDLER.runningPlugins[:] = []
        self.conf["lockDuringBreak"] = True

    def test_input_lock_can_be_disabled_from_settings(self):
        self.conf["lockDuringBreak"] = False
        self.timer._beginBreakLock()
        self.assertFalse(self.inputLock.locked)
        self.assertIsNone(self.timer._inputLockToken)


if __name__ == "__main__":
    unittest.main()


class CommandLayerTests(unittest.TestCase):
    def setUp(self):
        self.conf = sys.modules["config"].conf["focusBreakTimer"]
        self.conf.update({
            "focusMinutes": 30,
            "breakMinutes": 5,
            "cycles": 0,
            "finiteCycles": 4,
            "announceEverySeconds": 300,
            "beeps": True,
            "lockDuringBreak": False,
        })
        sys.modules["ui"].messages.clear()
        sys.modules["gui"].mainFrame.settingsCalls.clear()
        self.timer = mod.GlobalPlugin()

    def tearDown(self):
        self.timer.terminate()

    def _gesture(self, identifier):
        gesture = mod.KeyboardInputGesture.fromName(identifier.split(":", 1)[-1])
        gesture.identifier = identifier
        return gesture

    def test_default_entry_gesture_is_nvda_alt_e(self):
        script = self.timer.getScript(self._gesture("kb:NVDA+alt+e"))
        self.assertIsNotNone(script)
        self.assertEqual(script.__name__, "script_timerLayer")

    def test_i_starts_timer_and_layer_exits(self):
        self.timer.script_timerLayer(self._gesture("kb:NVDA+alt+e"))
        self.assertTrue(self.timer._layerActive)
        command = self.timer.getScript(self._gesture("kb:i"))
        command(self._gesture("kb:i"))
        self.assertFalse(self.timer._layerActive)
        self.assertIsNotNone(self.timer._engine)
        self.assertEqual(self.timer._engine.phase, mod.Phase.FOCUS)
        self.assertEqual(set(self.timer._gestureMap), {"kb:NVDA+alt+e"})


    def test_i_does_not_restart_running_timer(self):
        self.timer.script_startTimer(None)
        original_engine = self.timer._engine
        self.timer.script_timerLayer(self._gesture("kb:NVDA+alt+e"))
        self.timer.getScript(self._gesture("kb:i"))(self._gesture("kb:i"))
        self.assertIs(self.timer._engine, original_engine)
        self.assertTrue(any("Shift+I" in message for message in sys.modules["ui"].messages))
        self.assertFalse(self.timer._layerActive)

    def test_shift_i_restarts_running_timer_and_layer_exits(self):
        self.timer.script_startTimer(None)
        original_engine = self.timer._engine
        self.timer.script_timerLayer(self._gesture("kb:NVDA+alt+e"))
        command = self.timer.getScript(self._gesture("kb:shift+i"))
        self.assertIsNotNone(command)
        command(self._gesture("kb:shift+i"))
        self.assertIsNot(self.timer._engine, original_engine)
        self.assertEqual(self.timer._engine.phase, mod.Phase.FOCUS)
        self.assertEqual(self.timer._engine.cycle, 1)
        self.assertFalse(self.timer._layerActive)
        self.assertEqual(set(self.timer._gestureMap), {"kb:NVDA+alt+e"})

    def test_d_stops_timer(self):
        self.timer.script_startTimer(None)
        self.timer.script_timerLayer(self._gesture("kb:NVDA+alt+e"))
        self.timer.getScript(self._gesture("kb:d"))(self._gesture("kb:d"))
        self.assertEqual(self.timer._engine.phase, mod.Phase.STOPPED)
        self.assertFalse(self.timer._layerActive)

    def test_t_reports_current_time(self):
        self.timer.script_startTimer(None)
        sys.modules["ui"].messages.clear()
        self.timer.script_timerLayer(self._gesture("kb:NVDA+alt+e"))
        self.timer.getScript(self._gesture("kb:t"))(self._gesture("kb:t"))
        self.assertTrue(any("Quedan" in message for message in sys.modules["ui"].messages))

    def test_r_toggles_repetition_and_preserves_finite_cycle_count(self):
        self.assertEqual(self.conf["cycles"], 0)
        self.timer.script_timerLayer(self._gesture("kb:NVDA+alt+e"))
        self.timer.getScript(self._gesture("kb:r"))(self._gesture("kb:r"))
        self.assertEqual(self.conf["cycles"], 4)
        self.timer.script_timerLayer(self._gesture("kb:NVDA+alt+e"))
        self.timer.getScript(self._gesture("kb:r"))(self._gesture("kb:r"))
        self.assertEqual(self.conf["cycles"], 0)
        self.assertEqual(self.conf["finiteCycles"], 4)

    def test_r_changes_running_engine_immediately(self):
        self.timer.script_startTimer(None)
        self.assertEqual(self.timer._engine.cycles_target, 0)
        self.timer.script_toggleRepeat(None)
        self.assertEqual(self.timer._engine.cycles_target, 4)
        self.timer.script_toggleRepeat(None)
        self.assertEqual(self.timer._engine.cycles_target, 0)

    def test_o_opens_focus_break_timer_settings_directly(self):
        self.timer.script_timerLayer(self._gesture("kb:NVDA+alt+e"))
        self.timer.getScript(self._gesture("kb:o"))(self._gesture("kb:o"))
        calls = sys.modules["gui"].mainFrame.settingsCalls
        self.assertEqual(calls[-1], (mod.NVDASettingsDialog, mod.FocusBreakSettingsPanel))
        self.assertFalse(self.timer._layerActive)

    def test_unknown_layer_key_beeps_and_exits(self):
        self.timer.script_timerLayer(self._gesture("kb:NVDA+alt+e"))
        command = self.timer.getScript(self._gesture("kb:x"))
        self.assertIsNotNone(command)
        command(self._gesture("kb:x"))
        self.assertFalse(self.timer._layerActive)
        self.assertEqual(set(self.timer._gestureMap), {"kb:NVDA+alt+e"})
