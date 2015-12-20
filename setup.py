from setuptools import setup, find_packages

setup(
    name='anki_deck',
    version='0.1',
    author='Sergey Kozlov',
    description='Simple tool to generate Anki flashcards.',
    license='MIT',
    keywords="anki flashcards",
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
    ],
    include_package_data=True,
    install_requires=['click>=6', 'beautifulsoup4>=4.4'],
    entry_points='''
        [console_scripts]
        anki_deck=anki_deck.cli:run
    ''',
)
