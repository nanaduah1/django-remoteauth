import os
from setuptools import find_packages, setup

README = 'Coming Soon'

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-remoteauth',
    version='0.0.1-rc1',
    packages=find_packages(exclude='remoteauth'),
    include_package_data=True,
    license='BSD License',
    description='Package provides API to make http requests to a rest endpoint',
    long_description=README,
    url='https://gitlab.com/gabano2005/django-remoteauth.git',
    author='Nana Duah',
    install_requires=[
        'django>=2.1,<3',
        'requests==2.19.1'
    ]
)