"""
Represents the default values for all Sentry settings.
"""

import datetime
import logging
import os
import os.path
import socket

class SentryConfig(object):
    ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), os.pardir))

    DEBUG = True

    DATABASE_USING = None

    THRASHING_TIMEOUT = 60
    THRASHING_LIMIT = 10

    # Sentry allows you to specify an alternative search backend for itself
    SEARCH_ENGINE = None
    SEARCH_OPTIONS = {}

    KEY = socket.gethostname() + '1304u13oafjadf0913j4'

    LOG_LEVELS = (
        (logging.DEBUG, 'debug'),
        (logging.INFO, 'info'),
        (logging.WARNING, 'warning'),
        (logging.ERROR, 'error'),
        (logging.FATAL, 'fatal'),
    )

    # This should a list of the full URI to the storage API endpionts.
    REMOTES = []

    REMOTE_TIMEOUT = 5

    ADMINS = []

    CLIENT = 'sentry.client.base.SentryClient'

    NAME = socket.gethostname()

    # We allow setting the site name either by explicitly setting it with the
    # SENTRY_SITE setting, or using the django.contrib.sites framework for
    # fetching the current site. Since we can't reliably query the database
    # from this module, the specific logic is within the SiteFilter
    SITE = None

    # Extending this allow you to ignore module prefixes when we attempt to
    # discover which function an error comes from (typically a view)
    EXCLUDE_PATHS = []

    # By default Sentry only looks at modules in INSTALLED_APPS for drilling down
    # where an exception is located
    INCLUDE_PATHS = []

    # Absolute URL to the sentry root directory. Should not include a trailing slash.
    URL_PREFIX = ''

    # Allow access to Sentry without authentication.
    PUBLIC = False

    # Maximum length of variables before they get truncated
    MAX_LENGTH_LIST = 50
    MAX_LENGTH_STRING = 200

    SLICES = {
        'everything': {
            'name': 'Everything',
        },
        # 'errors': {
        #     'name': 'Exceptions',
        #     'events': ['sentry.events.Exception'],
        #     'filters': [
        #         ('server', 'sentry.web.filters.Choice'),
        #         ('level', 'sentry.web.filters.Choice'),
        #         ('logger', 'sentry.web.filters.Choice'),
        #     ],
        #     # override the default label 
        #     'labelby': 'url',
        # },
        # 'events': {
        #     'name': 'Messages',
        #     'events': ['sentry.events.Message'],
        #     'filters': [
        #         ('server', 'sentry.web.filters.Choice'),
        #         ('level', 'sentry.web.filters.Choice'),
        #         ('logger', 'sentry.web.filters.Choice'),
        #     ],
        # },
        # 'sql': {
        #     'name': 'SQL',
        #     'events': ['sentry.events.Query'],
        #     'filters': [
        #         ('server', 'sentry.web.filters.Choice'),
        #         ('duration', 'sentry.web.filters.Duration'),
        #     ],
        # },
    }
    
    DATASTORE = {
        'ENGINE': 'sentry.db.backends.redis.RedisBackend',
    }
    
    TRUNCATE_AFTER = datetime.timedelta(days=30)

    SERVER_EMAIL = None

    ## The following settings refer to the built-in webserver

    WEB_HOST = 'localhost'
    WEB_PORT = 9000
    WEB_LOG_FILE = 'sentry.log'
    WEB_PID_FILE = 'sentry.pid'