import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="purlovia",
    version="0.0.1",
    author="arkutils",
    author_email="author@example.com",
    description="Project Purlovia - digging up Ark data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arkutils/Purlovia",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7"
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=[
        "requests>=2.22.0",
        "pydantic>=0.30.1,<1.0",
        "pyyaml>=5.3",
        "psutil>=5.6.6,<5.7",
    ],
)
