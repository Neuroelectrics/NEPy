import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="NEPy",
    version="1.0.1",
    author="Giulio Ruffini and Roser Sanchez",
    author_email="roser.sanchez@neuroelectrics.com",
    description="python tool to read and  preprocess .easy and .nedf Neuroelectrics' EEG files",
    url="http://wiki.neuroelectrics.com",
    # packages=['nepy', 'nepy.capsule', 'nepy.frida', 'nepy.readers', 'nepy.tests'],
    packages=setuptools.find_packages()
)