from setuptools import setup

setup(
    name='pyuploadcare',
    version='0.6',
    description="UploadCare.com API library",
    author='Valentin Golev',
    author_email='v.golev@gmail.com',
    url='https://github.com/uploadcare/pyuploadcare',
    packages=['pyuploadcare', 'pyuploadcare.dj'],
    package_data={
        'pyuploadcare.dj': [
            'static/uploadcare/assets/uploaders/*.js',
        ]
    },
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ]
)
