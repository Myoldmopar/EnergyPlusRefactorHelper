# EnergyPlus Refactoring Helper
A small package to help inspect code, and prepare and apply changes to the EnergyPlus codebase.

## Parser Information
The parser is specifically designed to parse EnergyPlus C++ code.
It will almost certainly fail on any other codebase, because it is based (currently at least) on assumptions about the E+ code structure/rules.

## Testing
[![Flake8](https://github.com/Myoldmopar/EnergyPlusRefactorHelper/actions/workflows/flake8.yml/badge.svg)](https://github.com/Myoldmopar/EnergyPlusRefactorHelper/actions/workflows/flake8.yml)
[![Run Tests](https://github.com/Myoldmopar/EnergyPlusRefactorHelper/actions/workflows/test.yml/badge.svg)](https://github.com/Myoldmopar/EnergyPlusRefactorHelper/actions/workflows/test.yml)

Code is tested pretty heavily, and is always trying to hit 100% coverage.

## Documentation
Docs are being stubbed out in Sphinx, and will be expanded as possible.

# TODO
- Get Coveralls going again
- Get docs fleshed out and RTD working
- Demonstrate the package in-action
- Deploy on PyPi
