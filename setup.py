import os
import setuptools  # type: ignore

with open(".github/assets/pypi_desc.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

if version := os.environ.get("RELEASE_VERSION"):
    setuptools.setup(
        name="phaistos",
        version=version,
        author="Kamil Rybacki",
        author_email="kamilandrzejrybacki@gmail.com",
        description="Tooling to automatically generate validated data models from YAML configuration files",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://phaistos.readthedocs.io/en/latest",
        packages=setuptools.find_packages(),
        install_requires=[
            "PyYAML==6.0.1",
            "pydantic==2.7.0",
        ]
    )
else:
    raise RuntimeError("RELEASE_VERSION environment variable is not set")
