#!/usr/bin/python

import cgi
import cgitb
import cStringIO
import os
try:
    import simplejson as json
except:
    import json
import sys
from datetime import datetime, timedelta
cgitb.enable()

from google.appengine.ext import db
from google.appengine.api import users

DISPLAY_N_RECENT = 5
CYCLE_TIME = 10

class Http302(Exception):
    def __init__(self, url):
        self.url = url
class Http400(Exception):
    def __init__(self, message):
        self.message = message
class Http404(Exception):
    pass
class Http500(Exception):
    def __init__(self, message):
        self.message = message


class Entry(db.Model):
    owner = db.UserProperty(required=True)
    date = db.DateTimeProperty(auto_now_add=True)
    image = db.BlobProperty()

class State(db.Model):
    slot = db.IntegerProperty()
    since = db.DateTimeProperty()


path = os.environ['PATH_INFO']

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


def frontpage():
    cgi.print_environ()

def current_json():
    entry = get_current_entry()
    return json.dumps({
            'image': '/image/%d' % entry.key().id(),
            'owner': entry.owner.nickname()
            })

def cycle():
    print """<head>
<link rel=stylesheet href=static/style.css>
</head>

<table width=100%% height=100%%>
<tr><td align=center valign=center>
<img id=image><br>
<div id=caption>posted by <span id=owner></span></div>
</td></tr></table>
<script>
function display(state) {
  document.getElementById('image').src = state.image;
  document.getElementById('owner').innerHTML = state.owner;
}
function update() {
  var xhr = new XMLHttpRequest();
  xhr.onreadystatechange = function() {
    if (xhr.readyState == 4) {
      if (xhr.status == 200)
        display(JSON.parse(xhr.responseText));
      scheduleUpdate();
    }
  }
  xhr.open('GET', '/json', true);
  xhr.send();
}
function scheduleUpdate() {
  setTimeout(update, 3 * 1000);
}

display(%s);
scheduleUpdate();
</script>
""" % current_json()

def new():
    user = users.get_current_user()

    method = os.environ['REQUEST_METHOD']
    if method == 'GET':
        if not user:
            raise Http302(users.create_login_url(path))
        else:
            print """<head>
<link rel=stylesheet href=static/style.css>
</head>

<form method=post enctype=multipart/form-data>
<input name=image type=file><br>
<input type=submit>
</form>
"""
    elif method == 'POST':
        if not user:
            raise Http400('must login')
        form = cgi.FieldStorage()
        image = form['image'].value
        if image:
            print 'accepted %d bytes of image' % len(image)
            entry = Entry(owner=user, image=image)
            entry.put()
        else:
            raise Http400('no image included')

try:
    headers = None
    try:
        orig_stdout = sys.stdout
        sys.stdout = cStringIO.StringIO()
        if path == '/':
            headers = frontpage()
        elif path == '/cycle':
            headers = cycle()
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
            raise Http404()
        output = sys.stdout.getvalue()
        sys.stdout.close()
    finally:
        sys.stdout = orig_stdout
    if len(output) == 0:
        raise Http500('no output')
    print 'Status: 200 OK'
    if headers is None:
        headers = {
            'Content-Type': 'text/html',
            }
    if 'Content-Length' not in headers:
        headers['Content-Length'] = str(len(output))
    for key, val in headers.iteritems():
        print '%s: %s' % (key, val)
    print
    print output
except Http302 as e:
    print """Status: 302 Redirect
Location: %s""" % e.url
except Http400 as e:
    print """Status: 400 Bad Request
Content-Type: text/plain

Bad Request: """ + e.message
except Http404:
    print """Status: 404 Not Found
Content-Type: text/plain

Not Found"""
except Http500 as e:
    print """Status: 500 Internal Server Error
Content-Type: text/plain

Internal server error:
""" + e.message
