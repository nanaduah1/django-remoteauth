import os
from setuptools import find_packages, setup

README = (
    "Connect to any OAuth2 API in python using client credentials and password flows"
)

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name="django-remoteauth",
    version="0.1.2",
    packages=find_packages(exclude="remoteauth"),
    include_package_data=True,
    license="BSD License",
    description="Package provides API to make http requests to a rest endpoint",
    long_description=README,
    url="gitlab.com",
    author="Nana Duah",
    install_requires=["django", "requests"],
)
