# coding=utf-8

import unittest

import feeder


class TestSequenceFunctions(unittest.TestCase):

    def test_basic_instance(self):
        obj = feeder.Feeder("foo_kambanize_api_key", 3, "foo_slack_token",
                            "foo_slack_channel")
        exp_kambanize_opts = {
            'api_key': "foo_kambanize_api_key",
            'board_id': 3,
            'collect_minutes_timedelta': 2
        }
        exp_slack_opts = {
            'token': "foo_slack_token",
            'channel': "foo_slack_channel",
            'user': "slackbot"
        }
        self.assertEqual(exp_kambanize_opts, obj.kambanize_opts)
        self.assertEqual(exp_slack_opts, obj.slack_opts)
        self.assertEqual(-3, obj.local_timediff)

if __name__ == '__main__':
    unittest.main()
