import sys
import unittest

sys.path.insert(0, r'c:\Users\Federico\git\pinyin-tones')
loader = unittest.TestLoader()
suite = unittest.TestSuite()
suite.addTests(loader.loadTestsFromName('tests.test_converter'))
suite.addTests(loader.loadTestsFromName('tests.test_live_flow'))
runner = unittest.TextTestRunner(verbosity=2)
res = runner.run(suite)
if not res.wasSuccessful():
    sys.exit(1)
