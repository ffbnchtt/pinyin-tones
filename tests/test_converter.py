import unittest

from pinyin_app.pinyin_converter import convert_pinyin_token, has_vowel


class TestPinyinConverter(unittest.TestCase):
    def test_standard_tones(self):
        self.assertEqual(convert_pinyin_token('ni3'), 'nǐ')
        self.assertEqual(convert_pinyin_token('hao3'), 'hǎo')
        self.assertEqual(convert_pinyin_token('hua2'), 'huá')

    def test_umlaut_support(self):
        self.assertEqual(convert_pinyin_token('lü4'), 'lǜ')
        self.assertEqual(convert_pinyin_token('Lü4'), 'Lǜ')

    def test_special_rules(self):
        self.assertEqual(convert_pinyin_token('liu3'), 'liǔ')
        self.assertEqual(convert_pinyin_token('hui4'), 'huì')
        self.assertEqual(convert_pinyin_token('ma5'), 'ma5')

    def test_non_matching_tokens(self):
        self.assertEqual(convert_pinyin_token('abc'), 'abc')
        self.assertEqual(convert_pinyin_token('ni3x'), 'ni3x')

    def test_vowel_detection(self):
        self.assertTrue(has_vowel('lu'))
        self.assertTrue(has_vowel('lü'))
        self.assertFalse(has_vowel('rhythms'))


if __name__ == '__main__':
    unittest.main()
