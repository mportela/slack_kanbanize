# coding=utf-8

import datetime

from dateutil import tz
from python_kanbanize.wrapper import Kanbanize
from pyslack import SlackClient


class Feeder(object):

    UTC_ZONE = tz.tzutc()
    LOCAL_ZONE = tz.tzlocal()

    def __init__(self, kanbanize_api_key, kanbanize_board_id, slack_token,
                 slack_channel, slack_user='slackbot',
                 kanbanize_timedelta_collect_minutes=2):
        """
            Arguments:
            @kanbanize_api_key - kanbanize appi key to be used
            @kanbanize_board_id - kanbanize board_id to be monitored
            @kanbanize_timedelta_collect_minutes - minutes to collect data from
                                                  N minutes before now
            @slack_token - slack token autorization to be used
            @slack_channel - slack channel to be used
            @slack_user - slack user to be used

            obs: in slack free version there is a limit of "Limit per hour (per
                API KEY)" of 30 calls
                see https://kanbanize.com/ctrl_integration/ for details
        """
        self.kanbanize_opts = {
            'api_key': kanbanize_api_key,
            'board_id': kanbanize_board_id,
            'collect_minutes_timedelta': kanbanize_timedelta_collect_minutes
        }
        self.slack_opts = {
            'token': slack_token,
            'channel': slack_channel,
            'user': slack_user
        }
        self.slack_client = SlackClient(slack_token)
        self.kanbanize_client = Kanbanize(kanbanize_api_key)

    def _get_kanbanize_board_activities(self, from_date, to_date):
        """
            Used to get python-kanbanize.get_board_activities
            Arguments:
            @from_date - datetime object to be used in get_board_activities
            @to_date - datetime object to be used in get_board_activities
            Return a list with board activities
        """

        from_date_aware = from_date.replace(tzinfo=Feeder.LOCAL_ZONE)
        from_dt_utc_string = from_date_aware.astimezone(
                                                    Feeder.UTC_ZONE).strftime(
                                                           "%Y-%m-%d %H:%M:%S")
        to_date_aware = to_date.replace(tzinfo=Feeder.LOCAL_ZONE)
        to_dt_utc_string = to_date_aware.astimezone(
                                                    Feeder.UTC_ZONE).strftime(
                                                           "%Y-%m-%d %H:%M:%S")

        return self.kanbanize_client.get_board_activities(
                                               self.kanbanize_opts['board_id'],
                                               from_dt_utc_string,
                                               to_dt_utc_string)

    def _post_slack_message(self, text, **params):
        """
            Used to post a message to the slack board configured in
            self.slack_opts, using SlackClient.chat_post_message
            Arguments:
            @text - string with string message
            @**params - optional extra kwargs to be passed to the slack api
            Return True if all ok with api communication
        """
        params.update({'username': self.slack_opts['user']})
        ret = self.slack_client.chat_post_message(self.slack_opts['channel'],
                                                  text,
                                                  **params)
        return ret[u'ok']

    @staticmethod
    def _default_message_formatter_function(activity_data):
        """
            Process the activitie object and Return the formatted_message for
            this activity
            Arguments:
            @activity_data - dict object with this format:
                            {u'event': u'Task updated',
                             u'text': u'New tag:', u'author': u'mportela'}
            Return the formatted_string for the activity, based in the 'event'
        """
        events_emoji_traslator = {
            u'Task archived': ':+1:',
            u'Assignee changed': ':octocat:',
            u'Comment added': ':speech_balloon:',
            u'Task moved': ':rocket:',
            u'Attachments updated': ':paperclip:',
            u'Task updated': ':pencil:',
            u'Task created': ':ticket:',
            u'External link changed': ':link:',
            u'Tags changed': ':triangular_flag_on_post:'
            }
        emoji = ''
        event = activity_data.get(u'event', u'')
        user = '*%s*' % activity_data.get(u'author', u'')
        text = activity_data.get(u'text', u'')
        try:
            emoji = '%s ' % events_emoji_traslator[event]
        except KeyError, e:
            # case of event not know, just return the name with italic format
            event = u'_%s_' % event

        msg = u"%sUser: %s Event: %s"\
              u": %s" % (emoji, user, event, text)

        return msg

    def _parse_kambanize_activities(self, raw_data,
                msg_formatter_function=_default_message_formatter_function):
        """
            Used to process activities, grouping by same taskid / date
            Arguments:
            @raw_data - raw_data returned from
                        kambanize._get_kanbanize_board_activities
            @msg_formatter_function - function to be used to format each msg
            Return list with objects grouped by taskid / date
            example of return:
            [{u'taskid': u'125',
              u'activities': {u'2014-09-30 19:01:31': [
                            {u'event': u'Task updated',
                             u'text': u'New tag:', u'author': u'mportela',
                             u'formatted_message': 'foo fmted'}]}
             },...]
        """
        pass
