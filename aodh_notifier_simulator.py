# Copyright 2018 Catalyst IT Ltd.
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


def main():
    """Send notification to aodh-listener.

    mkdir -p /etc/lingxian
    cat <<EOF > /etc/lingxian/lingxian.conf
    [oslo_messaging_rabbit]
    rabbit_userid = stackrabbit
    rabbit_password = password
    EOF
    """
    conf_file = '/etc/lingxian/lingxian.conf'
    project_id = '360d69d06890407eab1a44573c1f3776'
    publisher_id = "test.lingxian_host"

    conf = cfg.ConfigOpts()
    conf.register_opts([cfg.StrOpt('project_id')], None)
    conf(None, project='lingxian', validate_default_values=False,
         default_config_files=[conf_file])
    transport = oslo_messaging.get_notification_transport(conf)
    notifier = oslo_messaging.Notifier(
        transport,
        publisher_id,
        driver='messagingv2',
        topics=['alarm.all']
    )

    notifier.sample(
        {},
        event_type='',
        payload={
            'event_type': 'compute.instance.create',
            'message_id': 'ac6ce4ae-546a-47cc-a0cb-ad1bae44ca61',
            'traits': [
                # key, type, value
                ['project_id',1,project_id],
                ['service',1,'nova'],
                ['vm_name',1,'new_instance'],
                ['vm_id',1,'ba2b30a0-1b14-4ad4-9a66-f24ece912cad'],
            ],
            'message_signature': 'bcfb59e386d5375dbb7ded9910900a98536f168d377f52ae7ffd89159c0019f5',
            'raw': {},
            'generated': '2017-10-03T10:02:38.305378',
        }
    )
    print('Message sent')


if __name__ == '__main__':
    main()
