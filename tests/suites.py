import unittest

from tests.unit import (
    test_graphene, test_core, test_export_formats, test_import_formats,
    test_recorder, test_plate_registry,
    test_carbon_type_core, test_carbon_type_recorder,
    test_cnt_restore_core, test_cnt_restore_recorder,
    test_reserved_ctype_prefixes,
    test_session_modified_flag,
    test_remove_selection,
    test_open_work_cnt_roundtrip,
    test_atom_type_collision,
    test_plate_registry_slicing,
    test_custom_ctype_mol2_export,
)
from tests.integration import (
    test_cli_headless,
    test_carbon_type_headless,  # Etapa 12: set_carbon_type llega hasta el .top
)
from tests.golden import test_golden

_UNIT_MODULES= (
    test_graphene, test_core, test_export_formats, test_import_formats,
    test_recorder, test_plate_registry,
    test_carbon_type_core, test_carbon_type_recorder,
    test_cnt_restore_core, test_cnt_restore_recorder,
    test_reserved_ctype_prefixes,
    test_session_modified_flag,
    test_remove_selection,
    test_open_work_cnt_roundtrip,
    test_atom_type_collision,
    test_plate_registry_slicing,
    test_custom_ctype_mol2_export,
)
_INTEGRATION_MODULES= (test_cli_headless, test_carbon_type_headless)
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
