from setuptools import setup, find_packages

setup(
    name='langmark',
    version='0.8.0',
    description=('Lightweight markup language.'),
    long_description=('Powerful lightweight markup language with a '
                      'configurable and extensible parser.'),
    url='https://github.com/kynikos/langmark',
    author='Dario Giovannetti',
    author_email='dev@dariogiovannetti.net',
    license='GPLv3+',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Markup',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',  # noqa
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='markup language parser',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
)
