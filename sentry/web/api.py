import base64
import datetime
import simplejson
import logging
import time

from sentry import app
from sentry.utils import is_float
from sentry.utils.api import get_mac_signature, parse_auth_header

from flask import request, abort

@app.route('/api/store/', methods=['POST'])
def store():
    if not request.environ.get('AUTHORIZATION', '').startswith('Sentry'):
        abort(401,'Unauthorized')
    
    auth_vars = parse_auth_header(request.META['AUTHORIZATION'])
    
    signature = auth_vars.get('sentry_signature')
    timestamp = auth_vars.get('sentry_timestamp')

    data = request.data

    # Signed data packet
    if signature and timestamp:
        try:
            timestamp = float(timestamp)
        except ValueError:
            abort(400, 'Invalid Timestamp')

        if timestamp < time.time() - 3600: # 1 hour
            abort(410, 'Message has expired')

        if signature != get_mac_signature(app.config['KEY'], data):
            abort(403, 'Invalid signature')
    else:
        abort(401,'Unauthorized')

    logger = logging.getLogger('sentry.server')

    try:
        data = base64.b64decode(data).decode('zlib')
    except Exception, e:
        # This error should be caught as it suggests that there's a
        # bug somewhere in the client's code.
        logger.exception('Bad data received')
        abort(400, 'Bad data decoding request (%s, %s)' % (e.__class__.__name__, e))

    try:
        data = simplejson.loads(data)
    except Exception, e:
        # This error should be caught as it suggests that there's a
        # bug somewhere in the client's code.
        logger.exception('Bad data received')
        abort(403, 'Bad data reconstructing object (%s, %s)' % (e.__class__.__name__, e))

    # XXX: ensure keys are coerced to strings
    data = dict((str(k), v) for k, v in data.iteritems())

    if 'timestamp' in data:
        if is_float(data['timestamp']):
            data['timestamp'] = datetime.datetime.fromtimestamp(float(data['timestamp']))
        else:
            if '.' in data['timestamp']:
                format = '%Y-%m-%dT%H:%M:%S.%f'
            else:
                format = '%Y-%m-%dT%H:%M:%S'
            data['timestamp'] = datetime.datetime.strptime(data['timestamp'], format)

    # TODO
    store()
    
    return ''