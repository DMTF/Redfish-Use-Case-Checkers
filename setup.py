# Copyright Notice:
# Copyright 2017-2025 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Use-Case-Checkers/blob/main/LICENSE.md

from setuptools import setup
from codecs import open

with open("README.md", "r", "utf-8") as f:
    long_description = f.read()

setup(
    name="redfish_use_case_checkers",
    version="2.0.1",
    description="Redfish Use Case Checkers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="DMTF, https://www.dmtf.org/standards/feedback",
    license='BSD 3-clause "New" or "Revised License"',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Topic :: Communications",
    ],
    keywords="Redfish",
    url="https://github.com/DMTF/Redfish-Use-Case-Checkers",
    packages=["redfish_use_case_checkers"],
    entry_points={"console_scripts": ["rf_use_case_checkers=redfish_use_case_checkers.console_scripts:main"]},
    install_requires=["colorama", "redfish>=3.0.0", "redfish_utilities>=1.1.4"],
)
