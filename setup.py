#!/bin/python3

try:
    from setuptools import setup, find_packages
except:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
        name='P1tr',
        version='0.1beta',
        description='A modular irc bot.',
        author='Christian Ortner',
        author_email='chris.ortner@gmail.com',
        keywords='plugin irc bot',
        license='MIT',
        url='https://github.com/howard/p1tr-tng',
        install_requires=['oyoyo'],
        package_data={'': ['LICENSE', 'README.md', 'config.cfg.ex']},
        include_package_data=True,
        packages=find_packages(),
        entry_points="""
        [console_scripts]
        p1tr = p1tr.p1tr:main
        """
)

