import os
import ast
import codecs
from setuptools import setup, find_packages


here = os.path.abspath(os.path.dirname(__file__))
about = {}
with open(os.path.join(here, "naz", "__version__.py"), "r") as f:
    x = f.read()
    y = x.replace("about = ", "")
    about = ast.literal_eval(y)


try:
    import pypandoc

    long_description = pypandoc.convert("README.md", "rst")
except ImportError:
    long_description = codecs.open("README.md").read()


setup(
    name=about["__title__"],
    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=about["__version__"],
    description=about["__description__"],
    long_description=long_description,
    # The project's main homepage.
    url=about["__url__"],
    # Author details
    author=about["__author__"],
    author_email=about["__author_email__"],
    # Choose your license
    license=about["__license__"],
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 4 - Beta",
        # Indicate who your project is intended for
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Security",
        "Topic :: System :: Installation/Setup",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
        # Pick your license as you wish (should match "license" above)
        "License :: OSI Approved :: MIT License",
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        "Programming Language :: Python :: 3.7",
    ],
    # What does your project relate to?
    keywords="naz, smpp, smpp-client, smpp-protocol, smpp-library",
    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    # packages=['naz'],
    packages=find_packages(
        exclude=[
            "documentation",
            "*tests*",
            "examples",
            "benchmarks",
            ".github",
            "documentation/sphinx-docs",
            "sphinx-build",
        ]
    ),
    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    #   py_modules=["my_module"],
    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[],
    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test,benchmarks]
    extras_require={
        "dev": [
            "coverage",
            "pypandoc",
            "twine",
            "wheel",
            "Sphinx==2.2.0",
            "sphinx-autodoc-typehints==1.7.0",
            "sphinx-rtd-theme==0.4.3",  # naz sphinx docs theme
            "redis==3.2.1",
            "pika==1.0.1",
        ],
        "test": ["flake8", "pylint", "black", "bandit", "docker==4.0.1", "mypy", "pytype"],
        "benchmarks": [
            "asyncpg==0.18.3",
            "docker==4.0.1",
            "prometheus_client==0.6.0",
            "aioredis==1.2.0",
        ],
    },
    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    # package_data={
    #     'sample': ['package_data.dat'],
    # },
    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[('my_data', ['data/data_file'])],
    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    # entry_points={
    #     'console_scripts': [
    #         'sample=sample:main',
    #     ],
    # },
    entry_points={"console_scripts": ["naz-cli=cli.cli:main"]},
)

# python packaging documentation:
# 1. https://python-packaging.readthedocs.io/en/latest/index.html
# 2. https://python-packaging-user-guide.readthedocs.io/tutorials/distributing-packages
# a) pip install wheel twine
# b) pip install -e .
# c) python setup.py sdist
# d) python setup.py bdist_wheel
# e) DONT use python setup.py register and python setup.py upload. They use http
# f) twine upload dist/* -r testpypi
# g) pip install -i https://testpypi.python.org/pypi <package name>
# h) twine upload dist/*   # prod pypi
# i) pip install <package name>
# pip install -e .[dev,test,benchmarks]
