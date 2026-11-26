# -*- coding: UTF-8 -*-
"""Focus / break timer Global Plugin for NVDA."""
from __future__ import annotations

import time
from datetime import datetime
from typing import Optional

import addonHandler
import config
import core
import globalPluginHandler
import inputCore
import tones
import ui
import wx
import gui
from gui import guiHelper
from gui.settingsDialogs import NVDASettingsDialog, SettingsPanel
from keyboardHandler import KeyboardInputGesture
from logHandler import log
from scriptHandler import script

from .focusBreakTimerCore import (
    FocusBreakEngine,
    Phase,
    TimerEvent,
    is_minute_in_daily_window,
    minutes_from_hm,
)

addonHandler.initTranslation()

CONFIG_SECTION = "focusBreakTimer"
CATEGORY = _("Temporizador de enfoque")

config.conf.spec[CONFIG_SECTION] = {
    "focusMinutes": "integer(default=30,min=1,max=1440)",
    "breakMinutes": "integer(default=5,min=1,max=1440)",
    "cycles": "integer(default=0,min=0,max=999)",
    "finiteCycles": "integer(default=4,min=1,max=999)",
    "announceRemaining": "boolean(default=false)",
    "announceEverySeconds": "integer(default=300,min=0,max=86400)",
    "beeps": "boolean(default=true)",
    "lockDuringBreak": "boolean(default=true)",
    "startOnNVDA": "boolean(default=false)",
    "suspendScheduleEnabled": "boolean(default=false)",
    "suspendFromMinutes": "integer(default=1320,min=0,max=1439)",
    "suspendUntilMinutes": "integer(default=360,min=0,max=1439)",
}


def _format_duration(seconds: int) -> str:
    seconds = max(0, int(seconds))
    minutes, secs = divmod(seconds, 60)
    if minutes and secs:
        return _("{minutes} minutos y {seconds} segundos").format(minutes=minutes, seconds=secs)
    if minutes:
        return _("{minutes} minutos").format(minutes=minutes)
    return _("{seconds} segundos").format(seconds=secs)


def _format_clock_minutes(total_minutes: int) -> str:
    total_minutes = int(total_minutes) % (24 * 60)
    hour, minute = divmod(total_minutes, 60)
    return f"{hour:02d}:{minute:02d}"


def _local_minutes_now() -> int:
    now = datetime.now()
    return now.hour * 60 + now.minute


class InputLockBridge:
    """Narrow integration boundary for the external Input Lock add-on.

    Input Lock 26.1 exposes a toggle script and a ``locked`` state on its running
    GlobalPlugin instance, but does not publish a stable third-party API.  We therefore
    discover the running instance conservatively, require the expected surface, and use
    the user's currently assigned Input Lock gesture as the gesture object passed to its
    own toggle script.  Failure always degrades to an unlocked break rather than guessing.
    """

    MODULE_SUFFIX = "globalPlugins.inputLock"

    def _plugin(self):
        for plugin in globalPluginHandler.runningPlugins:
            module_name = plugin.__class__.__module__
            if module_name == self.MODULE_SUFFIX or module_name.endswith(".inputLock"):
                if (
                    hasattr(plugin, "script_inputLock")
                    and hasattr(plugin, "locked")
                    and hasattr(plugin, "gesture")
                ):
                    return plugin
        return None

    def _gesture_identifier(self, plugin) -> Optional[str]:
        try:
            mappings = inputCore.manager.getAllGestureMappings()
        except Exception:
            log.exception("FocusBreakTimer: unable to enumerate NVDA gesture mappings")
            return None
        for commands in mappings.values():
            for info in commands.values():
                try:
                    matches = info.cls is plugin.__class__ and info.scriptName == "inputLock"
                except Exception:
                    continue
                if not matches:
                    continue
                for identifier in info.gestures:
                    if identifier.startswith("kb:") or identifier.startswith("kb("):
                        return identifier
        return None

    @staticmethod
    def _key_name(identifier: str) -> Optional[str]:
        if ":" not in identifier:
            return None
        source, key_name = identifier.split(":", 1)
        if not source.startswith("kb") or not key_name:
            return None
        return key_name

    def available(self) -> bool:
        plugin = self._plugin()
        return plugin is not None and self._gesture_identifier(plugin) is not None

    def is_locked(self) -> Optional[bool]:
        plugin = self._plugin()
        if plugin is None:
            return None
        try:
            return bool(plugin.locked)
        except Exception:
            return None

    def lock_for_timer(self):
        """Lock Input Lock and return an ownership token, or ``None`` on failure.

        The token is the exact keyboard gesture object that Input Lock stores in
        ``plugin.gesture`` while locked.  Identity is used later so a manual
        unlock/re-lock cannot be mistaken for a lock still owned by this timer.
        """
        plugin = self._plugin()
        if plugin is None:
            return None
        try:
            if bool(plugin.locked):
                return None
        except Exception:
            return None

        identifier = self._gesture_identifier(plugin)
        if not identifier:
            return None
        key_name = self._key_name(identifier)
        if not key_name:
            return None
        try:
            gesture = KeyboardInputGesture.fromName(key_name)
            # Calling Input Lock's own toggle script preserves its capture gesture and
            # avoids sending a physical Windows key. Input Lock stores this exact
            # object while the lock is active, which doubles as our ownership token.
            plugin.script_inputLock(gesture)
            if bool(plugin.locked) and plugin.gesture is gesture:
                return gesture
        except Exception:
            log.exception("FocusBreakTimer: Input Lock integration failed while locking")
        return None

    def owns_lock(self, token) -> bool:
        if token is None:
            return False
        plugin = self._plugin()
        if plugin is None:
            return False
        try:
            return bool(plugin.locked) and plugin.gesture is token
        except Exception:
            return False

    def unlock_if_owned(self, token) -> bool:
        """Unlock only if Input Lock still holds the exact timer-owned token.

        If the user has already unlocked or replaced the lock with a new manual
        one, this method deliberately leaves the current state untouched.
        """
        if token is None:
            return True
        plugin = self._plugin()
        if plugin is None:
            return False
        try:
            if not bool(plugin.locked):
                return True
            if plugin.gesture is not token:
                return True
            plugin.script_inputLock(token)
            return not bool(plugin.locked)
        except Exception:
            log.exception("FocusBreakTimer: Input Lock integration failed while unlocking")
            return False



class FocusBreakSettingsPanel(SettingsPanel):
    title = _("Temporizador de enfoque")

    def makeSettings(self, settingsSizer):
        helper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
        conf = config.conf[CONFIG_SECTION]

        self.focusMinutes = helper.addLabeledControl(
            _("Duración del &enfoque, en minutos:"),
            wx.SpinCtrl,
            min=1,
            max=1440,
            initial=int(conf["focusMinutes"]),
        )
        self.breakMinutes = helper.addLabeledControl(
            _("Duración del &descanso, en minutos:"),
            wx.SpinCtrl,
            min=1,
            max=1440,
            initial=int(conf["breakMinutes"]),
        )

        storedCycles = int(conf["cycles"])
        storedFiniteCycles = int(conf.get("finiteCycles", storedCycles if storedCycles > 0 else 4))
        self.repeatIndefinitely = helper.addItem(
            wx.CheckBox(self, label=_("&Repetir los ciclos indefinidamente"))
        )
        self.repeatIndefinitely.SetValue(storedCycles == 0)
        self.repeatIndefinitely.Bind(wx.EVT_CHECKBOX, self._onRepeatIndefinitelyChanged)

        self.cycles = helper.addLabeledControl(
            _("&Número de ciclos:"),
            wx.SpinCtrl,
            min=1,
            max=999,
            initial=storedCycles if storedCycles > 0 else storedFiniteCycles,
        )
        self._updateCyclesControl()

        self.lockDuringBreak = helper.addItem(
            wx.CheckBox(self, label=_("Activar &Input Lock durante el descanso"))
        )
        self.lockDuringBreak.SetValue(bool(conf["lockDuringBreak"]))

        self.announceRemaining = helper.addItem(
            wx.CheckBox(self, label=_("&Anunciar automáticamente el tiempo restante"))
        )
        self.announceRemaining.SetValue(bool(conf["announceRemaining"]))
        self.announceRemaining.Bind(wx.EVT_CHECKBOX, self._onAnnounceRemainingChanged)

        storedAnnounceEverySeconds = int(conf["announceEverySeconds"])
        storedAnnounceEveryMinutes = max(1, round(storedAnnounceEverySeconds / 60))
        self.announceEveryMinutes = helper.addLabeledControl(
            _("Anunciar tiempo restante cada, en &minutos:"),
            wx.SpinCtrl,
            min=1,
            max=1440,
            initial=storedAnnounceEveryMinutes,
        )
        self._updateAnnounceControl()
        self.beeps = helper.addItem(
            wx.CheckBox(self, label=_("Reproducir &sonidos al cambiar de período"))
        )
        self.beeps.SetValue(bool(conf["beeps"]))

        self.startOnNVDA = helper.addItem(
            wx.CheckBox(self, label=_("&Iniciar el temporizador al iniciar NVDA"))
        )
        self.startOnNVDA.SetValue(bool(conf.get("startOnNVDA", False)))

        self.suspendScheduleEnabled = helper.addItem(
            wx.CheckBox(self, label=_("&Suspender el temporizador automáticamente en un horario"))
        )
        self.suspendScheduleEnabled.SetValue(bool(conf.get("suspendScheduleEnabled", False)))
        self.suspendScheduleEnabled.Bind(wx.EVT_CHECKBOX, self._onSuspendScheduleChanged)

        suspend_from = int(conf.get("suspendFromMinutes", 22 * 60))
        suspend_until = int(conf.get("suspendUntilMinutes", 6 * 60))
        from_hour, from_minute = divmod(suspend_from, 60)
        until_hour, until_minute = divmod(suspend_until, 60)

        self.suspendFromHour = helper.addLabeledControl(
            _("Suspender &desde, hora:"),
            wx.SpinCtrl,
            min=0,
            max=23,
            initial=from_hour,
        )
        self.suspendFromMinute = helper.addLabeledControl(
            _("Suspender desde, &minutos:"),
            wx.SpinCtrl,
            min=0,
            max=59,
            initial=from_minute,
        )
        self.suspendUntilHour = helper.addLabeledControl(
            _("Reanudar &a las, hora:"),
            wx.SpinCtrl,
            min=0,
            max=23,
            initial=until_hour,
        )
        self.suspendUntilMinute = helper.addLabeledControl(
            _("Reanudar a las, m&inutos:"),
            wx.SpinCtrl,
            min=0,
            max=59,
            initial=until_minute,
        )
        self._updateSuspendScheduleControls()

        helper.addItem(
            wx.StaticText(
                self,
                label=_(
                    "Los cambios de duración y ciclos se aplicarán la próxima vez que se inicie o reinicie "
                    "el temporizador. El horario de suspensión se aplica automáticamente tras guardar. "
                    "La opción de iniciar con NVDA tiene efecto en el próximo inicio de NVDA. Para usar "
                    "Input Lock durante el descanso, su comando de alternar bloqueo debe tener un gesto "
                    "de teclado asignado."
                ),
            )
        )

    def _onRepeatIndefinitelyChanged(self, evt):
        self._updateCyclesControl()
        evt.Skip()

    def _updateCyclesControl(self):
        self.cycles.Enable(not self.repeatIndefinitely.GetValue())

    def _onAnnounceRemainingChanged(self, evt):
        self._updateAnnounceControl()
        evt.Skip()

    def _updateAnnounceControl(self):
        self.announceEveryMinutes.Enable(self.announceRemaining.GetValue())

    def _onSuspendScheduleChanged(self, evt):
        self._updateSuspendScheduleControls()
        evt.Skip()

    def _updateSuspendScheduleControls(self):
        enabled = self.suspendScheduleEnabled.GetValue()
        self.suspendFromHour.Enable(enabled)
        self.suspendFromMinute.Enable(enabled)
        self.suspendUntilHour.Enable(enabled)
        self.suspendUntilMinute.Enable(enabled)

    def onSave(self):
        conf = config.conf[CONFIG_SECTION]
        conf["focusMinutes"] = self.focusMinutes.GetValue()
        conf["breakMinutes"] = self.breakMinutes.GetValue()
        finite_cycles = self.cycles.GetValue()
        conf["finiteCycles"] = finite_cycles
        conf["cycles"] = 0 if self.repeatIndefinitely.GetValue() else finite_cycles
        conf["lockDuringBreak"] = self.lockDuringBreak.GetValue()
        conf["announceRemaining"] = self.announceRemaining.GetValue()
        conf["announceEverySeconds"] = self.announceEveryMinutes.GetValue() * 60
        conf["beeps"] = self.beeps.GetValue()
        conf["startOnNVDA"] = self.startOnNVDA.GetValue()
        conf["suspendScheduleEnabled"] = self.suspendScheduleEnabled.GetValue()
        conf["suspendFromMinutes"] = minutes_from_hm(
            self.suspendFromHour.GetValue(),
            self.suspendFromMinute.GetValue(),
        )
        conf["suspendUntilMinutes"] = minutes_from_hm(
            self.suspendUntilHour.GetValue(),
            self.suspendUntilMinute.GetValue(),
        )


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = CATEGORY

    def __init__(self):
        super().__init__()
        self._engine: Optional[FocusBreakEngine] = None
        self._loopGeneration = 0
        self._loopActive = False
        self._inputLock = InputLockBridge()
        self._inputLockToken = None
        self._lastAnnouncedRemaining: Optional[int] = None
        self._layerActive = False
        self._pausedBySchedule = False
        self._pendingStartupStart = bool(config.conf[CONFIG_SECTION].get("startOnNVDA", False))
        self._scheduleWatchGeneration = 0
        self._bindBaseGesture()
        if FocusBreakSettingsPanel not in NVDASettingsDialog.categoryClasses:
            NVDASettingsDialog.categoryClasses.append(FocusBreakSettingsPanel)
        self._startScheduleWatch()

    def _bindBaseGesture(self):
        self.bindGesture("kb:NVDA+alt+e", "timerLayer")

    def getScript(self, gesture):
        if not self._layerActive:
            return globalPluginHandler.GlobalPlugin.getScript(self, gesture)
        command = globalPluginHandler.GlobalPlugin.getScript(self, gesture)
        if command is None:
            command = self.script_layerError

        def runAndFinish(innerGesture):
            try:
                return command(innerGesture)
            finally:
                self._finishCommandLayer()

        return runAndFinish

    def _finishCommandLayer(self):
        self._layerActive = False
        self.clearGestureBindings()
        self._bindBaseGesture()

    def script_layerError(self, gesture):
        tones.beep(120, 100)

    @script(
        description=_(
            "Activa la capa de comandos del temporizador: I iniciar, Shift+I reiniciar, "
            "D detener, T informar tiempo, R alternar repetición y O abrir opciones."
        ),
        category=CATEGORY,
    )
    def script_timerLayer(self, gesture):
        if self._layerActive:
            self.script_layerError(gesture)
            return
        self.bindGestures({
            "kb:i": "startTimer",
            "kb:shift+i": "restartTimer",
            "kb:d": "stopTimer",
            "kb:t": "reportStatus",
            "kb:r": "toggleRepeat",
            "kb:o": "showSettings",
        })
        self._layerActive = True
        tones.beep(100, 30)

    def terminate(self):
        try:
            self._stopScheduleWatch()
            self._stopTimerLoop()
            self._releaseOwnedInputLock()
        finally:
            try:
                NVDASettingsDialog.categoryClasses.remove(FocusBreakSettingsPanel)
            except (ValueError, RuntimeError):
                pass
            super().terminate()

    def _startScheduleWatch(self):
        self._scheduleWatchGeneration += 1
        generation = self._scheduleWatchGeneration
        core.callLater(500, self._onScheduleWatch, generation)

    def _stopScheduleWatch(self):
        self._scheduleWatchGeneration += 1

    def _scheduleValues(self):
        conf = config.conf[CONFIG_SECTION]
        enabled = bool(conf.get("suspendScheduleEnabled", False))
        start = int(conf.get("suspendFromMinutes", 22 * 60))
        end = int(conf.get("suspendUntilMinutes", 6 * 60))
        return enabled, start, end

    def _isScheduleSuspendedNow(self) -> bool:
        enabled, start, end = self._scheduleValues()
        if not enabled:
            return False
        return is_minute_in_daily_window(_local_minutes_now(), start, end)

    def _scheduleResumeLabel(self) -> str:
        _, _, end = self._scheduleValues()
        return _format_clock_minutes(end)

    def _applyScheduleState(self):
        suspended = self._isScheduleSuspendedNow()
        if suspended:
            if self._engine is not None and self._engine.phase in (Phase.FOCUS, Phase.BREAK):
                # Pause the state machine without sending its generic pause event; this
                # is a distinct automatic suspension with its own spoken message.
                self._engine.pause(time.monotonic())
                self._releaseOwnedInputLock()
                self._pausedBySchedule = True
                ui.message(
                    _("Horario de suspensión iniciado. Temporizador suspendido hasta las {time}.").format(
                        time=self._scheduleResumeLabel()
                    )
                )
            return True

        if self._pausedBySchedule:
            self._pausedBySchedule = False
            if self._engine is not None and self._engine.phase == Phase.PAUSED:
                for event in self._engine.resume(time.monotonic()):
                    self._processEvent(event)
            return False

        if self._pendingStartupStart:
            # If the preference was disabled after NVDA started but before a deferred
            # start could happen, honor the new preference and cancel the pending start.
            if bool(config.conf[CONFIG_SECTION].get("startOnNVDA", False)):
                self._pendingStartupStart = False
                self._startFreshTimer(respectSchedule=False)
            else:
                self._pendingStartupStart = False
        return False

    def _onScheduleWatch(self, generation: int):
        if generation != self._scheduleWatchGeneration:
            return
        self._applyScheduleState()
        if generation == self._scheduleWatchGeneration:
            core.callLater(1000, self._onScheduleWatch, generation)

    def _newEngine(self) -> FocusBreakEngine:
        conf = config.conf[CONFIG_SECTION]
        return FocusBreakEngine(
            focus_seconds=int(conf["focusMinutes"]) * 60,
            break_seconds=int(conf["breakMinutes"]) * 60,
            cycles=int(conf["cycles"]),
        )

    def _beep(self, kind: str):
        if not config.conf[CONFIG_SECTION]["beeps"]:
            return
        frequency = 750 if kind == "focus_done" else 1000 if kind == "break_done" else 500
        try:
            tones.beep(frequency, 250)
        except Exception:
            log.debugWarning("FocusBreakTimer: sound notification unavailable")

    def _startTimerLoop(self):
        self._loopGeneration += 1
        generation = self._loopGeneration
        self._loopActive = True
        core.callLater(500, self._onTimer, generation)

    def _stopTimerLoop(self):
        self._loopActive = False
        self._loopGeneration += 1

    def _releaseOwnedInputLock(self):
        token = self._inputLockToken
        self._inputLockToken = None
        if token is None:
            return
        if not self._inputLock.unlock_if_owned(token):
            ui.message(
                _(
                    "No se pudo desactivar el bloqueo iniciado por el temporizador. "
                    "Use el gesto de Input Lock manualmente."
                )
            )

    def _beginBreakLock(self):
        self._inputLockToken = None
        if not bool(config.conf[CONFIG_SECTION]["lockDuringBreak"]):
            return
        state = self._inputLock.is_locked()
        if state is True:
            ui.message(_("Input Lock ya estaba activado; el temporizador no modificará ese bloqueo."))
            return
        if state is None:
            ui.message(_("Descanso iniciado. Input Lock no está disponible."))
            return
        token = self._inputLock.lock_for_timer()
        if token is not None:
            self._inputLockToken = token
        else:
            ui.message(
                _(
                    "Descanso iniciado, pero no se pudo activar Input Lock. "
                    "Compruebe que su comando tenga un gesto de teclado asignado."
                )
            )

    def _processEvent(self, event: TimerEvent):
        if event.kind == "focus_started":
            self._lastAnnouncedRemaining = None
            ui.message(_("Enfoque iniciado. Ciclo {cycle}.").format(cycle=event.cycle))
        elif event.kind == "break_started":
            self._beep("focus_done")
            ui.message(_("Período de enfoque terminado. Comienza el descanso."))
            self._beginBreakLock()
            self._lastAnnouncedRemaining = None
        elif event.kind == "break_finished":
            self._releaseOwnedInputLock()
            self._beep("break_done")
        elif event.kind == "completed":
            self._pausedBySchedule = False
            self._stopTimerLoop()
            ui.message(_("Temporizador completado."))
        elif event.kind == "stopped":
            self._pausedBySchedule = False
            self._releaseOwnedInputLock()
            self._stopTimerLoop()
            ui.message(_("Temporizador detenido."))
        elif event.kind == "paused":
            # A paused break should not keep the user locked indefinitely.
            self._releaseOwnedInputLock()
            ui.message(_("Temporizador pausado."))
        elif event.kind == "resumed":
            if self._engine and self._engine.phase == Phase.BREAK:
                self._beginBreakLock()
            ui.message(_("Temporizador reanudado."))

    def _onTimer(self, generation: int):
        if not self._loopActive or generation != self._loopGeneration or self._engine is None:
            return
        # Check the wall-clock suspension before advancing the state machine so a
        # boundary such as 22:00 cannot start a break/lock just before the schedule
        # watcher gets its next turn.
        if self._applyScheduleState():
            if self._loopActive and generation == self._loopGeneration:
                core.callLater(500, self._onTimer, generation)
            return
        now = time.monotonic()

        # Ownership is tied to the exact gesture object stored by Input Lock.
        # A manual unlock or unlock/re-lock replaces/removes that object, so the
        # timer relinquishes ownership and never touches a new user-created lock.
        if self._inputLockToken is not None and not self._inputLock.owns_lock(self._inputLockToken):
            self._inputLockToken = None

        for event in self._engine.tick(now):
            self._processEvent(event)

        if self._engine.phase == Phase.STOPPED:
            self._stopTimerLoop()
            return

        announce_remaining = bool(config.conf[CONFIG_SECTION]["announceRemaining"])
        announce_every = int(config.conf[CONFIG_SECTION]["announceEverySeconds"])
        if announce_remaining and announce_every > 0 and self._engine.phase != Phase.PAUSED:
            remaining = self._engine.remaining_seconds(now)
            if remaining > 0 and remaining % announce_every == 0 and remaining != self._lastAnnouncedRemaining:
                label = _("Enfoque") if self._engine.phase == Phase.FOCUS else _("Descanso")
                ui.message(_("{label}: quedan {duration}.").format(label=label, duration=_format_duration(remaining)))
                self._lastAnnouncedRemaining = remaining

        if self._loopActive and generation == self._loopGeneration:
            core.callLater(500, self._onTimer, generation)

    def _startFreshTimer(self, respectSchedule: bool = True) -> bool:
        if respectSchedule and self._isScheduleSuspendedNow():
            ui.message(
                _("El temporizador está suspendido por horario hasta las {time}.").format(
                    time=self._scheduleResumeLabel()
                )
            )
            return False
        self._pendingStartupStart = False
        self._pausedBySchedule = False
        self._releaseOwnedInputLock()
        self._stopTimerLoop()
        self._engine = self._newEngine()
        for event in self._engine.start(time.monotonic()):
            self._processEvent(event)
        self._startTimerLoop()
        return True

    @script(description=_("Inicia el temporizador de enfoque"), category=CATEGORY)
    def script_startTimer(self, gesture):
        if self._engine is not None and self._engine.phase != Phase.STOPPED:
            ui.message(_("El temporizador ya está en ejecución. Use Shift+I en la capa para reiniciarlo."))
            return
        self._startFreshTimer()

    @script(description=_("Reinicia el temporizador de enfoque desde el comienzo"), category=CATEGORY)
    def script_restartTimer(self, gesture):
        self._startFreshTimer()

    @script(description=_("Pausa o reanuda el temporizador de enfoque"), category=CATEGORY)
    def script_pauseResume(self, gesture):
        if self._pausedBySchedule or self._isScheduleSuspendedNow():
            ui.message(
                _("El temporizador está suspendido por horario hasta las {time}.").format(
                    time=self._scheduleResumeLabel()
                )
            )
            return
        if self._engine is None or self._engine.phase == Phase.STOPPED:
            ui.message(_("El temporizador no está en ejecución."))
            return
        now = time.monotonic()
        events = self._engine.resume(now) if self._engine.phase == Phase.PAUSED else self._engine.pause(now)
        for event in events:
            self._processEvent(event)

    @script(description=_("Detiene el temporizador de enfoque"), category=CATEGORY)
    def script_stopTimer(self, gesture):
        self._pendingStartupStart = False
        self._pausedBySchedule = False
        if self._engine is None or self._engine.phase == Phase.STOPPED:
            self._releaseOwnedInputLock()
            ui.message(_("El temporizador ya está detenido."))
            return
        for event in self._engine.stop():
            self._processEvent(event)

    @script(description=_("Activa o desactiva la repetición de ciclos"), category=CATEGORY)
    def script_toggleRepeat(self, gesture):
        conf = config.conf[CONFIG_SECTION]
        current_cycles = int(conf["cycles"])
        if current_cycles == 0:
            finite_cycles = int(conf.get("finiteCycles", 4))
            finite_cycles = max(1, finite_cycles)
            conf["cycles"] = finite_cycles
            if self._engine is not None and self._engine.phase != Phase.STOPPED:
                self._engine.set_cycles_target(max(finite_cycles, self._engine.cycle))
                if self._engine.cycle >= finite_cycles:
                    ui.message(_("Repetición indefinida desactivada. El temporizador se detendrá al finalizar el ciclo actual."))
                else:
                    ui.message(
                        _("Repetición indefinida desactivada. Se ejecutarán {cycles} ciclos.").format(
                            cycles=finite_cycles
                        )
                    )
            else:
                ui.message(
                    _("Repetición indefinida desactivada. Se ejecutarán {cycles} ciclos.").format(
                        cycles=finite_cycles
                    )
                )
        else:
            conf["finiteCycles"] = current_cycles
            conf["cycles"] = 0
            if self._engine is not None and self._engine.phase != Phase.STOPPED:
                self._engine.set_cycles_target(0)
            ui.message(_("Repetición indefinida activada."))

    @script(description=_("Abre las opciones del Temporizador de enfoque"), category=CATEGORY)
    def script_showSettings(self, gesture):
        wx.CallAfter(
            gui.mainFrame.popupSettingsDialog,
            NVDASettingsDialog,
            FocusBreakSettingsPanel,
        )

    @script(description=_("Informa el estado y el tiempo restante del temporizador"), category=CATEGORY)
    def script_reportStatus(self, gesture):
        if self._engine is None or self._engine.phase == Phase.STOPPED:
            if self._pendingStartupStart and self._isScheduleSuspendedNow():
                ui.message(
                    _("Temporizador pendiente de inicio. Horario de suspensión activo hasta las {time}.").format(
                        time=self._scheduleResumeLabel()
                    )
                )
            else:
                ui.message(_("Temporizador detenido."))
            return
        snap = self._engine.snapshot(time.monotonic())
        phase = snap.paused_from if snap.phase == Phase.PAUSED else snap.phase
        phase_text = _("enfoque") if phase == Phase.FOCUS else _("descanso")
        if self._pausedBySchedule:
            paused = _("Suspendido por horario hasta las {time}. ").format(time=self._scheduleResumeLabel())
        else:
            paused = _("Pausado. ") if snap.phase == Phase.PAUSED else ""
        cycles = _("ciclo {cycle}").format(cycle=snap.cycle)
        if snap.cycles_target:
            cycles = _("ciclo {cycle} de {total}").format(cycle=snap.cycle, total=snap.cycles_target)
        ui.message(
            _("{paused}{phase}, {cycles}. Quedan {duration}.").format(
                paused=paused,
                phase=phase_text,
                cycles=cycles,
                duration=_format_duration(snap.remaining_seconds),
            )
        )
