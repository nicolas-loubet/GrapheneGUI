import unittest

from tests.unit import test_graphene, test_core, test_export_formats, test_import_formats, test_recorder
from tests.integration import test_cli_headless
from tests.golden import test_golden

_UNIT_MODULES= (test_graphene, test_core, test_export_formats, test_import_formats, test_recorder)
_INTEGRATION_MODULES= (test_cli_headless,)
_GOLDEN_MODULES= (test_golden,)


def unit_suite():
    loader= unittest.TestLoader()
    suite= unittest.TestSuite()
    for module in _UNIT_MODULES:
        suite.addTests(loader.loadTestsFromModule(module))
    return suite


def integration_suite():
    loader= unittest.TestLoader()
    suite= unittest.TestSuite()
    for module in _INTEGRATION_MODULES:
        suite.addTests(loader.loadTestsFromModule(module))
    return suite


def golden_suite():
    loader= unittest.TestLoader()
    suite= unittest.TestSuite()
    for module in _GOLDEN_MODULES:
        suite.addTests(loader.loadTestsFromModule(module))
    return suite


def full_suite():
    suite= unittest.TestSuite()
    suite.addTests(unit_suite())
    suite.addTests(integration_suite())
    suite.addTests(golden_suite())
    return suite
