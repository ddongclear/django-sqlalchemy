from django.core.management.base import NoArgsCommand, CommandError
from django.core.management.color import no_style
from optparse import make_option
from django_sqlalchemy.management import sql
from django.db import models

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--verbosity', action='store', dest='verbosity', default='1',
            type='choice', choices=['0', '1', '2'],
            help='Verbosity level; 0=minimal output, 1=normal output, 2=all output'),
        make_option('--noinput', action='store_false', dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'),
    )
    help = "Executes ``sqlflush`` on the current database."

    def handle_noargs(self, **options):
        from django.conf import settings
        from django.db import connection, transaction, models
        from django.dispatch import dispatcher
        from django.core.management.sql import emit_post_sync_signal

        verbosity = int(options.get('verbosity', 1))
        interactive = options.get('interactive')

        self.style = no_style()

        # Import the 'management' module within each installed app, to register
        # dispatcher events.
        for app_name in settings.INSTALLED_APPS:
            try:
                __import__(app_name + '.management', {}, {}, [''])
            except ImportError:
                pass

        if interactive:
            confirm = raw_input("""You have requested a flush of the database.
This will IRREVERSIBLY DESTROY all data currently in the %r database,
and return each table to the state it was in after syncdb.
Are you sure you want to do this?

    Type 'yes' to continue, or 'no' to cancel: """ % settings.DJANGO_SQLALCHEMY_DBURI)
        else:
            confirm = 'yes'

        if confirm == 'yes':
            try:
                from sqlalchemy import create_engine
                # TODO: Original django code flushes by deleting rows from 
                # each table and reseting sequences back to zero.  This 
                # doesn't reset sequences.
                from django_sqlalchemy.backend import metadata, session
                for app in models.get_apps():
                    for table in sql._get_tables_for_app(app):
                        session.execute(table.delete())
                session.commit()
            except Exception, e:
                # transaction.rollback_unless_managed()
                raise CommandError("""Database %s couldn't be flushed. Possible reasons:
      * The database isn't running or isn't configured correctly.
      * At least one of the expected database tables doesn't exist.
      * The SQL was invalid.
    Hint: Look at the output of 'django-admin.py sqlflush'. That's the SQL this command wasn't able to run.
    The full error: %s""" % (settings.DJANGO_SQLALCHEMY_DBURI, e))
            # transaction.commit_unless_managed()

            # Emit the post sync signal. This allows individual
            # applications to respond as if the database had been
            # sync'd from scratch.
            emit_post_sync_signal(models.get_models(), verbosity, interactive)

            # Reinstall the initial_data fixture.
            from django.core.management import call_command
            call_command('loaddata', 'initial_data', **options)

        else:
            print "Flush cancelled."
