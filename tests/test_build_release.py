import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import build_release


class TestBuildReleaseHelpers(unittest.TestCase):
    def test_normalize_platform_name_maps_python_platform_values(self):
        self.assertEqual(build_release.normalize_platform_name('Darwin'), 'macos')
        self.assertEqual(build_release.normalize_platform_name('Windows'), 'windows')
        self.assertEqual(build_release.normalize_platform_name('Linux'), 'linux')

    def test_build_pyinstaller_command_windows_uses_ico(self):
        icon_assets = {'ico': Path('C:/tmp/pinyin_app.ico'), 'icns': Path('C:/tmp/pinyin_app.icns'), 'png': Path('C:/tmp/pinyin_app.png')}
        command = build_release.build_pyinstaller_command('windows', icon_assets)
        self.assertIn('--noconsole', command)
        self.assertIn('--icon', command)
        self.assertIn(str(icon_assets['ico']), command)

    def test_build_pyinstaller_command_macos_uses_icns(self):
        icon_assets = {'ico': Path('C:/tmp/pinyin_app.ico'), 'icns': Path('C:/tmp/pinyin_app.icns'), 'png': Path('C:/tmp/pinyin_app.png')}
        command = build_release.build_pyinstaller_command('macos', icon_assets)
        self.assertIn('--windowed', command)
        self.assertIn(str(icon_assets['icns']), command)

    def test_build_pyinstaller_command_linux_has_no_icon_flag(self):
        icon_assets = {'ico': Path('C:/tmp/pinyin_app.ico'), 'icns': Path('C:/tmp/pinyin_app.icns'), 'png': Path('C:/tmp/pinyin_app.png')}
        command = build_release.build_pyinstaller_command('linux', icon_assets)
        self.assertIn('--noconsole', command)
        self.assertNotIn('--icon', command)

    def test_build_pyinstaller_env_sets_windows_tcl_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tcl_root = Path(temp_dir) / 'tcl'
            tcl_library = tcl_root / 'tcl8.6'
            tk_library = tcl_root / 'tk8.6'
            tcl_library.mkdir(parents=True)
            tk_library.mkdir(parents=True)

            with mock.patch.object(build_release.sys, 'base_prefix', temp_dir), \
                 mock.patch.dict(build_release.os.environ, {}, clear=True):
                env = build_release.build_pyinstaller_env('windows')

            self.assertEqual(env['TCL_LIBRARY'], str(tcl_library))
            self.assertEqual(env['TK_LIBRARY'], str(tk_library))

    def test_build_icon_assets_produces_png_and_ico(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch.object(build_release, 'ASSET_DIR', Path(temp_dir)):
                assets = build_release.ensure_icon_assets()

            self.assertTrue(assets['png'].exists())
            self.assertTrue(assets['ico'].exists())
            self.assertTrue(assets['icns'].exists())

    def test_copy_release_payload_includes_docs_and_icon(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            fake_artifact = temp_path / 'pinyin_app.exe'
            fake_artifact.write_text('binary', encoding='utf-8')
            fake_license = temp_path / 'LICENSE'
            fake_license.write_text('license', encoding='utf-8')
            fake_guide = temp_path / 'USER_GUIDE.md'
            fake_guide.write_text('guide', encoding='utf-8')
            fake_png = temp_path / 'pinyin_app.png'
            fake_png.write_text('png', encoding='utf-8')
            fake_ico = temp_path / 'pinyin_app.ico'
            fake_ico.write_text('ico', encoding='utf-8')
            fake_icns = temp_path / 'pinyin_app.icns'
            fake_icns.write_text('icns', encoding='utf-8')

            with mock.patch.object(build_release, 'RELEASE_DIR', temp_path / 'release'), \
                 mock.patch.object(build_release, 'LICENSE_SOURCE', fake_license), \
                 mock.patch.object(build_release, 'USER_GUIDE_SOURCE', fake_guide):
                release_dir = build_release.copy_release_payload(
                    'windows',
                    fake_artifact,
                    {'png': fake_png, 'ico': fake_ico, 'icns': fake_icns},
                )

            self.assertTrue((release_dir / 'pinyin_app.exe').exists())
            self.assertTrue((release_dir / 'LICENSE').exists())
            self.assertTrue((release_dir / 'USER_GUIDE.md').exists())
            self.assertTrue((release_dir / 'pinyin_app.png').exists())
            self.assertTrue((release_dir / 'pinyin_app.ico').exists())


if __name__ == '__main__':
    unittest.main()
