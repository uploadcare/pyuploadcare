from setuptools import setup


setup(
    name='pyuploadcare',
    version='0.17',
    description='UploadCare.com API library',
    author='Valentin Golev',
    author_email='v.golev@gmail.com',
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
    install_requires=['requests>=1.0'],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
)
