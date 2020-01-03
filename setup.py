import os.path as op
import re
from setuptools import setup, find_packages

root = op.dirname(__file__)


def read(*parts, **kwargs):
    return open(op.join(root, *parts)).read()


def read_version():
    filename = 'anki_deck/__init__.py'
    content = read(filename)
    m = re.search("__version__ = '(.+)'", content)
    if m is None:
        raise RuntimeError("Can't read base version from %s" % filename)
    return m.group(1)


setup(
    name='anki-deck',
    version=read_version(),
    author='Sergey Kozlov',
    description='Simple tool to generate Anki flashcards.',
    license='MIT',
    keywords='anki flashcards deck',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
    ],
    include_package_data=True,
    install_requires=['click>=7', 'beautifulsoup4>=4.4'],
    entry_points='''
        [console_scripts]
        anki-deck=anki_deck.cli:run
    ''',
)
