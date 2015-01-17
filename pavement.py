#!/bin/env python
import os

from paver.easy import needs, path, sh
from paver.setuputils import install_distutils_tasks
from paver.tasks import task

install_distutils_tasks()

PKGNAME = 'tomate-alarm-plugin'

ROOT_PATH = path(__file__).dirname().abspath()

TOMATE_PATH = ROOT_PATH / 'tomate'

DATA_PATH = ROOT_PATH / 'data'

PLUGIN_PATH = DATA_PATH / 'plugins'


@needs(['test'])
@task
def default():
    pass


@task
def install():
    sh('cat packages.txt | sudo xargs apt-get -y --force-yes install')


@task
def clean():
    sh('pyclean data/plugin')
    sh('pyclean .')
    sh('rm .coverage', ignore_error=True)


@task
@needs(['clean'])
def test(options):
    os.environ['PYTHONPATH'] = '%s:%s' % (TOMATE_PATH, PLUGIN_PATH)
    os.environ['XDG_DATA_DIRS'] = str(DATA_PATH)
    sh('nosetests --cover-erase --with-coverage tests.py')


@task
def docker_build():
    sh('docker build -t eliostvs/tomate-alarm-plugin .')


@task
def docker_run():
    sh('docker run --rm eliostvs/tomate-alarm-plugin')
