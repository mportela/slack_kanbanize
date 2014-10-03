# coding=utf-8

import unittest
import mock
import datetime

from dateutil import tz
import feeder
from python_kanbanize.wrapper import Kanbanize
from pyslack import SlackClient


class TestFeederClass(unittest.TestCase):

    def setUp(self):
        self.obj = feeder.Feeder("foo_kanbanize_api_key", 3, "foo_slack_token",
                                 "foo_slack_channel")
        self.utc_zone = tz.tzutc()
        self.local_zone = tz.tzlocal()

    def test_basic_instance(self):
        exp_kanbanize_opts = {
            'api_key': "foo_kanbanize_api_key",
            'board_id': 3,
            'collect_minutes_timedelta': 2
        }
        exp_slack_opts = {
            'token': "foo_slack_token",
            'channel': "foo_slack_channel",
            'user': "slackbot"
        }
        self.assertEqual(exp_kanbanize_opts, self.obj.kanbanize_opts)
        self.assertEqual(exp_slack_opts, self.obj.slack_opts)

    @mock.patch.object(Kanbanize, 'get_board_activities')
    def test_get_kanbanize_board_activities(self, mk_get_activities):
        to_date = datetime.datetime.now()
        from_date = datetime.datetime.now() - datetime.timedelta(hours=1)

        mk_ret = [{'type': 'blah'}, {'type': 'blah'}, {'type': 'blah2'}]

        mk_get_activities.return_value = mk_ret
        ret = self.obj._get_kanbanize_board_activities(from_date, to_date)

        exp_from_date = from_date.replace(tzinfo=self.local_zone)
        exp_from_date = exp_from_date.astimezone(self.utc_zone).strftime(
                                                        "%Y-%m-%d %H:%M:%S")
        exp_to_date = to_date.replace(tzinfo=self.local_zone)
        exp_to_date = exp_to_date.astimezone(self.utc_zone).strftime(
                                                        "%Y-%m-%d %H:%M:%S")
        mk_get_activities.assert_called_once_with(
                                        self.obj.kanbanize_opts['board_id'],
                                        exp_from_date,
                                        exp_to_date)
        self.assertEqual(mk_ret, ret)

    @mock.patch.object(SlackClient, 'chat_post_message')
    def test_simple_post_slack_message(self, mk_post_message):
        mk_post_message.return_value = {u'ok': True}
        ret = self.obj._post_slack_message("foo message blah")
        mk_post_message.assert_called_once_with(
                                      self.obj.slack_opts['channel'],
                                      "foo message blah",
                                      username=self.obj.slack_opts['user'])
        self.assertEqual(True, ret, "must return True when ok")

    @mock.patch.object(SlackClient, 'chat_post_message')
    def test_extra_params_post_slack_message(self, mk_post_message):
        mk_post_message.return_value = {u'ok': True}
        ret = self.obj._post_slack_message("foo message blah", parse="full",
                                           unfurl_links=1)
        mk_post_message.assert_called_once_with(
                                      self.obj.slack_opts['channel'],
                                      "foo message blah",
                                      username=self.obj.slack_opts['user'],
                                      parse="full",
                                      unfurl_links=1)
        self.assertEqual(True, ret, "must return True when ok")

    @mock.patch.object(feeder.Feeder, 'default_message_formatter_function')
    def test_parse_kambanize_activities_without_formatter(self, mk_formatter):
        """
            test parse activities with default formatter
            simulatte complex possibilities to be grouped and returned:
                - 2 activities in same task / date
                - 2 activities in same task / different dates
                - 1 activity in other task / date
        """
        mk_formatter.side_effect = [u'msg fmted 1', u'msg fmted 2',
                                    u'msg fmted 3', u'msg fmted 4',
                                    u'msg fmted 5']
        raw_data = {u'activities': [
            {u'author': u'marcel.portela',
             u'date': u'2014-10-02 20:21:06',
             u'event': u'Assignee changed',
             u'taskid': u'133',
             u'text': u'New assignee: marcel.portela'},
            {u'author': u'marcel.portela',
             u'date': u'2014-10-02 20:21:06',
             u'event': u'Task moved',
             u'taskid': u'133',
             u'text': u"From 'J\xe1 detalhados' to 'In Progress.Fazendo'"},
            {u'author': u'pappacena',
             u'date': u'2014-10-02 19:25:36',
             u'event': u'Task moved',
             u'taskid': u'119',
             u'text': u"From 'J\xe1 detalhados' to 'Backlog'"},
            {u'author': u'pappacena',
             u'date': u'2014-10-02 19:26:36',
             u'event': u'Task moved',
             u'taskid': u'119',
             u'text': u"From 'Backlog' to 'J\xe1 detalhados'"},
            {u'author': u'pappacena',
             u'date': u'2014-10-02 19:36:36',
             u'event': u'Assignee changed',
             u'taskid': u'121',
             u'text': u'New assignee: marcel.portela'}
            ]
        }

        ret = self.obj._parse_kambanize_activities(raw_data)

        exp_calls = [
            mock.call(
                {u'author': u'marcel.portela',
                 u'event': u'Assignee changed',
                 u'text': u'New assignee: marcel.portela'},
            ),
            mock.call(
                {u'author': u'marcel.portela',
                 u'event': u'Task moved',
                 u'text': u"From 'J\xe1 detalhados' to 'In Progress.Fazendo'"}
            ),
            mock.call(
                {u'author': u'pappacena',
                 u'event': u'Task moved',
                 u'text': u"From 'J\xe1 detalhados' to 'Backlog'"}
            ),
            mock.call(
                {u'author': u'pappacena',
                 u'event': u'Task moved',
                 u'text': u"From 'Backlog' to 'J\xe1 detalhados'"}
            ),
            mock.call(
                {u'author': u'pappacena',
                 u'event': u'Assignee changed',
                 u'text': u'New assignee: marcel.portela'}
            )
        ]
        self.assertEqual(exp_calls, mk_formatter.call_args_list)

        #expected ret - 3 tasks
        exp_ret = [
            {u'taskid': u'133',
             u'activities': {
                    u'2014-10-02 20:21:06': [
                        {u'author': u'marcel.portela',
                         u'event': u'Assignee changed',
                         u'text': u'New assignee: marcel.portela',
                         u'formatted_message': u'msg fmted 1'},
                        {u'author': u'marcel.portela',
                         u'event': u'Task moved',
                         u'text': u"From 'J\xe1 detalhados' to"
                                  u"'In Progress.Fazendo'",
                         u'formatted_message': u'msg fmted 2'},
                    ]
                }
            },
            {u'taskid': u'119',
             u'activities': {
                    u'2014-10-02 19:25:36': [
                        {u'author': u'pappacena',
                         u'event': u'Task moved',
                         u'text': u"From 'J\xe1 detalhados' to 'Backlog'",
                         u'formatted_message': u'msg fmted 3'},
                    ],
                    u'2014-10-02 19:26:36': [
                        {u'author': u'pappacena',
                         u'event': u'Task moved',
                         u'text': u"From 'Backlog' to 'J\xe1 detalhados'",
                         u'formatted_message': u'msg fmted 4'},
                    ],
                }
            },
            {u'taskid': u'121',
             u'activities': {
                    u'2014-10-02 19:36:36': [
                        {u'author': u'pappacena',
                         u'event': u'Assignee changed',
                         u'text': u'New assignee: marcel.portela',
                         u'formatted_message': u'msg fmted 5'}
                    ]
                }
            }
        ]
        self.assertEqual(exp_ret, ret)

    def test_parse_kambanize_activities_with_formatter(self):
        """
            test parse activities with some formatter function passed
            as argument
            simulatte the following data to be grouped and returned:
                - 2 activities in same task / date
        """
        #simulated formatter function to be used
        def new_formatter(data):
            return u'foo formated data'

        raw_data = {u'activities': [
            {u'author': u'marcel.portela',
             u'date': u'2014-10-02 20:21:06',
             u'event': u'Assignee changed',
             u'taskid': u'133',
             u'text': u'New assignee: marcel.portela'},
            {u'author': u'marcel.portela',
             u'date': u'2014-10-02 20:21:06',
             u'event': u'Task moved',
             u'taskid': u'133',
             u'text': u"From 'J\xe1 detalhados' to 'In Progress.Fazendo'"}
        ]}

        ret = self.obj._parse_kambanize_activities(raw_data, new_formatter)

        exp_ret = [
            {u'taskid': u'133',
             u'activities': {
                    u'2014-10-02 20:21:06': [
                        {u'author': u'marcel.portela',
                         u'event': u'Assignee changed',
                         u'text': u'New assignee: marcel.portela',
                         u'formatted_message': u'foo formated data'},
                        {u'author': u'marcel.portela',
                         u'event': u'Task moved',
                         u'text': u"From 'J\xe1 detalhados' to"
                                  u"'In Progress.Fazendo'",
                         u'formatted_message': u'foo formated data'},
                    ]
                }
            }
        ]
        self.assertEqual(exp_ret, ret)

if __name__ == '__main__':
    unittest.main()
