import unittest
import tempfile
from types import SimpleNamespace
from unittest import mock

from pinyin_app import pinyin_live
from pinyin_app import clipboard as clipboard_mod
from pinyin_app import buffer as buffer_mod
from pinyin_app import keyboard_output as keyboard_output_mod
from pinyin_app.update_check import ReleaseInfo, UpdateState


class TestLiveReplacementFlow(unittest.TestCase):
    def setUp(self):
        pinyin_live.ACTIVE = False
        buffer_mod.SUPPRESS_UNTIL = 0.0
        pinyin_live.CONFIG_DIALOG_OPEN.clear()
        buffer_mod.BUFFER.clear()
        pinyin_live.PRESSED_KEYS = set()
        clipboard_mod.CLIPBOARD_BASELINE = None
        clipboard_mod.CLIPBOARD_RESTORE_TIMER = None
        self.original_replacement_delay = buffer_mod.REPLACEMENT_DELAY
        buffer_mod.REPLACEMENT_DELAY = 0.0
        self.calls = []
        self.clipboard = {'value': 'original'}

        def fake_paste():
            self.calls.append(('paste',))
            return self.clipboard['value']

        def fake_copy(text):
            self.calls.append(('copy', text))
            self.clipboard['value'] = text

        def fake_press_backspace(presses):
            self.calls.append(('press_backspace', presses))

        def fake_paste_shortcut():
            modifier = 'command' if keyboard_output_mod.platform.system() == 'Darwin' else 'ctrl'
            self.calls.append(('keyDown', modifier))
            self.calls.append(('press', 'v'))
            self.calls.append(('keyUp', modifier))

        def fake_type_text(text):
            self.calls.append(('type_text', text))

        self.paste_patch = mock.patch.object(clipboard_mod.pyperclip, 'paste', side_effect=fake_paste)
        self.copy_patch = mock.patch.object(clipboard_mod.pyperclip, 'copy', side_effect=fake_copy)
        self.press_patch = mock.patch.object(buffer_mod, 'press_backspace', side_effect=fake_press_backspace)
        self.paste_shortcut_patch = mock.patch.object(clipboard_mod, 'paste_shortcut', side_effect=fake_paste_shortcut)
        self.type_text_patch = mock.patch.object(clipboard_mod, 'type_text', side_effect=fake_type_text)

        self.paste_patch.start()
        self.copy_patch.start()
        self.press_patch.start()
        self.paste_shortcut_patch.start()
        self.type_text_patch.start()

    def tearDown(self):
        buffer_mod.REPLACEMENT_DELAY = self.original_replacement_delay
        mock.patch.stopall()

    def test_process_buffer_replaces_exact_token(self):
        buffer_mod.BUFFER[:] = list('hao3')
        pinyin_live.process_buffer()
        self.assertEqual(buffer_mod.BUFFER, [])
        self.assertEqual(self.calls[0], ('press_backspace', 4))
        self.assertIn(('copy', 'hǎo'), self.calls)
        self.assertIn(('keyDown', 'ctrl'), self.calls)
        self.assertIn(('press', 'v'), self.calls)
        self.assertIn(('keyUp', 'ctrl'), self.calls)

    def test_delete_last_token_uses_word_delete(self):
        pinyin_live.delete_last_token()
        self.assertIn(('press_backspace', 1), self.calls)

    def test_process_buffer_ignores_non_tokens(self):
        buffer_mod.BUFFER[:] = list('hola')
        pinyin_live.process_buffer()
        self.assertEqual(buffer_mod.BUFFER, list('hola'))
        self.assertNotIn(('keyDown', 'ctrl'), self.calls)

    def test_paste_text_waits_for_clipboard_sync(self):
        clipboard_reads = iter(['original', 'original', 'hǎo'])
        paste_calls = []

        def fake_paste():
            paste_calls.append('paste')
            return next(clipboard_reads)

        def fake_sleep(_seconds):
            return None

        with mock.patch.object(clipboard_mod.pyperclip, 'paste', side_effect=fake_paste), \
             mock.patch.object(clipboard_mod.pyperclip, 'copy') as fake_copy, \
             mock.patch.object(clipboard_mod, 'paste_shortcut') as fake_paste_shortcut, \
             mock.patch.object(clipboard_mod.time, 'sleep', side_effect=fake_sleep):
            pinyin_live.paste_text('hǎo')

        fake_copy.assert_called_with('hǎo')
        fake_paste_shortcut.assert_called_once_with()
        self.assertGreaterEqual(len(paste_calls), 2)

    def test_clipboard_restore_uses_initial_baseline(self):
        timers = []

        class FakeTimer:
            def __init__(self, delay, callback):
                self.delay = delay
                self.callback = callback
                self.cancelled = False
                timers.append(self)

            def start(self):
                return None

            def cancel(self):
                self.cancelled = True

        with mock.patch.object(clipboard_mod.threading, 'Timer', side_effect=FakeTimer), \
             mock.patch.object(clipboard_mod.time, 'sleep', return_value=None):
            pinyin_live.paste_text('zhōng')
            pinyin_live.paste_text('guó')

        self.assertEqual(clipboard_mod.CLIPBOARD_BASELINE, 'original')
        self.assertEqual(len(timers), 2)
        self.assertTrue(timers[0].cancelled)
        timers[-1].callback()
        self.assertEqual(self.clipboard['value'], 'original')

    def test_backspace_pops_one_character(self):
        pinyin_live.ACTIVE = True
        buffer_mod.BUFFER[:] = list('hao')
        pinyin_live.on_type(pinyin_live.keyboard.Key.backspace)
        self.assertEqual(buffer_mod.BUFFER, list('ha'))

    def test_suppression_window_blocks_synthetic_input(self):
        buffer_mod.SUPPRESS_UNTIL = 9999999999
        buffer_mod.BUFFER[:] = list('hao3')
        pinyin_live.on_type(SimpleNamespace(char='x'))
        self.assertEqual(buffer_mod.BUFFER, list('hao3'))

    def test_on_type_accepts_umlaut_vowel_for_live_buffer(self):
        pinyin_live.ACTIVE = True
        buffer_mod.BUFFER.clear()

        pinyin_live.on_type(SimpleNamespace(char='l'))
        pinyin_live.on_type(SimpleNamespace(char='ü'))

        self.assertEqual(buffer_mod.BUFFER, ['l', 'ü'])

    def test_process_buffer_sets_suppression_window(self):
        buffer_mod.BUFFER[:] = list('hao3')
        with mock.patch.object(buffer_mod.time, 'monotonic', return_value=1000.0):
            pinyin_live.process_buffer()
        self.assertGreaterEqual(buffer_mod.SUPPRESS_UNTIL, 1000.0)

    def test_process_buffer_waits_before_replacement_when_delay_configured(self):
        buffer_mod.REPLACEMENT_DELAY = 1.25
        buffer_mod.BUFFER[:] = list('hao3')

        with mock.patch.object(buffer_mod.time, 'sleep') as fake_sleep:
            pinyin_live.process_buffer()

        fake_sleep.assert_any_call(1.25)
        self.assertEqual(self.calls[0], ('press_backspace', 4))

    def test_configuration_dialog_blocks_global_listeners(self):
        pinyin_live.CONFIG_DIALOG_OPEN.set()
        pinyin_live.ACTIVE = True
        buffer_mod.BUFFER[:] = list('hao')

        pinyin_live.on_type(SimpleNamespace(char='a'))

        app = object.__new__(pinyin_live.PinyinApp)
        app.hotkey = '<ctrl>+<alt>+<shift>+p'
        app.hotkey_modifiers, app.hotkey_trigger = pinyin_live.parse_hotkey(app.hotkey)
        toggled = []
        app.toggle_active = lambda: toggled.append(True)

        app._toggle_on_press(pinyin_live.keyboard.Key.ctrl)
        app._toggle_on_press(pinyin_live.keyboard.Key.alt)
        app._toggle_on_press(SimpleNamespace(char='p', name='p'))

        self.assertEqual(buffer_mod.BUFFER, list('hao'))
        self.assertEqual(toggled, [])

    def test_sequence_zhong1_guo2(self):
        outputs = []
        buffer_mod.BUFFER[:] = list('zhong1')
        pinyin_live.process_buffer()
        outputs.extend(self.calls)
        self.calls.clear()
        buffer_mod.BUFFER[:] = list('guo2')
        pinyin_live.process_buffer()
        outputs.extend(self.calls)

        paste_sequences = [call for call in outputs if call == ('press', 'v')]
        self.assertIn(('copy', 'zhōng'), outputs)
        self.assertIn(('copy', 'guó'), outputs)
        self.assertGreaterEqual(len(paste_sequences), 2)

    def test_paste_text_uses_command_on_macos(self):
        with mock.patch.object(keyboard_output_mod.platform, 'system', return_value='Darwin'), \
             mock.patch.object(clipboard_mod, 'paste_shortcut', new=keyboard_output_mod.paste_shortcut), \
             mock.patch.object(keyboard_output_mod.KEYBOARD, 'press') as fake_press, \
             mock.patch.object(keyboard_output_mod.KEYBOARD, 'release') as fake_release, \
             mock.patch.object(keyboard_output_mod.time, 'sleep', return_value=None):
            pinyin_live.paste_text('hǎo')

        fake_press.assert_any_call(keyboard_output_mod.Key.cmd)
        fake_release.assert_any_call(keyboard_output_mod.Key.cmd)

    def test_paste_text_falls_back_to_direct_typing_without_clipboard(self):
        with mock.patch.object(clipboard_mod, 'pyperclip', None):
            pinyin_live.paste_text('hǎo')

        self.assertIn(('type_text', 'hǎo'), self.calls)

    def test_paste_text_falls_back_to_direct_typing_when_clipboard_copy_fails(self):
        with mock.patch.object(clipboard_mod.pyperclip, 'copy', side_effect=RuntimeError('clipboard unavailable')):
            pinyin_live.paste_text('hǎo')

        self.assertIn(('type_text', 'hǎo'), self.calls)
        self.assertNotIn(('keyDown', 'ctrl'), self.calls)


class TestHotkeyCaptureFormatting(unittest.TestCase):
    def test_dialog_run_does_not_start_capture_listener_on_open(self):
        dialog = object.__new__(pinyin_live.HotkeySettingsDialog)
        dialog.root = mock.Mock()
        dialog._build_window = mock.Mock()
        dialog._start_listener = mock.Mock()
        dialog._stop_listener = mock.Mock()
        dialog.logger = mock.Mock()

        pinyin_live.HotkeySettingsDialog.run(dialog)

        dialog._build_window.assert_called_once_with()
        dialog.root.mainloop.assert_called_once_with()
        dialog._start_listener.assert_not_called()
        dialog._stop_listener.assert_called_once_with()

    def test_dialog_start_capture_arms_listener_explicitly(self):
        dialog = object.__new__(pinyin_live.HotkeySettingsDialog)
        button = mock.Mock()
        entry = mock.Mock()
        dialog.capture_button = button
        dialog.capture_entry = entry
        dialog.capture_state = {
            'pressed_keys': {'char:x'},
            'modifiers': {'ctrl'},
            'trigger': 'p',
            'listener': None,
        }
        dialog.capture_var = SimpleNamespace(set=lambda _value: None)
        dialog.status_var = SimpleNamespace(set=lambda _value: None)
        dialog._start_listener = mock.Mock()

        pinyin_live.HotkeySettingsDialog.start_capture(dialog)

        self.assertEqual(dialog.capture_state['pressed_keys'], set())
        self.assertEqual(dialog.capture_state['modifiers'], set())
        self.assertIsNone(dialog.capture_state['trigger'])
        button.configure.assert_called_once_with(state='disabled')
        entry.configure.assert_called_once_with(state='readonly')
        dialog._start_listener.assert_called_once_with()

    def test_format_hotkey_normalizes_modifiers(self):
        self.assertEqual(
            pinyin_live.format_hotkey({'shift', 'ctrl'}, 'P'),
            '<ctrl>+<shift>+p',
        )

    def test_format_hotkey_display_is_human_readable(self):
        self.assertEqual(
            pinyin_live.format_hotkey_display({'shift', 'ctrl'}, 'p'),
            'Ctrl+Shift+P',
        )

    def test_normalize_tk_keys(self):
        self.assertEqual(
            pinyin_live.normalize_capture_key(SimpleNamespace(keysym='Control_L')),
            'ctrl',
        )
        self.assertEqual(
            pinyin_live.normalize_trigger_key(SimpleNamespace(keysym='P')),
            'p',
        )
        self.assertIsNone(
            pinyin_live.normalize_trigger_key(SimpleNamespace(keysym='F12')),
        )
        self.assertIsNone(pinyin_live.normalize_trigger_key(SimpleNamespace(keysym='Control_L')))

    def test_pynput_trigger_key_accepts_special_keys(self):
        self.assertIsNone(
            pinyin_live.normalize_pynput_trigger_key(SimpleNamespace(char=None, name='f12')),
        )
        self.assertEqual(
            pinyin_live.normalize_pynput_trigger_key(SimpleNamespace(char=None, name=None, vk=80)),
            'p',
        )
        self.assertIsNone(
            pinyin_live.normalize_pynput_trigger_key(SimpleNamespace(char=None, name='ctrl_l', vk=162)),
        )

    def test_toggle_uses_configured_letter_trigger(self):
        app = object.__new__(pinyin_live.PinyinApp)
        app.hotkey = '<ctrl>+<shift>+p'
        app.hotkey_modifiers, app.hotkey_trigger = pinyin_live.parse_hotkey(app.hotkey)

        triggered = []

        def fake_toggle_active():
            triggered.append(True)

        app.toggle_active = fake_toggle_active

        pinyin_live.PRESSED_KEYS.clear()
        app._toggle_on_press(SimpleNamespace(char='p', name='p', vk=80))
        app._toggle_on_press(pinyin_live.keyboard.Key.ctrl)
        app._toggle_on_press(pinyin_live.keyboard.Key.shift)

        self.assertTrue(triggered)

    def test_dialog_captures_single_key_without_sticky_modifiers(self):
        dialog = object.__new__(pinyin_live.HotkeySettingsDialog)
        dialog.capture_state = {
            'pressed_keys': set(),
            'modifiers': set(),
            'trigger': None,
            'listener': None,
        }
        dialog.capture_var = SimpleNamespace(set=lambda _value: None)
        dialog.status_var = SimpleNamespace(set=lambda _value: None)
        dialog._schedule_ui = lambda callback: callback()

        pinyin_live.HotkeySettingsDialog.on_capture_press(dialog, SimpleNamespace(char='p', name='p', vk=80))
        pinyin_live.HotkeySettingsDialog.on_capture_release(dialog, SimpleNamespace(char='p', name='p', vk=80))

        self.assertEqual(dialog.capture_state['modifiers'], set())
        self.assertEqual(dialog.capture_state['trigger'], 'p')

    def test_dialog_stops_capture_after_completed_chord(self):
        dialog = object.__new__(pinyin_live.HotkeySettingsDialog)
        dialog.capture_state = {
            'pressed_keys': {'char:p'},
            'modifiers': {'ctrl'},
            'trigger': 'p',
            'listener': None,
        }
        dialog._schedule_ui = lambda callback: callback()
        dialog._stop_listener = mock.Mock()

        pinyin_live.HotkeySettingsDialog.on_capture_release(dialog, SimpleNamespace(char='p', name='p', vk=80))

        dialog._stop_listener.assert_called_once_with()

    def test_dialog_stop_listener_disables_capture_entry(self):
        listener = mock.Mock()
        button = mock.Mock()
        entry = mock.Mock()
        dialog = object.__new__(pinyin_live.HotkeySettingsDialog)
        dialog.capture_button = button
        dialog.capture_entry = entry
        dialog.capture_state = {
            'pressed_keys': {'char:p'},
            'modifiers': {'ctrl'},
            'trigger': 'p',
            'listener': listener,
        }

        pinyin_live.HotkeySettingsDialog._stop_listener(dialog)

        listener.stop.assert_called_once_with()
        self.assertIsNone(dialog.capture_state['listener'])
        self.assertEqual(dialog.capture_state['pressed_keys'], set())
        entry.configure.assert_called_once_with(state='disabled')
        button.configure.assert_called_once_with(state='normal')

    def test_dialog_captures_multi_key_chord_and_resets_between_sequences(self):
        dialog = object.__new__(pinyin_live.HotkeySettingsDialog)
        dialog.capture_state = {
            'pressed_keys': set(),
            'modifiers': set(),
            'trigger': None,
            'listener': None,
        }
        dialog.capture_var = SimpleNamespace(set=lambda _value: None)
        dialog.status_var = SimpleNamespace(set=lambda _value: None)
        dialog._schedule_ui = lambda callback: callback()

        pinyin_live.HotkeySettingsDialog.on_capture_press(dialog, pinyin_live.keyboard.Key.ctrl)
        pinyin_live.HotkeySettingsDialog.on_capture_press(dialog, pinyin_live.keyboard.Key.alt)
        pinyin_live.HotkeySettingsDialog.on_capture_press(dialog, SimpleNamespace(char='p', name='p', vk=80))
        pinyin_live.HotkeySettingsDialog.on_capture_release(dialog, SimpleNamespace(char='p', name='p', vk=80))
        pinyin_live.HotkeySettingsDialog.on_capture_release(dialog, pinyin_live.keyboard.Key.alt)
        pinyin_live.HotkeySettingsDialog.on_capture_release(dialog, pinyin_live.keyboard.Key.ctrl)

        self.assertEqual(dialog.capture_state['modifiers'], {'ctrl', 'alt'})
        self.assertEqual(dialog.capture_state['trigger'], 'p')

        pinyin_live.HotkeySettingsDialog.on_capture_press(dialog, SimpleNamespace(char='f', name='f', vk=70))
        pinyin_live.HotkeySettingsDialog.on_capture_release(dialog, SimpleNamespace(char='f', name='f', vk=70))

        self.assertEqual(dialog.capture_state['modifiers'], set())
        self.assertEqual(dialog.capture_state['trigger'], 'f')

    def test_dialog_enter_confirms_without_becoming_trigger(self):
        dialog = object.__new__(pinyin_live.HotkeySettingsDialog)
        dialog.capture_state = {
            'pressed_keys': set(),
            'modifiers': {'ctrl', 'alt'},
            'trigger': 'p',
            'listener': None,
        }
        dialog.capture_var = SimpleNamespace(set=lambda _value: None)
        dialog.status_var = SimpleNamespace(set=lambda _value: None)
        dialog._schedule_ui = lambda callback: callback()
        saved = []
        dialog.save = lambda: saved.append(True)
        dialog.cancel = lambda: None

        pinyin_live.HotkeySettingsDialog.on_capture_press(dialog, pinyin_live.keyboard.Key.enter)

        self.assertEqual(saved, [True])
        self.assertEqual(dialog.capture_state['trigger'], 'p')


class TestAutostartHelpers(unittest.TestCase):
    def test_get_launch_command_args_prefers_frozen_executable(self):
        with mock.patch.object(pinyin_live.sys, 'frozen', True, create=True):
            args = pinyin_live.get_launch_command_args()
        self.assertEqual(args, [pinyin_live.os.path.abspath(pinyin_live.sys.executable)])

    def test_build_linux_desktop_entry_uses_exec_line(self):
        with mock.patch.object(pinyin_live, 'get_launch_command_args', return_value=['/opt/pinyin/pinyin_tones', '--flag']):
            desktop_entry = pinyin_live.build_linux_desktop_entry()
        self.assertIn('Name=Pinyin Tones', desktop_entry)
        self.assertIn('Exec=/bin/sh -c', desktop_entry)
        self.assertIn('/opt/pinyin/pinyin_tones --flag', desktop_entry)
        self.assertIn('X-GNOME-Autostart-enabled=true', desktop_entry)

    def test_build_macos_launch_agent_plist_contains_program_arguments(self):
        with mock.patch.object(pinyin_live, 'get_launch_command_args', return_value=['/Applications/Pinyin.app/Contents/MacOS/pinyin_tones']):
            plist_data = pinyin_live.build_macos_launch_agent_plist()
        self.assertEqual(plist_data['Label'], 'com.federico.pinyin-tones')
        self.assertEqual(plist_data['ProgramArguments'][0], '/bin/sh')
        self.assertEqual(plist_data['ProgramArguments'][1], '-c')
        self.assertIn('/Applications/Pinyin.app/Contents/MacOS/pinyin_tones', plist_data['ProgramArguments'][2])
        self.assertTrue(plist_data['RunAtLoad'])

    def test_sync_autostart_setting_dispatches_by_platform(self):
        with mock.patch.object(pinyin_live.platform, 'system', return_value='Linux'), \
             mock.patch.object(pinyin_live, 'set_linux_autostart') as fake_linux, \
             mock.patch.object(pinyin_live, 'set_windows_autostart') as fake_windows, \
             mock.patch.object(pinyin_live, 'set_macos_autostart') as fake_macos:
            result = pinyin_live.sync_autostart_setting(True)

        self.assertTrue(result)
        fake_linux.assert_called_once_with(True)
        fake_windows.assert_not_called()
        fake_macos.assert_not_called()

    def test_windows_autostart_command_is_compact_and_self_cleaning(self):
        config = pinyin_live.build_autostart_config()
        cmd = pinyin_live._autostart.get_windows_autostart_command(config)

        self.assertTrue(cmd.startswith('cmd /c for %i in ("'))
        self.assertIn('@if exist %~fi (start "" %~fi)', cmd)
        self.assertIn('reg delete HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run', cmd)
        self.assertIn('/v "Pinyin Tones" /f', cmd)
        # Windows Run entries have a practical command length limit near MAX_PATH.
        self.assertLessEqual(len(cmd), 260)


class TestSingleInstanceGuard(unittest.TestCase):
    def test_single_instance_lock_rejects_second_acquire_until_released(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            lock_path = pinyin_live.os.path.join(tmp_dir, "pinyin-tones.lock")
            first = pinyin_live.SingleInstanceLock(lock_path)
            second = pinyin_live.SingleInstanceLock(lock_path)

            self.assertTrue(first.acquire())
            try:
                self.assertFalse(second.acquire())
            finally:
                first.release()

            try:
                self.assertTrue(second.acquire())
            finally:
                second.release()

    def test_main_exits_before_startup_when_another_instance_is_running(self):
        class BusyLock:
            def __init__(self, _path):
                pass

            def __enter__(self):
                return None

            def __exit__(self, _exc_type, _exc, _tb):
                return None

        with mock.patch.object(pinyin_live, "SingleInstanceLock", BusyLock), \
             mock.patch.object(pinyin_live, "_run_main_loop") as fake_run:
            pinyin_live.main()

        fake_run.assert_not_called()

    def test_main_runs_when_single_instance_lock_is_acquired(self):
        class AcquiredLock:
            def __init__(self, _path):
                pass

            def __enter__(self):
                return self

            def __exit__(self, _exc_type, _exc, _tb):
                return None

        with mock.patch.object(pinyin_live, "SingleInstanceLock", AcquiredLock), \
             mock.patch.object(pinyin_live, "_run_main_loop") as fake_run:
            pinyin_live.main()

        fake_run.assert_called_once_with()


class TestStartupFailureHandling(unittest.TestCase):
    def setUp(self):
        pinyin_live.STOP_REQUESTED.clear()

    def tearDown(self):
        pinyin_live.STOP_REQUESTED.clear()
        mock.patch.stopall()

    def test_start_stops_started_listener_when_later_listener_fails(self):
        class FakeListener:
            def __init__(self, fail=False):
                self.fail = fail
                self.started = False
                self.stopped = False

            def start(self):
                if self.fail:
                    raise RuntimeError("listener unavailable")
                self.started = True

            def stop(self):
                self.stopped = True

        app = object.__new__(pinyin_live.PinyinApp)
        app.autostart_enabled = False
        app.autostart_config = pinyin_live.build_autostart_config()
        app.type_listener = FakeListener()
        app.toggle_listener = FakeListener(fail=True)
        app.icon = None
        app.request_update_check = mock.Mock()

        with self.assertRaises(RuntimeError):
            pinyin_live.PinyinApp.start(app)

        self.assertTrue(app.type_listener.started)
        self.assertTrue(app.type_listener.stopped)
        self.assertTrue(app.toggle_listener.stopped)
        app.request_update_check.assert_not_called()

    def test_tray_failure_requests_shutdown(self):
        app = object.__new__(pinyin_live.PinyinApp)
        app._run_tray = mock.Mock(side_effect=RuntimeError("tray unavailable"))

        pinyin_live.PinyinApp._run_tray_safe(app)

        self.assertTrue(pinyin_live.STOP_REQUESTED.is_set())

    def test_run_main_loop_shows_startup_error_when_start_fails(self):
        app = mock.Mock()
        app.hotkey = pinyin_live.DEFAULT_HOTKEY
        app.hotkey_modifiers, app.hotkey_trigger = pinyin_live.parse_hotkey(app.hotkey)
        app.start.side_effect = RuntimeError("listener unavailable")

        with mock.patch.object(pinyin_live, "PinyinApp", return_value=app), \
             mock.patch.object(pinyin_live, "show_startup_error") as fake_error:
            pinyin_live._run_main_loop()

        fake_error.assert_called_once()
        app.stop.assert_not_called()


class TestUpdateController(unittest.TestCase):
    def test_apply_available_update_requests_dialog_and_refreshes_menu(self):
        app = object.__new__(pinyin_live.PinyinApp)
        app.config = dict(pinyin_live.DEFAULT_CONFIG)
        app.icon = mock.Mock()
        app.update_lock = pinyin_live.threading.Lock()
        app.update_state = UpdateState(status="idle")

        state = UpdateState(
            status="available",
            latest_release=ReleaseInfo(
                version="0.2.0",
                tag="v0.2.0",
                html_url="https://example/release",
                asset_name="pinyin-tones-windows.zip",
                asset_url="https://example/file.zip",
                published_at=None,
            ),
        )

        pinyin_live.UPDATE_DIALOG_REQUESTED.clear()
        app._set_update_state(state)
        if app._should_prompt_for_update(state):
            pinyin_live.UPDATE_DIALOG_REQUESTED.set()

        self.assertTrue(pinyin_live.UPDATE_DIALOG_REQUESTED.is_set())
        app.icon.update_menu.assert_called_once_with()

    def test_should_prompt_for_update_respects_dismissed_version(self):
        app = object.__new__(pinyin_live.PinyinApp)
        app.config = dict(pinyin_live.DEFAULT_CONFIG)

        state = UpdateState(
            status="available",
            latest_release=ReleaseInfo(
                version="0.2.0",
                tag="v0.2.0",
                html_url="https://example/release",
                asset_name=None,
                asset_url=None,
                published_at=None,
            ),
        )

        self.assertTrue(app._should_prompt_for_update(state))
        self.assertTrue(app._should_prompt_for_update(state, force_prompt=True))

    def test_can_download_update_when_release_asset_exists(self):
        app = object.__new__(pinyin_live.PinyinApp)
        app.update_lock = pinyin_live.threading.Lock()
        app.update_state = UpdateState(
            status="available",
            latest_release=ReleaseInfo(
                version="0.2.0",
                tag="v0.2.0",
                html_url="https://example/release",
                asset_name="pinyin-tones-windows.zip",
                asset_url="https://example/file.zip",
                published_at=None,
            ),
        )
        self.assertTrue(app._can_download_update())

    def test_update_status_label_reflects_downloaded_update(self):
        app = object.__new__(pinyin_live.PinyinApp)
        app.config = dict(pinyin_live.DEFAULT_CONFIG)
        app.update_lock = pinyin_live.threading.Lock()
        app.update_state = UpdateState(
            status="available",
            latest_release=ReleaseInfo(
                version="0.2.0",
                tag="v0.2.0",
                html_url="https://example/release",
                asset_name="pinyin-tones-windows.zip",
                asset_url="https://example/file.zip",
                published_at=None,
            ),
            downloaded_path="C:/tmp/pinyin-tones-windows.zip",
        )
        self.assertEqual(
            app._update_status_label(),
            "Actualización descargada: v0.2.0",
        )

    def test_update_status_label_is_descriptive_before_first_check(self):
        app = object.__new__(pinyin_live.PinyinApp)
        app.config = dict(pinyin_live.DEFAULT_CONFIG)
        app.update_lock = pinyin_live.threading.Lock()
        app.update_state = UpdateState(status="idle")

        self.assertEqual(
            app._update_status_label(),
            "Actualizado",
        )
        self.assertEqual(
            app._update_menu_label(),
            "Actualizado",
        )


if __name__ == '__main__':
    unittest.main()
