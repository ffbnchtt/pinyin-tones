import unittest
from types import SimpleNamespace
from unittest import mock

from pinyin_app import pinyin_live
from pinyin_app import clipboard as clipboard_mod
from pinyin_app import buffer as buffer_mod


class TestLiveReplacementFlow(unittest.TestCase):
    def setUp(self):
        pinyin_live.ACTIVE = False
        buffer_mod.SUPPRESS_UNTIL = 0.0
        pinyin_live.CONFIG_DIALOG_OPEN.clear()
        buffer_mod.BUFFER.clear()
        pinyin_live.PRESSED_KEYS = set()
        clipboard_mod.CLIPBOARD_BASELINE = None
        clipboard_mod.CLIPBOARD_RESTORE_TIMER = None
        self.calls = []
        self.clipboard = {'value': 'original'}

        def fake_paste():
            self.calls.append(('paste',))
            return self.clipboard['value']

        def fake_copy(text):
            self.calls.append(('copy', text))
            self.clipboard['value'] = text

        def fake_hotkey(*keys):
            self.calls.append(('hotkey', keys))

        def fake_press(key, presses=1, interval=0.0):
            self.calls.append(('press', key, presses, interval))

        self.paste_patch = mock.patch.object(clipboard_mod.pyperclip, 'paste', side_effect=fake_paste)
        self.copy_patch = mock.patch.object(clipboard_mod.pyperclip, 'copy', side_effect=fake_copy)
        self.hotkey_patch = mock.patch.object(clipboard_mod.pyautogui, 'hotkey', side_effect=fake_hotkey)
        self.press_patch = mock.patch.object(buffer_mod.pyautogui, 'press', side_effect=fake_press)

        self.paste_patch.start()
        self.copy_patch.start()
        self.hotkey_patch.start()
        self.press_patch.start()

    def tearDown(self):
        mock.patch.stopall()

    def test_process_buffer_replaces_exact_token(self):
        buffer_mod.BUFFER[:] = list('hao3')
        pinyin_live.process_buffer()
        self.assertEqual(buffer_mod.BUFFER, [])
        self.assertEqual(self.calls[0], ('press', 'backspace', 4, 0))
        self.assertIn(('copy', 'hǎo'), self.calls)
        self.assertIn(('hotkey', ('ctrl', 'v')), self.calls)

    def test_delete_last_token_uses_word_delete(self):
        pinyin_live.delete_last_token()
        self.assertIn(('press', 'backspace', 1, 0), self.calls)

    def test_process_buffer_ignores_non_tokens(self):
        buffer_mod.BUFFER[:] = list('hola')
        pinyin_live.process_buffer()
        self.assertEqual(buffer_mod.BUFFER, list('hola'))
        self.assertNotIn(('hotkey', ('ctrl', 'v')), self.calls)

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
             mock.patch.object(clipboard_mod.pyautogui, 'hotkey') as fake_hotkey, \
             mock.patch.object(clipboard_mod.time, 'sleep', side_effect=fake_sleep):
            pinyin_live.paste_text('hǎo')

        fake_copy.assert_called_with('hǎo')
        fake_hotkey.assert_called_once_with('ctrl', 'v')
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

    def test_process_buffer_sets_suppression_window(self):
        buffer_mod.BUFFER[:] = list('hao3')
        with mock.patch.object(buffer_mod.time, 'monotonic', return_value=1000.0):
            pinyin_live.process_buffer()
        self.assertGreaterEqual(buffer_mod.SUPPRESS_UNTIL, 1000.0)

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

        hotkeys = [call for call in outputs if call[0] == 'hotkey']
        self.assertIn(('copy', 'zhōng'), outputs)
        self.assertIn(('copy', 'guó'), outputs)
        self.assertGreaterEqual(len(hotkeys), 2)


class TestHotkeyCaptureFormatting(unittest.TestCase):
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
        with mock.patch.object(pinyin_live, 'get_launch_command_args', return_value=['/opt/pinyin/pinyin_app', '--flag']):
            desktop_entry = pinyin_live.build_linux_desktop_entry()
        self.assertIn('Name=Pinyin Tones', desktop_entry)
        self.assertIn('Exec=/bin/sh -c', desktop_entry)
        self.assertIn('/opt/pinyin/pinyin_app --flag', desktop_entry)
        self.assertIn('X-GNOME-Autostart-enabled=true', desktop_entry)

    def test_build_macos_launch_agent_plist_contains_program_arguments(self):
        with mock.patch.object(pinyin_live, 'get_launch_command_args', return_value=['/Applications/Pinyin.app/Contents/MacOS/pinyin_app']):
            plist_data = pinyin_live.build_macos_launch_agent_plist()
        self.assertEqual(plist_data['Label'], 'com.federico.pinyin-tones')
        self.assertEqual(plist_data['ProgramArguments'][0], '/bin/sh')
        self.assertEqual(plist_data['ProgramArguments'][1], '-c')
        self.assertIn('/Applications/Pinyin.app/Contents/MacOS/pinyin_app', plist_data['ProgramArguments'][2])
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


if __name__ == '__main__':
    unittest.main()
