onscreen
========

This is a simple app that cycles through images uploaded by users.

We use it to display images of interest on a screen in our office.

Usage is as follows:

1. Find an image or movie that warrants your officemates' attention.
2. Submit image to app.
3. Shout "ON SCREEN", chanelling your best captain Picard.

directories
-----------

* `appengine/` -- contains the app engine app.
* `client/` -- contains a (not yet finished) native desktop client.
* `extension/` -- contains a (not yet finished) Chrome extension.

todo
----

* when server accepts a url, decide whether it's an image or not for embed
* server-side image resizing
* chrome extension needs to POST and needs server support
* python uploader needs to POST
