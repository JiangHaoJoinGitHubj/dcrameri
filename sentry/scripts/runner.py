#!/usr/bin/env python
import eventlet
import os
import sys

from daemon.daemon import DaemonContext
from daemon.runner import DaemonRunner, make_pidlockfile
from django.conf import settings
from django.core.management import call_command
from eventlet import wsgi
from optparse import OptionParser
from sentry import VERSION
from sentry.wsgi import application

class SentryServer(DaemonRunner):
    pidfile_timeout = 10
    start_message = u"started with pid %(pid)d"

    def __init__(self, host='localhost', port=9000, pidfile='/var/run/sentry.pid',
                 logfile='/var/log/sentry.log'):

        self.daemon_context = DaemonContext()
        self.daemon_context.stdout = open(logfile, 'w+')
        self.daemon_context.stderr = open(logfile, 'w+', buffering=0)

        self.pidfile = None
        if pidfile is not None:
            self.pidfile = make_pidlockfile(
                pidfile, self.pidfile_timeout)

        self.daemon_context.pidfile = self.pidfile

        self.host = host
        self.port = port

        # HACK: set app to self so self.app.run() works
        self.app = self

    def execute(self, action):
        self.action = action
        self.do_action()

    def run(self):
        upgrade()
        wsgi.server(eventlet.listen((self.host, self.port)), application)

def cleanup(days=30, logger=None, site=None, server=None):
    from sentry.models import GroupedMessage, Message
    import datetime
    
    ts = datetime.datetime.now() - datetime.timedelta(days=days)
    
    qs = Message.objects.filter(datetime__lte=ts)
    if logger:
        qs.filter(logger=logger)
    if site:
        qs.filter(site=site)
    if server:
        qs.filter(server_name=server)
    qs.delete()
    
    # TODO: we should collect which messages above were deleted
    # and potentially just send out post_delete signals where
    # GroupedMessage can update itself accordingly
    qs = GroupedMessage.objects.filter(last_seen__lte=ts)
    if logger:
        qs.filter(logger=logger)
    qs.delete()

def upgrade():
    from sentry import conf
    
    call_command('syncdb', database=conf.DATABASE_USING or 'default', interactive=False)

    if 'south' in settings.INSTALLED_APPS:
        call_command('migrate', database=conf.DATABASE_USING or 'default', interactive=False)

def main():
    command_list = ('start', 'stop', 'restart', 'cleanup', 'upgrade')
    args = sys.argv
    if len(args) < 2 or args[1] not in command_list:
        print "usage: sentry [command] [options]"
        print
        print "Available subcommands:"
        for cmd in command_list:
            print "  ", cmd
        sys.exit(1)

    parser = OptionParser(version="%%prog %s" % VERSION)
    parser.add_option('--config', metavar='CONFIG')
    if args[1] == 'start':
        parser.add_option('--host', default='localhost', metavar='HOSTNAME')
        parser.add_option('--port', type=int, default=9000, metavar='PORT')
        parser.add_option('--daemon', action='store_true', default=False, dest='daemonize')
        parser.add_option('--pidfile', default='/var/run/sentry.pid', dest='pidfile')
        parser.add_option('--logfile', default='/var/log/sentry.log', dest='logfile')
    elif args[1] == 'stop':
        parser.add_option('--pidfile', default='/var/run/sentry.pid', dest='pidfile')
        parser.add_option('--logfile', default='/var/log/sentry.log', dest='logfile')
    elif args[1] == 'cleanup':
        parser.add_option('--days', default='30',
                          help='Numbers of days to truncate on.')
        parser.add_option('--logger',
                          help='Limit truncation to only entries from logger.')
        parser.add_option('--site',
                          help='Limit truncation to only entries from site.')
        parser.add_option('--server',
                          help='Limit truncation to only entries from server.')

    (options, args) = parser.parse_args()

    if options.config:
        os.environ['DJANGO_SETTINGS_MODULE'] = options.config

    if not settings.configured:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'sentry.utils.conf.server'

    if args[0] == 'upgrade':
        upgrade()

    elif args[0] == 'start':
        if not options.pidfile:
            sys.exit('You must specify --pidfile')

        app = SentryServer(host=options.host, port=options.port,
                             pidfile=options.pidfile, logfile=options.logfile)
        app.execute(args[0])

    elif args[0] == 'restart':
        app = SentryServer()
        app.execute(args[0])
  
    elif args[0] == 'stop':
        if not options.pidfile:
            sys.exit('You must specify --pidfile')

        app = SentryServer(pidfile=options.pidfile, logfile=options.logfile)
        app.execute(args[0])

    elif args[0] == 'cleanup':
        cleanup(days=options.days, logger=options.logger, site=options.site, server=options.server)

    sys.exit(0)

if __name__ == '__main__':
    main()