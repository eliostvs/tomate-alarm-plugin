#!/bin/env python
import os

from setuptools import setup

DATA_FILES = [
    ('share/{pkgname}/plugins', 'data/plugins'),
    ('share/{pkgname}/media', 'data/media'),
]


def find_xdg_data_files(install_path, topdir, pkgname, data_files=[]):
    for (dirpath, _, filenames) in os.walk(topdir):
        if filenames:
            install_path = install_path.format(pkgname=pkgname)

            subpath = dirpath.split(topdir)[1]
            if subpath.startswith('/'):
                subpath = subpath[1:]

            files = [os.path.join(dirpath, f) for f in filenames]

            data_files.append((os.path.join(install_path, subpath), files))

    return data_files


def find_data_files(data_map, pkgname):
    data_files = []

    for (system_path, local_path) in data_map:
        find_xdg_data_files(system_path, local_path, pkgname, data_files)

    return data_files


setup(
    author='Elio Esteves Duarte',
    author_email='elio.esteves.duarte@gmail.com',
    description='Tomate Plugin. Play alarm at session end.',
    include_package_data=True,
    keywords='pomodoro,tomate',
    license='GPL-3',
    long_description=open('README.md').read(),
    name='tomate-alarm-plugin',
    data_files=find_data_files(DATA_FILES, 'tomate'),
    url='https://github.com/eliostvs/tomate-alarm-plugin',
    version='0.1.0',
    zip_safe=False,
)
