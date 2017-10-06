# Copyright 2017 Catalyst IT Ltd
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

"""Qinling alarm notifier."""

from oslo_log import log
import six.moves.urllib.parse as urlparse
from qinlingclient.v1 import client as q_client

from aodh import keystone_client
from aodh import notifier
from aodh.notifier import trust

LOG = log.getLogger(__name__)


class QinlingFunctionNotifier(notifier.AlarmNotifier):
    def __init__(self, conf):
        super(QinlingFunctionNotifier, self).__init__(conf)
        self.conf = conf
        self._endpoint = None

    def _get_endpoint(self):
        if self._endpoint is None:
            try:
                ks_client = keystone_client.get_client(self.conf)
                srv = ks_client.services.find(type='function-engine')
                endpoint = ks_client.endpoints.find(service_id=srv.id,
                                                    interface='public')
                self._endpoint = endpoint.url
            except Exception:
                LOG.error("Qinling endpoint could not be found in Keystone "
                          "service catalog.")
        return self._endpoint

    def notify(self, action, alarm_id, alarm_name, severity, previous,
               current, reason, reason_data, headers=None):
        LOG.info(
            "Notifying alarm %(alarm_name)s %(alarm_id)s of %(severity)s "
            "priority from %(previous)s to %(current)s with action %(action)s"
            " because %(reason)s." % ({'alarm_name': alarm_name,
                                       'alarm_id': alarm_id,
                                       'severity': severity,
                                       'previous': previous,
                                       'current': current,
                                       'action': action,
                                       'reason': reason})
        )

        queue_info = urlparse.parse_qs(action.query)
        function_id = queue_info.get('function_id')[0]

        # Get function input params
        container = None
        object = None
        traits = reason_data['event']['traits']
        for t in traits:
            if t[0] == 'container':
                container = t[2]
            if t[0] == 'object':
                object = t[2]

        input = {'container': container, 'object': object}
        LOG.info('Function %s, input: %s', function_id, input)

        # Initialize qinling client
        qinling_endpoint = self._get_endpoint()
        client = q_client.Client(
            qinling_endpoint,
            token=headers.get('X-Auth-Token'),
            auth_url=self.conf.service_credentials.auth_url,
        )

        # Invoke qinling function
        res = client.function_executions.create(
            function_id,
            input=input,
            sync=False
        )

        LOG.info('Function %s invoked.', function_id)


class TrustQinlingFunctionNotifier(trust.TrustAlarmNotifierMixin,
                                   QinlingFunctionNotifier):
    """Qinling notifier using a Keystone trust to invoke user's function.

    The URL must be in the form:
    ``trust+qinling://?function_id=123``.
    """

