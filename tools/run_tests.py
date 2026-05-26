import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / 'src'
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(ROOT_DIR))
loader = unittest.TestLoader()
suite = unittest.TestSuite()
suite.addTests(loader.loadTestsFromName('tests.test_converter'))
suite.addTests(loader.loadTestsFromName('tests.test_live_flow'))
suite.addTests(loader.loadTestsFromName('tests.test_build_release'))
runner = unittest.TextTestRunner(verbosity=2)
res = runner.run(suite)
if not res.wasSuccessful():
    sys.exit(1)
