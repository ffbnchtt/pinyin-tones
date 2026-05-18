import unittest
from types import SimpleNamespace
from unittest import mock

from pinyin_app.src import pinyin_live


class TestLiveReplacementFlow(unittest.TestCase):
    def setUp(self):
        pinyin_live.ACTIVE = False
        pinyin_live.SUPPRESS_INPUT = False
        pinyin_live.SUPPRESS_UNTIL = 0.0
        pinyin_live.BUFFER = []
        pinyin_live.CLIPBOARD_BASELINE = None
        pinyin_live.CLIPBOARD_RESTORE_TIMER = None
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

        self.paste_patch = mock.patch.object(pinyin_live.pyperclip, 'paste', side_effect=fake_paste)
        self.copy_patch = mock.patch.object(pinyin_live.pyperclip, 'copy', side_effect=fake_copy)
        self.hotkey_patch = mock.patch.object(pinyin_live.pyautogui, 'hotkey', side_effect=fake_hotkey)
        self.press_patch = mock.patch.object(pinyin_live.pyautogui, 'press', side_effect=fake_press)

        self.paste_patch.start()
        self.copy_patch.start()
        self.hotkey_patch.start()
        self.press_patch.start()

    def tearDown(self):
        mock.patch.stopall()

    def test_process_buffer_replaces_exact_token(self):
        pinyin_live.BUFFER = list('hao3')
        pinyin_live.process_buffer()
        self.assertEqual(pinyin_live.BUFFER, [])
        self.assertEqual(self.calls[0], ('press', 'backspace', 4, 0))
        self.assertIn(('copy', 'hǎo'), self.calls)
        self.assertIn(('hotkey', ('ctrl', 'v')), self.calls)

    def test_delete_last_token_uses_word_delete(self):
        pinyin_live.delete_last_token()
        self.assertIn(('press', 'backspace', 1, 0), self.calls)

    def test_process_buffer_ignores_non_tokens(self):
        pinyin_live.BUFFER = list('hola')
        pinyin_live.process_buffer()
        self.assertEqual(pinyin_live.BUFFER, list('hola'))
        self.assertNotIn(('hotkey', ('ctrl', 'v')), self.calls)

    def test_paste_text_waits_for_clipboard_sync(self):
        clipboard_reads = iter(['original', 'original', 'hǎo'])
        paste_calls = []

        def fake_paste():
            paste_calls.append('paste')
            return next(clipboard_reads)

        def fake_sleep(_seconds):
            return None

        with mock.patch.object(pinyin_live.pyperclip, 'paste', side_effect=fake_paste), \
             mock.patch.object(pinyin_live.pyperclip, 'copy') as fake_copy, \
             mock.patch.object(pinyin_live.pyautogui, 'hotkey') as fake_hotkey, \
             mock.patch.object(pinyin_live.time, 'sleep', side_effect=fake_sleep):
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

        with mock.patch.object(pinyin_live.threading, 'Timer', side_effect=FakeTimer), \
             mock.patch.object(pinyin_live.time, 'sleep', return_value=None):
            pinyin_live.paste_text('zhōng')
            pinyin_live.paste_text('guó')

        self.assertEqual(pinyin_live.CLIPBOARD_BASELINE, 'original')
        self.assertEqual(len(timers), 2)
        self.assertTrue(timers[0].cancelled)
        timers[-1].callback()
        self.assertEqual(self.clipboard['value'], 'original')

    def test_backspace_pops_one_character(self):
        pinyin_live.ACTIVE = True
        pinyin_live.BUFFER = list('hao')
        pinyin_live.on_type(pinyin_live.keyboard.Key.backspace)
        self.assertEqual(pinyin_live.BUFFER, list('ha'))

    def test_suppression_window_blocks_synthetic_input(self):
        pinyin_live.SUPPRESS_UNTIL = 9999999999
        pinyin_live.BUFFER = list('hao3')
        pinyin_live.on_type(SimpleNamespace(char='x'))
        self.assertEqual(pinyin_live.BUFFER, list('hao3'))

    def test_sequence_zhong1_guo2(self):
        outputs = []
        pinyin_live.BUFFER = list('zhong1')
        pinyin_live.process_buffer()
        outputs.extend(self.calls)
        self.calls.clear()
        pinyin_live.BUFFER = list('guo2')
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

    def test_normalize_tk_keys(self):
        self.assertEqual(
            pinyin_live.normalize_capture_key(SimpleNamespace(keysym='Control_L')),
            'ctrl',
        )
        self.assertEqual(
            pinyin_live.normalize_trigger_key(SimpleNamespace(char='P')),
            'p',
        )
        self.assertIsNone(pinyin_live.normalize_trigger_key(SimpleNamespace(char='-')))


if __name__ == '__main__':
    unittest.main()
