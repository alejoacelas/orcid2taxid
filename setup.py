from setuptools import setup, find_namespace_packages

setup(
    name="orcid2taxid",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_namespace_packages(where="src"),
    description="A tool to map ORCID identifiers to taxonomic IDs",
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "orcid2taxid=orcid2taxid.main:main",
        ],
    },
) 