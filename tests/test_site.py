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


if __name__ == '__main__':
    unittest.main()
