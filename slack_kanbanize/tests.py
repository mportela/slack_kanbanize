# coding=utf-8

import unittest
import datetime
import json

import mock
from freezegun import freeze_time
from dateutil import tz
import feeder
from python_kanbanize.wrapper import Kanbanize
from pyslack import SlackClient


class LastShownMessageTests(unittest.TestCase):
    def test_save(self):
        pass


class TestFeederClass(unittest.TestCase):

    def setUp(self):
        self.obj = feeder.Feeder("foo_kanbanize_api_key", 4, "foo_slack_token",
                                 "foo_slack_channel")
        self.utc_zone = tz.tzutc()
        self.local_zone = tz.tzlocal()
        self.maxDiff = None

    def test_basic_instance(self):
        exp_kanbanize_opts = {
            'api_key': "foo_kanbanize_api_key",
            'board_id': 4,
            'collect_timedelta': datetime.timedelta(minutes=60),
            'kanbanize_message_fomatter': None
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

    @freeze_time("2012-01-14 10:00:00")
    @mock.patch.object(Kanbanize, 'get_board_activities')
    def test_get_kanbanize_board_activities_without_arguments(self,
                                                            mk_get_activities):
        mk_to_date = datetime.datetime.now()
        mk_from_date = datetime.datetime.now() -\
            self.obj.kanbanize_opts['collect_timedelta']

        mk_ret = [{'type': 'blah'}, {'type': 'blah'}, {'type': 'blah2'}]

        mk_get_activities.return_value = mk_ret
        ret = self.obj._get_kanbanize_board_activities()

        exp_from_date = mk_from_date.replace(tzinfo=self.local_zone)
        exp_from_date = exp_from_date.astimezone(self.utc_zone).strftime(
                                                        "%Y-%m-%d %H:%M:%S")
        exp_to_date = mk_to_date.replace(tzinfo=self.local_zone)
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

    def test_parse_kambanize_activities_with_nodata_msg(self):
        msg = u'No activities found for the specified board and time range.'\
              u' Make sure all parameters are set correctly.'
        ret = self.obj._parse_kambanize_activities(msg)
        self.assertEqual([], ret)

    @mock.patch('dateutil.tz.tzlocal')
    @mock.patch.object(feeder.Feeder, '_default_message_formatter_function')
    def test_parse_kambanize_activities_without_formatter(self, mk_formatter,
                                                          fake_local):
        """
            test parse activities with default formatter
            simulatte complex possibilities to be grouped and returned:
                - 2 activities in same task / date
                - 2 activities in same task / different dates
                - 1 activity in other task / date
        """
        fake_local.return_value = tz.tzoffset(None, -10800)
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
                 u'text': u'New assignee: marcel.portela',
                 u'formatted_message': u'msg fmted 1'}
            ),
            mock.call(
                {u'author': u'marcel.portela',
                 u'event': u'Task moved',
                 u'text': u"From 'J\xe1 detalhados' to 'In"
                          u" Progress.Fazendo'",
                 u'formatted_message': u'msg fmted 2'}
            ),
            mock.call(
                {u'author': u'pappacena',
                 u'event': u'Task moved',
                 u'text': u"From 'J\xe1 detalhados' to 'Backlog'",
                 u'formatted_message': u'msg fmted 3'}
            ),
            mock.call(
                {u'author': u'pappacena',
                 u'event': u'Task moved',
                 u'text': u"From 'Backlog' to 'J\xe1 detalhados'",
                 u'formatted_message': u'msg fmted 4'}
            ),
            mock.call(
                {u'author': u'pappacena',
                 u'event': u'Assignee changed',
                 u'text': u'New assignee: marcel.portela',
                 u'formatted_message': u'msg fmted 5'}
            )
        ]
        self.assertEqual(exp_calls, mk_formatter.call_args_list)

        # expected ret - 3 tasks
        exp_ret = [
            {u'taskid': u'133',
             u'activities': {
                    u'2014-10-02 17:21:06': [
                        {u'author': u'marcel.portela',
                         u'event': u'Assignee changed',
                         u'text': u'New assignee: marcel.portela',
                         u'formatted_message': u'msg fmted 1'},
                        {u'author': u'marcel.portela',
                         u'event': u'Task moved',
                         u'text': u"From 'J\xe1 detalhados' to"
                                  u" 'In Progress.Fazendo'",
                         u'formatted_message': u'msg fmted 2'},
                    ]
                }
            },
            {u'taskid': u'119',
             u'activities': {
                    u'2014-10-02 16:25:36': [
                        {u'author': u'pappacena',
                         u'event': u'Task moved',
                         u'text': u"From 'J\xe1 detalhados' to 'Backlog'",
                         u'formatted_message': u'msg fmted 3'},
                    ],
                    u'2014-10-02 16:26:36': [
                        {u'author': u'pappacena',
                         u'event': u'Task moved',
                         u'text': u"From 'Backlog' to 'J\xe1 detalhados'",
                         u'formatted_message': u'msg fmted 4'},
                    ],
                }
            },
            {u'taskid': u'121',
             u'activities': {
                    u'2014-10-02 16:36:36': [
                        {u'author': u'pappacena',
                         u'event': u'Assignee changed',
                         u'text': u'New assignee: marcel.portela',
                         u'formatted_message': u'msg fmted 5'}
                    ]
                }
            }
        ]
        self.assertEqual(exp_ret, ret)

    @mock.patch('dateutil.tz.tzlocal')
    def test_parse_kambanize_activities_with_formatter(self, fake_local):
        """
            test parse activities with some formatter function passed
            as argument
            simulatte the following data to be grouped and returned:
                - 2 activities in same task / date
        """
        fake_local.return_value = tz.tzoffset(None, -10800)
        # simulated formatter function to be used
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
                    u'2014-10-02 17:21:06': [
                        {u'author': u'marcel.portela',
                         u'event': u'Assignee changed',
                         u'text': u'New assignee: marcel.portela',
                         u'formatted_message': u'foo formated data'},
                        {u'author': u'marcel.portela',
                         u'event': u'Task moved',
                         u'text': u"From 'J\xe1 detalhados' to"
                                  u" 'In Progress.Fazendo'",
                         u'formatted_message': u'foo formated data'},
                    ]
                }
            }
        ]
        self.assertEqual(exp_ret, ret)

    def test_default_message_formatter_function_with_know_event(self):
        activity = {u'author': u'marcel.portela',
                    u'event': u'Assignee changed',
                    u'text': u'New assignee: marcel.portela'}

        formatted_str = feeder.Feeder._default_message_formatter_function(
                                                                    activity)

        exp_str = u":octocat: User: *marcel.portela* Event: Assignee"\
                  u" changed: New assignee: marcel.portela"

        self.assertEqual(exp_str, formatted_str)

    def test_default_message_formatter_function_with_unknow_event(self):
        activity = {u'author': u'marcel.portela',
                    u'event': u'Foo other event',
                    u'text': u'foo msg text'}

        formatted_str = feeder.Feeder._default_message_formatter_function(
                                                                    activity)

        exp_str = u"User: *marcel.portela* Event: _Foo other event_:"\
                  u" foo msg text"

        self.assertEqual(exp_str, formatted_str)

    def test_format_slack_messages(self):
        activities = [
            {u'taskid': u'133',
             u'activities': {
                    u'2014-10-02 20:21:06': [
                        {u'author': u'marcel.portela',
                         u'event': u'Assignee changed',
                         u'text': u'New assignee: marcel.portela',
                         u'formatted_message': u'foo formated data1'},
                        {u'author': u'marcel.portela',
                         u'event': u'Task moved',
                         u'text': u"From 'J\xe1 detalhados' to"
                                  u" 'In Progress.Fazendo'",
                         u'formatted_message': u'foo formated data2'}
                    ],
                    u'2014-10-02 20:31:06': [
                        {u'author': u'marcel.portela',
                         u'event': u'Assignee changed',
                         u'text': u'New assignee: marcel.portela',
                         u'formatted_message': u'foo formated data3'}
                    ]
                }
            },
            {u'taskid': u'134',
             u'activities': {
                    u'2014-10-02 20:22:06': [
                        {u'author': u'marcel.portela',
                         u'event': u'Assignee changed',
                         u'text': u'New assignee: marcel.portela',
                         u'formatted_message': u'foo formated data4'}
                    ]
                }
            }
        ]

        formatted = self.obj._format_slack_messages(activities)

        exp_result = [{u'color': u'good',
                       u'mrkdwn_in': [u'fields'],
                       u'fields': [
                            {
                            u'title': u'Message',
                            u'value': u'foo formated data1\nfoo formated data2'
                            },
                            {
                            u'title': u'Task',
                            u'value': u'<https://kanbanize.com/ctrl_board/4/'
                                      u'133|133>',
                            u'short': True
                            },
                            {
                            u'title': u'Date',
                            u'value': u'2014-10-02 20:21:06',
                            u'short': True
                            }
                         ]
                      },
                      {u'color': u'good',
                       u'mrkdwn_in': [u'fields'],
                       u'fields': [
                            {
                            u'title': u'Message',
                            u'value': u'foo formated data3'
                            },
                            {
                            u'title': u'Task',
                            u'value': u'<https://kanbanize.com/ctrl_board/4/'
                                      u'133|133>',
                            u'short': True
                            },
                            {
                            u'title': u'Date',
                            u'value': u'2014-10-02 20:31:06',
                            u'short': True
                            }
                         ]
                      },
                      {u'color': u'good',
                       u'mrkdwn_in': [u'fields'],
                       u'fields': [
                            {
                            u'title': u'Message',
                            u'value': u'foo formated data4'
                            },
                            {
                            u'title': u'Task',
                            u'value': u'<https://kanbanize.com/ctrl_board/4/'
                                      u'134|134>',
                            u'short': True
                            },
                            {
                            u'title': u'Date',
                            u'value': u'2014-10-02 20:22:06',
                            u'short': True
                            }
                         ]
                      }
                    ]
        self.assertEqual(exp_result, formatted)

    @mock.patch.object(feeder.Feeder, '_post_slack_message')
    @mock.patch.object(feeder.Feeder, '_format_slack_messages')
    @mock.patch.object(feeder.Feeder, '_parse_kambanize_activities')
    @mock.patch.object(feeder.Feeder, '_get_kanbanize_board_activities')
    def test_run(self, mk_get_kanbanize, mk_parse_kanbanize,
                 mk_format_messages, mk_post_message):

        mk_ret_kanbanize = mock.Mock()
        mk_get_kanbanize.return_value = mk_ret_kanbanize
        mk_ret_parse_kanbanize = mock.Mock()
        mk_parse_kanbanize.return_value = mk_ret_parse_kanbanize
        mk_ret_format = [{'foor': 'blah'}]
        mk_format_messages.return_value = mk_ret_format

        ret = self.obj.run()

        self.assertTrue(ret, "method should return True")
        mk_get_kanbanize.assert_called_once_with()
        mk_parse_kanbanize.assert_called_once_with(mk_ret_kanbanize,
            self.obj.kanbanize_opts['kanbanize_message_fomatter'])
        mk_format_messages.assert_called_once_with(mk_ret_parse_kanbanize)
        exp_final_call_args = {
                             'text': u"Kambanize --> Slack",
                             'icon_emoji': u':alien:',
                             'attachments': json.dumps(mk_ret_format)}
             
        mk_post_message.assert_called_with(**exp_final_call_args)

if __name__ == '__main__':
    unittest.main()
