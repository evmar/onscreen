#!/usr/bin/python

import cgi
import os
from django.utils import simplejson as json
import sys
from datetime import datetime, timedelta

import web

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext.webapp import template

DISPLAY_N_RECENT = 5
CYCLE_TIME = 30

class Entry(db.Model):
    owner = db.UserProperty(required=True)
    date = db.DateTimeProperty(auto_now_add=True)
    image = db.BlobProperty()

class State(db.Model):
    slot = db.IntegerProperty()
    since = db.DateTimeProperty()


def get_current_entry():
    query = Entry.gql('ORDER BY date DESC')
    entries = query.fetch(DISPLAY_N_RECENT)

    state = State.gql('').get()
    if not state:
        state = State(slot=0, since=datetime.now())
        state.put()
    else:
        now = datetime.now()
        if now - state.since > timedelta(seconds=CYCLE_TIME):
            state.slot = (state.slot + 1) % min(len(entries), DISPLAY_N_RECENT)
            state.since = now
            state.put()

    return entries[state.slot]


def current_json():
    entry = get_current_entry()
    return json.dumps({
            'image': '/image/%d' % entry.key().id(),
            'owner': entry.owner.nickname()
            })

def new():
    user = users.get_current_user()

    method = os.environ['REQUEST_METHOD']
    if method == 'GET':
        if not user:
            raise web.Special(users.create_login_url(path))
        else:
            print template.render('templates/new.tmpl', {})
    elif method == 'POST':
        if not user:
            raise web.Error(400, 'must login')
        form = cgi.FieldStorage()
        image = form['image'].value
        if image:
            print 'accepted %d bytes of image' % len(image)
            entry = Entry(owner=user, image=image)
            entry.put()
        else:
            raise web.Error(400, 'no image included')

def handle_request(path):
    if path == '/':
        print template.render('templates/frontpage.tmpl', {})
    elif path == '/cycle':
        print template.render('templates/image.tmpl',
                              { 'json': current_json(),
                                'cycle': 1 })
    elif path == '/new':
        headers = new()
    elif path.startswith('/image/'):
        id = int(path[len('/image/'):])
        entry = Entry.get_by_id(id)
        if not entry:
            raise Http404()
        headers = {}
        print entry.image
    elif path == '/json':
        headers = {'Content-Type': 'application/json'}
        print current_json()
    else:
        raise web.Error(404)

web.run(handle_request)
