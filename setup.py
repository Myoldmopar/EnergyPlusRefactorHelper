from pathlib import Path
from setuptools import setup

from energyplus_refactor_helper import VERSION, PACKAGE_NAME
readme_file = Path(__file__).parent.resolve() / 'README.md'
readme_contents = readme_file.read_text()

setup(
    name=PACKAGE_NAME,
    version=VERSION,
    packages=[PACKAGE_NAME, f"{PACKAGE_NAME}.actions"],
    description="An EnergyPlus-specific set of tools that help analyze & refactor EnergyPlus code",
    package_data={f"{PACKAGE_NAME}": ['actions/known_error_calls.json']},
    include_package_data=True,
    long_description=readme_contents,
    long_description_content_type='text/markdown',
    author='Edwin Lee, for NREL, for the United States Department of Energy',
    url='https://github.com/Myoldmopar/EnergyPlusRefactorHelper',
    license='ModifiedBSD',
    install_requires=['matplotlib'],
    entry_points={
        'gui_scripts': [],
        'console_scripts': ['energyplus_refactor=energyplus_refactor_helper.main:run_cli']},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Physics',
        'Topic :: Utilities',
    ],
    platforms=[
        'Linux (Tested on Ubuntu)', 'MacOSX', 'Windows'
    ],
    keywords=[
        'EnergyPlus', 'eplus', 'Energy+',
        'Building Simulation', 'Whole Building Energy Simulation',
        'Heat Transfer', 'HVAC', 'Modeling',
    ]
)
