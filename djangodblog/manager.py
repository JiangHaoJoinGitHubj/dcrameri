# Multi-db support based on http://www.eflorenzano.com/blog/post/easy-multi-database-support-django/
# TODO: is there a way to use the traceback module based on an exception variable?

from django.conf import settings
from django.db import models
from django.conf import settings
from django.db.models import sql
from django.db.transaction import savepoint_state
from django.utils.hashcompat import md5_constructor
from django.utils.encoding import smart_unicode
from django.db.models.sql import BaseQuery
from django.db.models.query import QuerySet

try:
    import thread
except ImportError:
    import dummy_thread as thread
import traceback
import socket
import warnings
import datetime
import django

django_is_10 = django.VERSION < (1, 1)

"""
``DBLOG_DATABASE`` allows you to use a secondary database for error logging::

    DBLOG_DATABASE = dict(
        DATABASE_ENGINE='mysql', # defaults to settings.DATABASE_ENGINE
        DATABASE_NAME='my_db_name',
        DATABASE_USER='db_user',
        DATABASE_PASSWORD='db_pass',
        DATABASE_HOST='localhost', # defaults to localhost
        DATABASE_PORT='', # defaults to [default port]
        DATABASE_OPTIONS={}
    )
    
Note: You will need to create the tables by hand if you use this option.
"""

assert(not getattr(settings, 'DBLOG_DATABASE', None) or django.VERSION < (1, 2), 'The `DBLOG_DATABASE` setting requires Django < 1.2')

class DBLogManager(models.Manager):
    def get_query_set(self):
        db_options = getattr(settings, 'DBLOG_DATABASE', None)
        if not db_options:
            return super(DBLogManager, self).get_query_set()
            
        connection = self.get_db_wrapper(db_options)
        if connection.features.uses_custom_query_class:
            Query = connection.ops.query_class(BaseQuery)
        else:
            Query = BaseQuery
        return QuerySet(self.model, Query(self.model, connection))

    def get_db_wrapper(self, options):
        backend = __import__('django.db.backends.' + options.get('DATABASE_ENGINE', settings.DATABASE_ENGINE)
            + ".base", {}, {}, ['base'])
        if django_is_10:
            backup = {}
            for key, value in options.iteritems():
                backup[key] = getattr(settings, key)
                setattr(settings, key, value)
        connection = backend.DatabaseWrapper(options)
        # if django_is_10:
        #     connection._cursor(settings)
        # else:
        #     wrapper._cursor()
        if django_is_10:
            for key, value in backup.iteritems():
                setattr(settings, key, value)
        return connection

    def _insert(self, values, return_id=False, raw_values=False):
        db_options = getattr(settings, 'DBLOG_DATABASE', None)
        if not db_options:
            return super(DBLogManager, self)._insert(values, return_id, raw_values)

        query = sql.InsertQuery(self.model, self.get_db_wrapper())
        query.insert_values(values, raw_values)
        ret = query.execute_sql(return_id)
        # XXX: Why is the following needed?
        query.connection._commit()
        thread_ident = thread.get_ident()
        if thread_ident in savepoint_state:
            del savepoint_state[thread_ident]
        return ret

    def create_from_exception(self, exception, url=None):
        from models import Error, ErrorBatch
        
        server_name = socket.gethostname()
        tb_text     = traceback.format_exc()
        class_name  = exception.__class__.__name__
        checksum    = md5_constructor(tb_text).hexdigest()

        defaults = dict(
            class_name  = class_name,
            message     = smart_unicode(exception),
            url         = url,
            server_name = server_name,
            traceback   = tb_text,
        )

        try:
            instance = Error.objects.create(**defaults)
            batch, created = ErrorBatch.objects.get_or_create(
                class_name = class_name,
                server_name = server_name,
                checksum = checksum,
                defaults = defaults
            )
            if not created:
                batch.times_seen += 1
                batch.resolved = False
                batch.last_seen = datetime.datetime.now()
                batch.save()
        except Exception, exc:
            warnings.warn(smart_unicode(exc))
        return instance