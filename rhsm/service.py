# Copyright (C) 2019 Antonio Romito (aromito@redhat.com)
#
# This file is part of the sos project: https://github.com/aromito/rhsm-api-client
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# version 2 of the GNU General Public License.
#
# See the LICENSE file in the source distribution for further information.
import logging
import json
import requests
import time
import sys
from oauthlib.oauth2 import TokenExpiredError, Client
from requests_oauthlib import OAuth2Session
from rhsm.objects.system import System

logging.getLogger(__name__)

class RHSMAuthorizationCode(object):
    TOKEN_PATH = ''

    def __init__(self, token_url, client_id, offline_token, token=None):
        self.token_url = token_url
        self.client_id = client_id
        self.offline_token = offline_token
        self.token = token

        self.session = OAuth2Session(client=Client(client_id=self.client_id,
                                                   refresh_token=self.offline_token))

    def refresh_token(self):
        self.token = self.session.refresh_token(token_url=self.token_url, client_id=self.client_id)
        return self.token


class RHSMApi(object):
    API_URL = 'https://api.access.redhat.com/management/v1'
    FETCH_LIMIT = 100

    def __init__(self, auth=None):
        self.auth = auth

    def _get(self, endpoint, params=None):
        retries = 0
        success = False
        while not success and retries < 3:
            url = self.API_URL + '/' + endpoint
            logging.debug(time.ctime() + ' - Starting request: %s with params: %s ' % (url, params))
            if self.auth:
                try:
                    t1 = time.time()
                    response = self.auth.session.get(url, params=params)
                    t2 = time.time()
                except TokenExpiredError:
                    logging.debug(time.ctime() + ' - Token has expired. Refreshing token...')
                    self.auth.refresh_token()
                    t1 = time.time()
                    response = self.auth.session.get(url, params=params)
                    t2 = time.time()
            else:
                t1 = time.time()
                response = requests.get(url, params=params)
                t2 = time.time()
            logging.debug(time.ctime() + (' - The Round Trip Time (RTT) for %s is %.4fs. '
                                  'Status code is: %s') %
                  (response.url, (t2 - t1), response.status_code))

            try:
                response.raise_for_status()
                success = True
            except requests.exceptions.HTTPError:
                wait = 5
                retries += 1
                time.sleep(wait)
                logging.debug(time.ctime() + ' - Response status code code indicate a failed attempt to '
                                     'retrive data. Waiting %s secs and re-trying... Attempt '
                                     'number [%d]' % (str(wait), retries))

            if response.status_code == requests.codes.ok:
                return response.json()
            elif response.status_code != requests.codes.ok and retries == 3:
                sys.exit(time.ctime() + ' - Exiting after %d failed attempts to retrive data from: '
                                        '%s' % (retries, response.url))

    def systems(self):
        logging.debug('Started systems service call')
        all_systems = []
        offset = 0
        while True:
            batch_systems = self.fetch_systems(offset)
            batch_count = batch_systems['pagination']['count']
            if not batch_count:
                break

            logging.debug('Fetched another %s systems', batch_count)
            offset += self.FETCH_LIMIT
            for system_raw in batch_systems['body']:
                logging.debug('Processing: %s', system_raw)
                system = System.deserialize(system_raw)
                all_systems.append(system)
        return all_systems


    def fetch_systems(self, offset):
        payload = {'limit': self.FETCH_LIMIT, 'offset': offset}
        data = self._get("systems", params=payload)
        return data
