from setuptools import setup
import sys

sys.path.insert(0, "apc")  # noqa
import release


setup(
    name=release.name,
    version=release.__version__,
    author=release.__author__,
    author_email=release.__email__,
    description=release.__description__,
    url="https://github.com/scls19fr/APC/",
    download_url="https://github.com/scls19fr/APC/archive/master.zip",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
    ],
    keywords="apc power distribution unit pdu",
    packages=["apc"],
    install_requires=["pexpect"],
    entry_points={
        "console_scripts": ["apc=apc.cli_apc:main"],
    },
)
