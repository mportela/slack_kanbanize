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

if __name__ == '__main__':
    unittest.main()
