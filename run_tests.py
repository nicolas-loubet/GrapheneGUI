#!/usr/bin/env python3
"""Corredor de tests para GrapheneGUI. No necesita PySide6 instalado.

Uso:
    python3 run_tests.py                # todo
    python3 run_tests.py --unit         # solo unitarios (graphene/core/export/import)
    python3 run_tests.py --integration  # solo end-to-end del CLI headless
"""
import argparse
import sys
import unittest

from tests import suites


def main():
    parser= argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--unit", action="store_true", help="Solo el conjunto de tests unitarios")
    parser.add_argument("--integration", action="store_true", help="Solo el conjunto de tests de integración (CLI)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args= parser.parse_args()

    if args.unit:
        suite= suites.unit_suite()
    elif args.integration:
        suite= suites.integration_suite()
    else:
        suite= suites.full_suite()

    runner= unittest.TextTestRunner(verbosity=2 if args.verbose else 1)
    result= runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
