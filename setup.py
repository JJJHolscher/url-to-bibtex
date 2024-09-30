from setuptools import setup, find_packages

setup(
    name='readwise-to-zotero',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'requests',
        'toml',
        'argparse',
    ],
    entry_points={
        'console_scripts': [
            'readwise-to-zotero=readwise_to_zotero:main',
        ],
    },
    author='Jochem Holscher',
    author_email='jochem.holscher@gmail.com',
    description='CLI tool to import Readwise data into Zotero',
    url='https://github.com/JJJHolscher/readwise-to-zotero',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
)

