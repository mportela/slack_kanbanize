# coding=utf-8

from python_kanbanize.wrapper import Kanbanize
from pyslack import SlackClient


class Feeder(object):

    def __init__(self, kambanize_api_key, kambanize_board_id, slack_token,
                 slack_channel, slack_user='slackbot',
                 kambanize_timedelta_collect_minutes=2,
                 local_timediff=-3):
        """
            Arguments:
            @kambanize_api_key - kambanize appi key to be used
            @kambanize_board_id - kambanize board_id to be monitored
            @kambanize_timedelta_collect_minutes - minutes to collect data from
                                                  N minutes before now
            @slack_token - slack token autorization to be used
            @slack_channel - slack channel to be used
            @slack_user - slack user to be used
            @local_timediff - diference in local time hours from utc to present
                              datetime data returned

            obs: in slack free version there is a limit of "Limit per hour (per
                API KEY)" of 30 calls
                see https://kanbanize.com/ctrl_integration/ for details
        """
        self.local_timediff = local_timediff
        self.kambanize_opts = {
            'api_key': kambanize_api_key,
            'board_id': kambanize_board_id,
            'collect_minutes_timedelta': kambanize_timedelta_collect_minutes
        }
        self.slack_opts = {
            'token': slack_token,
            'channel': slack_channel,
            'user': slack_user
        }

    def _get_kambanize_board_activities(self, from_date, to_date):
        """
            Used to get python-kambanize.get_board_activities
            Arguments:
            @from_date - datetime object to be used in get_board_activities
            @to_date - datetime object to be used in get_board_activities
            Return a list with board activities
        """
        pass
