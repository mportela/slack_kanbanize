# coding=utf-8


class Feeder(object):

    def __init__(self, kambanize_api_key, kambanize_board_id, slack_token,
                 slack_channel, slack_user='slackbot',
                 kambanize_timedelta_collect_minutes=2):
        """
            parameters:
            @kambanize_api_key - kambanize appi key to be used
            @kambanize_board_id - kambanize board_id to be monitored
            @kambanize_timedelta_collect_minutes - minutes to collect data from
                                                  N minutes before now
            @slack_token - slack token autorization to be used
            @slack_channel - slack channel to be used
            @slack_user - slack user to be used

            * - in slack free version there is a limit of "Limit per hour (per
                API KEY)" of 30 calls
                see https://kanbanize.com/ctrl_integration/ for details
        """
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
