from setuptools import setup, find_packages

setup(
    name='anki_deck',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['click>=6', 'beautifulsoup4>=4.4'],
    entry_points='''
        [console_scripts]
        anki_deck=anki_deck.cli:run
    ''',
)
