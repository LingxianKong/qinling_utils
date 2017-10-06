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
from oslo_config import cfg
import oslo_messaging

from swift.common.swob import Request
from swift.common.utils import get_logger


class Swift(object):
    """Swift middleware used for sending ceilometer notifications."""

    def __init__(self, app, conf):
        self.logger = get_logger(conf, log_route='ceilometer')
        self._app = app

        oslo_messaging.set_transport_defaults(
            conf.get('control_exchange', 'swift')
        )
        self._notifier = oslo_messaging.Notifier(
            oslo_messaging.get_notification_transport(cfg.CONF,
                                                      url=conf.get('url')),
            publisher_id='ceilometermiddleware',
            driver=conf.get('driver', 'messagingv2'),
            topics=[conf.get('topic', 'notifications')]
        )

    def __call__(self, env, start_response):
        res = self._app(env, start_response)
        req = Request(env)

        if req.method == 'PUT':
            try:
                vrs, account, container, obj = req.split_path(4, 4, True)
            except ValueError:
                return res

            self.logger.info(
                'Object uploaded successfully. container: %s, object: %s' %
                (container, object)
            )

            project_id = env.get('HTTP_X_PROJECT_ID',
                                 env.get('HTTP_X_TENANT_ID'))

            self._notifier.info(
                {},
                event_type='objectstorage.object.upload',
                payload={
                    'tenant_id': project_id,
                    'container': container,
                    'object': obj,
                }
            )
            self.logger.info('Notification sent.')

        return res


def filter_factory(global_conf, **local_conf):
    conf = global_conf.copy()
    conf.update(local_conf)

    def filter(app):
        return Swift(app, conf)

    return filter

