import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from tools import build_release


class TestBuildReleaseHelpers(unittest.TestCase):
    def test_normalize_platform_name_maps_python_platform_values(self):
        self.assertEqual(build_release.normalize_platform_name('Darwin'), 'macos')
        self.assertEqual(build_release.normalize_platform_name('Windows'), 'windows')
        self.assertEqual(build_release.normalize_platform_name('Linux'), 'linux')

    def test_build_pyinstaller_command_windows_uses_ico(self):
        icon_assets = {'ico': Path('C:/tmp/pinyin_tones.ico'), 'icns': Path('C:/tmp/pinyin_tones.icns'), 'png': Path('C:/tmp/pinyin_tones.png')}
        with mock.patch.object(build_release, 'build_windows_tk_options', return_value=['--tk-options']):
            command = build_release.build_pyinstaller_command('windows', icon_assets)
        self.assertIn('--noconsole', command)
        self.assertIn('pinyin_tones', command)
        self.assertIn('--icon', command)
        self.assertIn(str(icon_assets['ico']), command)
        self.assertIn('--tk-options', command)

    def test_build_pyinstaller_command_macos_uses_icns(self):
        icon_assets = {'ico': Path('C:/tmp/pinyin_tones.ico'), 'icns': Path('C:/tmp/pinyin_tones.icns'), 'png': Path('C:/tmp/pinyin_tones.png')}
        command = build_release.build_pyinstaller_command('macos', icon_assets)
        self.assertIn('--windowed', command)
        self.assertIn('pinyin_tones', command)
        self.assertIn(str(icon_assets['icns']), command)

    def test_build_pyinstaller_command_linux_has_no_icon_flag(self):
        icon_assets = {'ico': Path('C:/tmp/pinyin_tones.ico'), 'icns': Path('C:/tmp/pinyin_tones.icns'), 'png': Path('C:/tmp/pinyin_tones.png')}
        command = build_release.build_pyinstaller_command('linux', icon_assets)
        self.assertIn('--noconsole', command)
        self.assertIn('pinyin_tones', command)
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
            fake_artifact = temp_path / 'pinyin_tones.exe'
            fake_artifact.write_text('binary', encoding='utf-8')
            fake_license = temp_path / 'LICENSE'
            fake_license.write_text('license', encoding='utf-8')
            fake_guide = temp_path / 'USER_GUIDE.md'
            fake_guide.write_text('guide', encoding='utf-8')
            fake_png = temp_path / 'pinyin_tones.png'
            fake_png.write_text('png', encoding='utf-8')
            fake_ico = temp_path / 'pinyin_tones.ico'
            fake_ico.write_text('ico', encoding='utf-8')
            fake_icns = temp_path / 'pinyin_tones.icns'
            fake_icns.write_text('icns', encoding='utf-8')

            with mock.patch.object(build_release, 'RELEASE_DIR', temp_path / 'release'), \
                 mock.patch.object(build_release, 'LICENSE_SOURCE', fake_license), \
                 mock.patch.object(build_release, 'USER_GUIDE_SOURCE', fake_guide):
                release_dir = build_release.copy_release_payload(
                    'windows',
                    fake_artifact,
                    {'png': fake_png, 'ico': fake_ico, 'icns': fake_icns},
                )

            self.assertTrue((release_dir / 'pinyin_tones.exe').exists())
            self.assertTrue((release_dir / 'LICENSE').exists())
            self.assertTrue((release_dir / 'USER_GUIDE.md').exists())
            self.assertTrue((release_dir / 'pinyin_tones.png').exists())
            self.assertTrue((release_dir / 'pinyin_tones.ico').exists())

    def test_remove_standalone_artifact_deletes_dist_file_after_payload_copy(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            artifact_path = temp_path / 'pinyin_tones.exe'
            artifact_path.write_text('binary', encoding='utf-8')
            release_dir = temp_path / 'pinyin_tones_release' / 'windows'
            release_dir.mkdir(parents=True)

            with mock.patch.object(build_release, 'DIST_DIR', temp_path):
                build_release.remove_standalone_artifact(artifact_path, release_dir)

            self.assertFalse(artifact_path.exists())

    def test_remove_standalone_artifact_keeps_release_payload_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            release_dir = temp_path / 'pinyin_tones_release' / 'windows'
            release_dir.mkdir(parents=True)
            artifact_path = release_dir / 'pinyin_tones.exe'
            artifact_path.write_text('binary', encoding='utf-8')

            with mock.patch.object(build_release, 'DIST_DIR', temp_path):
                build_release.remove_standalone_artifact(artifact_path, release_dir)

            self.assertTrue(artifact_path.exists())

    def test_create_release_archive_uses_stable_asset_name_and_flat_contents(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            release_dir = temp_path / 'pinyin_tones_release' / 'windows'
            release_dir.mkdir(parents=True)
            (release_dir / 'pinyin_tones.exe').write_text('binary', encoding='utf-8')
            (release_dir / 'LICENSE').write_text('license', encoding='utf-8')

            with mock.patch.object(build_release, 'DIST_DIR', temp_path):
                archive_path = build_release.create_release_archive('windows', release_dir)

            self.assertEqual(archive_path, temp_path / 'pinyin-tones-windows.zip')
            with zipfile.ZipFile(archive_path) as archive:
                self.assertEqual(
                    sorted(archive.namelist()),
                    [
                        'LICENSE',
                        'pinyin_tones.exe',
                    ],
                )

    def test_create_release_archive_replaces_existing_archive(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            release_dir = temp_path / 'pinyin_tones_release' / 'windows'
            release_dir.mkdir(parents=True)
            (release_dir / 'pinyin_tones.exe').write_text('binary', encoding='utf-8')
            archive_path = temp_path / 'pinyin-tones-windows.zip'
            archive_path.write_text('old archive', encoding='utf-8')

            with mock.patch.object(build_release, 'DIST_DIR', temp_path):
                build_release.create_release_archive('windows', release_dir)

            with zipfile.ZipFile(archive_path) as archive:
                self.assertEqual(
                    archive.namelist(),
                    ['pinyin_tones.exe'],
                )

    def test_create_release_archive_rejects_unsupported_platform(self):
        with self.assertRaises(ValueError):
            build_release.create_release_archive('freebsd', Path('release'))

    def test_build_windows_tk_options_includes_tkinter_runtime_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            tcl_library = temp_path / 'tcl' / 'tcl8.6'
            tk_library = temp_path / 'tcl' / 'tk8.6'
            tkinter_binary = temp_path / 'DLLs' / '_tkinter.pyd'
            tcl_binary = temp_path / 'DLLs' / 'tcl86t.dll'
            tk_binary = temp_path / 'DLLs' / 'tk86t.dll'
            for path in (tcl_library, tk_library, tkinter_binary.parent):
                path.mkdir(parents=True, exist_ok=True)
            for path in (tkinter_binary, tcl_binary, tk_binary):
                path.write_text('binary', encoding='utf-8')

            with mock.patch.object(
                build_release,
                'get_tk_paths',
                return_value=(tcl_library, tk_library, tkinter_binary, tcl_binary, tk_binary),
            ), mock.patch.object(build_release, 'TK_RUNTIME_HOOK', temp_path / 'tk_runtime.py'), \
                mock.patch.object(build_release, 'PYINSTALLER_HOOK_DIR', temp_path / 'hooks'):
                command = build_release.build_windows_tk_options()

            self.assertIn('--additional-hooks-dir', command)
            self.assertIn(str(temp_path / 'hooks'), command)
            self.assertIn('--hidden-import', command)
            self.assertIn('tkinter', command)
            self.assertIn('_tkinter', command)
            self.assertIn('--add-data', command)
            self.assertIn(f'{tcl_library};_tcl_data', command)
            self.assertIn(f'{tk_library};_tk_data', command)
            self.assertIn('--add-binary', command)
            self.assertIn(f'{tkinter_binary};.', command)
            self.assertIn(f'{tcl_binary};.', command)
            self.assertIn(f'{tk_binary};.', command)
            self.assertIn('--runtime-hook', command)
            self.assertTrue((temp_path / 'tk_runtime.py').exists())
            self.assertTrue((temp_path / 'hooks' / 'pre_find_module_path' / 'hook-tkinter.py').exists())

    def test_build_windows_tk_options_rejects_missing_runtime_files(self):
        missing = Path('C:/missing/tcl8.6')
        with mock.patch.object(
            build_release,
            'get_tk_paths',
            return_value=(missing, missing, missing, missing, missing),
        ):
            with self.assertRaises(FileNotFoundError):
                build_release.build_windows_tk_options()


if __name__ == '__main__':
    unittest.main()
