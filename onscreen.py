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
ENTRIES_NEWER_THAN_HOURS = 12

class Entry(db.Model):
    owner = db.UserProperty(required=True)
    date = db.DateTimeProperty(auto_now_add=True)
    image = db.BlobProperty()
    url = db.StringProperty()

class State(db.Model):
    slot = db.IntegerProperty()
    since = db.DateTimeProperty()


def get_current_entry():
    now = datetime.now()
    query = Entry.gql(' WHERE date > :date ORDER BY date DESC',
                      date=now - timedelta(hours=ENTRIES_NEWER_THAN_HOURS))
    entries = query.fetch(DISPLAY_N_RECENT)

    if not entries:
        return None

    state = State.gql('').get()
    if not state:
        state = State(slot=0, since=now)
        state.put()
    else:
        if (now - state.since > timedelta(seconds=CYCLE_TIME)  # time to cycle?
            or state.slot >= len(entries)):                    # entry expired?
            state.slot = (state.slot + 1) % min(len(entries), DISPLAY_N_RECENT)
            state.since = now
            state.put()

    return entries[state.slot]


def current_json():
    entry = get_current_entry()
    if entry:
        data = {
            'owner': entry.owner.nickname(),
            'id': entry.key().id()
            }

        if entry.url:
            data['url'] = entry.url
        elif entry.image:
            data['image'] = '/image/%d' % entry.key().id()
        return json.dumps(data)
    else:
        return "{}"


def new(path):
    user = users.get_current_user()

    method = os.environ['REQUEST_METHOD']
    if method == 'GET':
        if not user:
            raise web.Special(302, users.create_login_url(path))
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
        elif 'url' in form:
            print 'accepted url'
            entry = Entry(owner=user, url=form['url'].value)
            entry.put()
        else:
            raise web.Error(400, 'no image/url included')

def handle_request(path):
    if path == '/':
        print template.render('templates/frontpage.tmpl', {})
    elif path == '/cycle':
        print template.render('templates/image.tmpl',
                              { 'json': current_json(),
                                'cycle': 1 })
    elif path == '/new':
        headers = new(path)
    elif path.startswith('/image/'):
        id = int(path[len('/image/'):])
        entry = Entry.get_by_id(id)
        if not entry:
            raise web.Error(404)
        headers = {}
        print entry.image
    elif path == '/json':
        headers = {'Content-Type': 'application/json'}
        print current_json()
    else:
        raise web.Error(404)

web.run(handle_request)
