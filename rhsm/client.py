"""
Client interface that using Red Hat Subscription Manager (RHSM) APIs
to collect data from your account.
"""
# client.py
# gather information from RHSM and report it

# Copyright (C) 2019 Antonio Romito (aromito@redhat.com)
#
# This file is part of the sos project: https://github.com/aromito/rhsm-api-client
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# version 2 of the GNU General Public License.
#
# See the LICENSE file in the source distribution for further information.
import argparse
import time
import sys
import six
from rhsm.service import RHSMAuthorizationCode, RHSMApi
from rhsm.objects import System, Systems
from rhsm.outputter import Outputter, OutputFormat, OUTPUT_FORMAT_DEFAULT

if six.PY3:
    raw_input = input


class RHSMClient(object):

    """The main rhsm-api-client class"""

    def __init__(self, parser):
        self._parser = parser
        self._args = self._parser.parse_args()
        self.mode = self._args.mode

    def execute_systems(self):
        total_count = 0
        all_systems = list()

        authorization = RHSMAuthorizationCode(self._args.idp_token_url, self._args.client_id,
                                              self._args.token)
        authorization.refresh_token()
        api_service = RHSMApi(authorization)

        limit = int(self._args.limit)

        offset = 0
        while True:
            this_systems_json = api_service.systems(limit, offset)
            this_systems = Systems(this_systems_json['pagination'], this_systems_json['body'])
            if this_systems.get_count() != 0:
                total_count = total_count + this_systems.get_count()
                offset = offset + limit
                for system in this_systems.get_body():
                    if 'errataCounts' not in system:
                        system['errataCounts'] = None
                    if 'lastCheckin' not in system:
                        system['lastCheckin'] = None

                    this_system = System(
                            system['entitlementCount'], system['entitlementStatus'],
                            system['errataCounts'], system['href'], system['lastCheckin'],
                            system['name'], system['type'], system['uuid'])

                    all_systems.append(this_system)
            else:
                break

        print(time.ctime() + " - Total Number of systems in list: %d" % len(all_systems))
        print(time.ctime() + " - Total Number of systems from count: %d" % total_count)

        format = OutputFormat[self._args.format.upper()]
        outputter = Outputter(format, all_systems)
        outputter.write()

    def execute_allocations(args):
        print('To be implemented')

    def execute_subscriptions(args):
        print('To be implemented')

    def execute_erratas(args):
        print('To be implemented')

    def execute_packages(args):
        print('To be implemented')


def add_systems_command_options(subparsers):
    systems_parser = subparsers.add_parser('systems', help='Fetch a list of systems.')

    systems_parser.add_argument('-l', '--limit', help=('The default and max number of result in a '
                                                       'response are 100.'),
                                default=100, required=False, action='store')


def add_allocations_command_options(subparsers):
    subparsers.add_parser('allocations', help='Generate allocations CSV report.')


def add_subscriptions_command_options(subparsers):
    subparsers.add_parser('subscriptions', help='Generate subscriptions CSV report.')


def add_erratas_command_options(subparsers):
    subparsers.add_parser('erratas', help='Generate erratas CSV report.')


def add_packages_command_options(subparsers):
    subparsers.add_parser('packages', help='Generate packages CSV report.')


def _get_parser():
    parser = argparse.ArgumentParser(description="RHSM API implementation")
    group = parser.add_argument_group('authentication')
    group.add_argument('-c', '--client_id', help=('Red Hat Customer Portal OIDC client '
                       "(default: %(default)s)"), action='store', default='rhsm-api')
    group.add_argument('-i', '--idp_token_url', help=('Red Hat Customer Portal SSO Token URL '
                       "(default: %(default)s)"), action='store',
                       default=('https://sso.redhat.com/auth/realms/redhat-external'
                                '/protocol/openid-connect/token'))
    group.add_argument('-t', '--token', help='Red Hat Customer Portal offline token',
                       required=True, action='store')
    group.add_argument('-f', '--format', help='The format to output data as.',
                       choices=OutputFormat.as_args(), default=OUTPUT_FORMAT_DEFAULT)

    subparsers = parser.add_subparsers(help=('Program mode: systems, allocations, subscriptions, '
                                       'errata, packages)'), dest='mode')

    add_systems_command_options(subparsers)
    add_allocations_command_options(subparsers)
    add_subscriptions_command_options(subparsers)
    add_erratas_command_options(subparsers)
    add_packages_command_options(subparsers)

    return parser


def main():
    parser = _get_parser()
    rhsm = RHSMClient(parser)

    if rhsm.mode == "systems":
        rhsm.execute_systems()
    elif rhsm.mode == "allocations":
        rhsm.execute_allocations()
    elif rhsm.mode == "subscriptions":
        rhsm.execute_subscriptions()
    elif rhsm.mode == "erratas":
        rhsm.execute_erratas()
    elif rhsm.mode == "packages":
        rhsm.execute_packages()
