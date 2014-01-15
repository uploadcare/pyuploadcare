# coding: utf-8
import sys

from setuptools import setup


PY_VERSION = sys.version_info[0], sys.version_info[1]

requirements = ['requests>=1.0', 'python-dateutil>=2.1', 'six>=1.2.0']

if PY_VERSION == (2, 6):
    requirements.append('argparse')


setup(
    name='pyuploadcare',
    version='1.2.3',
    description='Python library for Uploadcare.com',
    long_description=(
        open('README.rst').read() + '\n\n' + open('HISTORY.rst').read()
    ),
    author='Uploadcare Ltd',
    author_email='hello@uploadcare.com',
    url='https://github.com/uploadcare/pyuploadcare',
    packages=['pyuploadcare', 'pyuploadcare.dj'],
    package_data={
        'pyuploadcare.dj': [
            'static/uploadcare/assets/uploaders/*.js',
        ]
    },
    entry_points={
        'console_scripts': [
            'ucare = pyuploadcare.ucare_cli:main',
        ],
    },
    install_requires=requirements,
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
    ],
)
