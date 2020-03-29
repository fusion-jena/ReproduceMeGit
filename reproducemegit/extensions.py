# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located in app.py."""
from flask_static_digest import FlaskStaticDigest
from flask_wtf.csrf import CSRFProtect
from flask_caching import Cache

csrf_protect = CSRFProtect()
cache = Cache()
flask_static_digest = FlaskStaticDigest()
