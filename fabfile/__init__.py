#!/usr/bin/env python
# -*- coding: utf-8 -*-

import StringIO
import os

from fabric.api import *
from fabric.operations import get, put
from jinja2 import Template

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))
env.hosts = ['178.62.41.50']
env.user = "root"

VHOST = 'shorelands'
APPS_DIR = '/www/'
APP_ROOT = '%s%s' % (APPS_DIR, VHOST.replace('.', '_'))
MODULE = 'app'

REPOS = '/repos/hg'
STATIC = 'static'
SUPERVISOR_DIR = '/etc/supervisor/conf.d/'
NGINX_DIR = '/etc/nginx/sites-'

APT_GET_PACKAGES = [
    "build-essential",
    "git",
    "vim",
    "python-dev",
    "python-virtualenv",
    "python-pip",
    "supervisor",
    "nginx"
]


def setup():
    "Install default packages for django"
    run("apt-get update && apt-get upgrade")
    run("apt-get install " + " ".join(APT_GET_PACKAGES))


def _render_template(string, context):
    return Template(string).render(context)


def make_supervisor_conf():
    template = open(os.path.join(__location__, 'supervisor_flask.tpl'))

    #get('%sflaskapp.tpl' % SUPERVISOR_DIR, template)
    interpolated = StringIO.StringIO()
    interpolated.write(_render_template(template.read(), {
        'domain': VHOST,
        'root': APP_ROOT,
        'module': MODULE
    }))
    put(interpolated, '%(supervisor_dir)s%(vhost)s.conf' % {'supervisor_dir': SUPERVISOR_DIR, 'vhost': VHOST},
        use_sudo=True)


def make_vhost():
    template = open(os.path.join(__location__, 'nginx_flask.tpl'))
    #get('%savailable/flask.tpl' % NGINX_DIR, template)
    interpolated = StringIO.StringIO()
    interpolated.write(_render_template(template.read(), {
        'domain': VHOST,
        'root': APP_ROOT,
        'static': STATIC
    }))
    put(interpolated, '%(nginx)savailable/%(vhost)s' % {'nginx': NGINX_DIR, 'vhost': VHOST}, use_sudo=True)
    sudo('ln -s %(src)s %(tar)s' % {'src': '%(nginx)savailable/%(vhost)s' % {'nginx': NGINX_DIR, 'vhost': VHOST},
                                    'tar': '%(nginx)senabled/%(vhost)s' % {'nginx': NGINX_DIR, 'vhost': VHOST}}
    )
    # with cd('www'):
    #     run('mkdir shorelands')
    # run('touch %s/access.log' % APP_ROOT)
    # run('touch %s/error.log' % APP_ROOT)


def make_gunicorn_config():
    config = open(os.path.join(__location__, 'gunicorn_flask.tpl'))
    interpolated = StringIO.StringIO()
    interpolated.write(_render_template(config.read()))
    put(interpolated, '/', use_sudo=True)


def clone_repo():
    with cd(APPS_DIR):
        run('hg clone %(repos)s%(vhost)s %(to)s' % {'repos': REPOS, 'vhost': VHOST, 'to': APP_ROOT})


def update_repo():
    with cd(APP_ROOT):
        run('hg pull')
        run('hg up -C default')


def reload_webserver():
    sudo("/etc/init.d/nginx reload")


def reload_supervisor():
    sudo('supervisorctl update')


def start_app():
    sudo('supervisorctl start %s' % VHOST)


def reload_app(touch=True):
    if touch:
        with cd(APP_ROOT):
            run('touch app.wsgi')
    else:
        sudo('supervisorctl restart %s' % VHOST)


def init_deploy():
    clone_repo()
    make_vhost()
    make_supervisor_conf()
    reload_webserver()
    reload_supervisor()
    start_app()


def deploy():
    update_repo()
    reload_app()