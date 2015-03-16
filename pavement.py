#!/bin/env python
import os
from optparse import Option

from paver.easy import cmdopts, needs, path, sh
from paver.tasks import task

ROOT_PATH = path(__file__).dirname().abspath()

TOMATE_PATH = ROOT_PATH / 'tomate'

DATA_PATH = ROOT_PATH / 'data'

PLUGIN_PATH = DATA_PATH / 'plugins'


@task
@needs(['test'])
def default():
    pass


@task
def clean():
    sh('pyclean data/plugin')
    sh('pyclean .')
    sh('rm .coverage', ignore_error=True)


@task
@needs(['clean'])
@cmdopts([
    Option('-v', '--verbosity', default=1, type=int),
])
def test(options):
    os.environ['PYTHONPATH'] = '%s:%s' % (TOMATE_PATH, PLUGIN_PATH)
    os.environ['XDG_DATA_DIRS'] = str(DATA_PATH)
    sh('nosetests --cover-erase --with-coverage --verbosity=%s tests.py' % options.test.verbosity)


@task
@needs(['docker_rmi', 'docker_build', 'docker_run'])
def docker_test():
    pass


@task
def docker_rmi():
    sh('docker rmi eliostvs/tomate-alarm-plugin', ignore_error=True)


@task
def docker_build():
    sh('docker build -t eliostvs/tomate-alarm-plugin .')


@task
def docker_run():
    sh('docker run --rm eliostvs/tomate-alarm-plugin')
