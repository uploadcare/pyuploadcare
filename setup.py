#!/usr/bin/env python
# coding: utf-8
import sys

from setuptools import setup


PY_VERSION = sys.version_info[0], sys.version_info[1]

requirements = [
    'requests>=1.0',
    'python-dateutil>=2.1',
    'six>=1.2.0',
]

if PY_VERSION < (3, 0):
    long_description = (open('README.rst').read() + '\n\n' +
                        open('HISTORY.rst').read())
else:
    long_description = (open('README.rst', encoding='utf-8').read() + '\n\n' +
                        open('HISTORY.rst', encoding='utf-8').read())

setup(
    name='pyuploadcare',
    version='2.5.0',
    description='Python library for Uploadcare.com',
    long_description=(long_description),
    author='Uploadcare LLC',
    author_email='hello@uploadcare.com',
    url='https://github.com/uploadcare/pyuploadcare',
    packages=['pyuploadcare', 'pyuploadcare.dj', 'pyuploadcare.ucare_cli'],
    package_data={
        'pyuploadcare.dj': [
            'static/uploadcare/*.js',
        ]
    },
    entry_points={
        'console_scripts': [
            'ucare = pyuploadcare.ucare_cli:main',
        ],
    },
    install_requires=requirements,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'License :: OSI Approved :: MIT License',
    ],
)
