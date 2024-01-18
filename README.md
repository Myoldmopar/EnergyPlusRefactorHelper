# EnergyPlus Refactoring Helper
A small package to help inspect code, and prepare and apply changes to the EnergyPlus codebase.

## Parser Information
The parser is specifically designed to parse EnergyPlus C++ code.
It will almost certainly fail on any other codebase, because it is based (currently at least) on assumptions about the E+ code structure/rules.

## Testing
[![Flake8](https://github.com/Myoldmopar/EnergyPlusRefactorHelper/actions/workflows/flake8.yml/badge.svg)](https://github.com/Myoldmopar/EnergyPlusRefactorHelper/actions/workflows/flake8.yml)
[![Run Tests](https://github.com/Myoldmopar/EnergyPlusRefactorHelper/actions/workflows/test.yml/badge.svg)](https://github.com/Myoldmopar/EnergyPlusRefactorHelper/actions/workflows/test.yml)
[![Coverage Status](https://coveralls.io/repos/github/Myoldmopar/EnergyPlusRefactorHelper/badge.svg?branch=PackageUpdates)](https://coveralls.io/github/Myoldmopar/EnergyPlusRefactorHelper?branch=PackageUpdates)

Code is tested pretty heavily, and is always trying to hit 100% coverage.

## Documentation
[![Documentation Status](https://readthedocs.org/projects/energyplusrefactorhelper/badge/?version=latest)](https://energyplusrefactorhelper.readthedocs.io/en/latest/?badge=latest)

Docs are written in Sphinx and our main branch is built on ReadTheDocs.

# TODO
- Move actions to a demos folder maybe?
- Deploy on PyPi
