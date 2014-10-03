from setuptools import setup, find_packages
import sys
import os

wd = os.path.dirname(os.path.abspath(__file__))
os.chdir(wd)
sys.path.insert(1, wd)

name = 'slack_kanbanize'
pkg = __import__('slack_kanbanize')

author, email = pkg.__author__.rsplit(' ', 1)
email = email.strip('<>')

version = pkg.__version__
classifiers = pkg.__classifiers__

readme = open(os.path.join(wd, 'README.md'),'r').readlines()
description = readme[1]
long_description = ''.join(readme)

try:
    reqs = open(os.path.join(os.path.dirname(__file__), 'requirements.txt')).read()
except (IOError, OSError):
    reqs = ''

setup(
    name=name,
    version=version,
    author=author,
    author_email=email,
    url='https://github.com/mportela/slack_kanbanize',
    maintainer=author,
    maintainer_email=email,
    description=description,
    long_description=long_description,
    classifiers=classifiers,
    dependency_links = ['https://github.com/mportela/python-kanbanize/tarball/master#egg=python-kanbanize-0.2.1',
                        'https://github.com/mportela/pyslack/tarball/master#egg=pyslack-0.3.0'],
    install_requires = reqs,
    package_dir={'': 'slack_kanbanize'},
    packages=[''] + find_packages('slack_kanbanize'),
    license = 'GNU GPL V2',
    keywords ='slack notificator kanbanize plugin',
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "slack_kanbanize_feeder = main:process"
        ],
    }
)
