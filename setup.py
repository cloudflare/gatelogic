import os
import setuptools
import shutil
import subprocess


# Some file systems don't support hard linking. The power of monkey
# patching!
os.link = shutil.copy

setuptools.setup(
    name = 'gatelogic',
    version = subprocess.check_output('git describe --tags --always --dirty=-dev'.split())[1:],
    description = 'Gatelogic - Somewhat functional reactive programming framework',
    packages = ['gatelogic'],
    entry_points = {
        'console_scripts': [
            ],
        },
    zip_safe = False,
    )
