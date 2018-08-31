"""
setup.py file

NOTE: This setup.py was lifted from https://github.com/kennethreitz/setup.py/blob/master/setup.py
and https://github.com/requests/requests/blob/master/setup.py.  So see there for more details.
"""
#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Note: To use the 'upload' functionality of this file, you must:
#   $ pip install twine

import io
import os
import sys
from shutil import rmtree

from setuptools import find_packages, setup, Command

# Used for looking up "<NAME>/__version__.py
NAME = 'butter'

# What packages are required for this module to be executed?
REQUIRED = [
    'boto3',
    'PyYaml',
    'jinja2',
    # This pytest dependency is only for the module tester.  Perhaps this should
    # be a separate module eventually.
    'pytest',
    'attr',
    'click',
    'apache-libcloud',
    'pycryptodome',
    # Even though moto is for testing, need it for the "mock-aws" provider.
    'moto==1.3.4',
]

# What packages are required for this module to be tested?
TESTS_REQUIRED = [
    'pytest',
    'pytest-xdist',
    'tox',
    'pylint'
]

# What packages are optional?
EXTRAS = {
    "testing": TESTS_REQUIRED
}

# The rest you shouldn't have to touch too much :)
# ------------------------------------------------
# Except, perhaps the License and Trove Classifiers!
# If you do change the License, remember to change the Trove Classifier for
# that!

here = os.path.abspath(os.path.dirname(__file__)) # pylint: disable=invalid-name

# Load the package's __version__.py module as a dictionary.
about = {} # pylint: disable=invalid-name
with open(os.path.join(here, NAME, '__version__.py')) as f:
    # pylint: disable=exec-used
    exec(f.read(), about)

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
try:
    with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        LONG_DESCRIPTION = '\n' + f.read()
except FileNotFoundError:
    LONG_DESCRIPTION = about["__description__"]


class UploadCommand(Command):
    """Support setup.py upload."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(message):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(message))

    def initialize_options(self):
        """
        Unused/noop
        """
        pass

    def finalize_options(self):
        """
        Unused/noop
        """
        pass

    def run(self):
        """
        Runs package upload
        """
        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel (universal) distribution…')
        os.system('{0} setup.py sdist bdist_wheel --universal'.format(
            sys.executable))

        self.status('Uploading the package to PyPI via Twine…')
        os.system('twine upload dist/*')

        self.status('Pushing git tags…')
        os.system('git tag v{0}'.format(about['__version__']))
        os.system('git push --tags')

        sys.exit()


# Where the magic happens:
setup(
    name=NAME,
    version=about['__version__'],
    description=about["__description__"],
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    author=about["__author__"],
    author_email=about["__author_email__"],
    python_requires=about["__requires_python__"],
    url=about["__url__"],
    packages=find_packages(exclude=('tests',)),
    # If your package is a single module, use this instead of 'packages':
    # py_modules=['mypackage'],

    entry_points={
        'console_scripts': ['butter-test=butter.testutils.cli:main'],
    },
    install_requires=REQUIRED,
    tests_require=TESTS_REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license=about["__license__"],
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
    # $ setup.py publish support.
    cmdclass={
        'upload': UploadCommand,
    },
)
