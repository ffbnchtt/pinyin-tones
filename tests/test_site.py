import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT_DIR / 'site'


class TestDownloadSite(unittest.TestCase):
    def test_static_site_has_required_entrypoints(self):
        for filename in ('index.html', 'styles.css', 'app.js', 'favicon.svg'):
            self.assertTrue((SITE_DIR / filename).is_file(), filename)

    def test_download_page_links_to_all_public_release_assets(self):
        index = (SITE_DIR / 'index.html').read_text(encoding='utf-8')
        expected_assets = (
            'pinyin-tones-windows.zip',
            'pinyin-tones-macos-arm64.dmg',
            'pinyin-tones-macos-x64.dmg',
            'pinyin-tones-macos.zip',
            'pinyin-tones-linux-amd64.deb',
            'pinyin-tones-linux-x86_64.AppImage',
            'pinyin-tones-linux.zip',
            'SHA256SUMS.txt',
        )
        for asset in expected_assets:
            self.assertIn(f'releases/latest/download/{asset}', index)

    def test_site_is_bilingual_without_a_github_api_dependency(self):
        index = (SITE_DIR / 'index.html').read_text(encoding='utf-8')
        script = (SITE_DIR / 'app.js').read_text(encoding='utf-8')
        self.assertIn('data-es=', index)
        self.assertIn('data-en=', index)
        self.assertNotIn('api.github.com', script)

    def test_hero_animates_numeric_pinyin_conversion_accessibly(self):
        index = (SITE_DIR / 'index.html').read_text(encoding='utf-8')
        styles = (SITE_DIR / 'styles.css').read_text(encoding='utf-8')
        script = (SITE_DIR / 'app.js').read_text(encoding='utf-8')

        self.assertIn('Escribí los tonos sin detenerte.', index)
        self.assertIn('class="typing-demo" aria-hidden="true"', index)
        self.assertIn('id="typing-demo-text"', index)
        self.assertIn('Ejemplo: ni3 hao3 se convierte en nǐ hǎo.', index)
        self.assertNotIn('conversion-card', index)
        self.assertIn("{ text: 'ni3'", script)
        self.assertIn("{ text: 'nǐ', delay: 450 }", script)
        self.assertIn("{ text: 'nǐ hao3'", script)
        self.assertIn("{ text: 'nǐ hǎo'", script)
        self.assertLess(script.index("{ text: 'ni3'"), script.index("{ text: 'nǐ', delay: 450 }"))
        self.assertLess(script.index("{ text: 'nǐ hao3'"), script.index("{ text: 'nǐ hǎo'"))
        self.assertIn('border:2px solid var(--accent-soft)', styles)
        self.assertIn("prefers-reduced-motion: reduce", script)
        self.assertIn('@media (prefers-reduced-motion:reduce)', styles)


if __name__ == '__main__':
    unittest.main()
