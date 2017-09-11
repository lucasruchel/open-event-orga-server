from datetime import datetime

import requests
from tzlocal import get_localzone
from requests import ConnectionError

from app.helpers.flask_ext.helpers import get_real_ip


def get_current_timezone():
    match = str(get_localzone())
    if match is not None:
        return match
    else:
        return 'UTC'


def get_event_time_field_format(form, field):
    try:
        return datetime.strptime(form[field + '_date'].strip() + ' ' + form[field + '_time'].strip(), '%m/%d/%Y %H:%M')
    except:
        return None


def get_searchable_location_name(event):
    searchable_location_name = None
    if event.latitude and event.longitude:
        url = 'https://maps.googleapis.com/maps/api/geocode/json'
        latlng = '{},{}'.format(event.latitude, event.longitude)
        params = {'latlng': latlng}
        response = dict()

        try:
            response = requests.get(url, params).json()
        except ConnectionError:
            response['status'] = u'Error'

        if response['status'] == u'OK':
            for addr in response['results'][0]['address_components']:
                if addr['types'] == ['locality', 'political']:
                    searchable_location_name = addr['long_name']
    return searchable_location_name
