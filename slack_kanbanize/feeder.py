# coding=utf-8

import datetime
import copy
import json
import os

from dateutil import tz
from python_kanbanize.wrapper import Kanbanize
from pyslack import SlackClient


class Feeder(object):
    file_name = '.slack-kanbanize-last-msg'

    def __init__(self, kanbanize_api_key, kanbanize_board_id, slack_token,
                 slack_channel, slack_user='slackbot',
                 kanbanize_timedelta_collect=datetime.timedelta(minutes=60),
                 kanbanize_message_fomatter=None):
        """
            Arguments:
            @kanbanize_api_key - kanbanize appi key to be used
            @kanbanize_board_id - kanbanize board_id to be monitored
            @kanbanize_timedelta_collect - timedelta to collect data from
                                                  N time before now
            @kanbanize_message_fomatter - function to override the format of
                                          '_default_message_formatter_function'
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
            'collect_timedelta': kanbanize_timedelta_collect,
            'kanbanize_message_fomatter': kanbanize_message_fomatter
        }
        self.slack_opts = {
            'token': slack_token,
            'channel': slack_channel,
            'user': slack_user
        }
        self.slack_client = SlackClient(slack_token)
        self.kanbanize_client = Kanbanize(kanbanize_api_key)
        self.last_action_file = self._get_last_action_file()

    def _get_kanbanize_board_activities(self, from_date=None,
                                        to_date=None):
        """
            Used to get python-kanbanize.get_board_activities
            Arguments:
            @from_date - datetime object to be used in get_board_activities
            @to_date - datetime object to be used in get_board_activities
            Return a list with board activities
        """
        if not to_date:
            to_date = datetime.datetime.now()
        if not from_date:
            from_date = to_date - self.kanbanize_opts['collect_timedelta']
        UTC_ZONE = tz.tzutc()
        LOCAL_ZONE = tz.tzlocal()

        from_date_aware = from_date.replace(tzinfo=LOCAL_ZONE)
        from_dt_utc_string = from_date_aware.astimezone(
                                                    UTC_ZONE).strftime(
                                                           "%Y-%m-%d %H:%M:%S")
        to_date_aware = to_date.replace(tzinfo=LOCAL_ZONE)
        to_dt_utc_string = to_date_aware.astimezone(
                                                    UTC_ZONE).strftime(
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
            u'Task archived': u':+1:',
            u'Assignee changed': u':octocat:',
            u'Comment added': u':speech_balloon:',
            u'Task moved': u':rocket:',
            u'Attachments updated': u':paperclip:',
            u'Task updated': u':pencil:',
            u'Task created': u':ticket:',
            u'External link changed': u':link:',
            u'Tags changed': u':triangular_flag_on_post:'
            }
        emoji = u''
        event = activity_data.get(u'event', u'')
        user = u'*%s*' % activity_data.get(u'author', u'')
        text = activity_data.get(u'text', u'')
        try:
            emoji = u'%s ' % events_emoji_traslator[event]
        except KeyError, e:
            # case of event not know, just return the name with italic format
            event = u'_%s_' % event

        msg = u"%sUser: %s Event: %s"\
              u": %s" % (emoji, user, event, text)

        return msg

    def _parse_kanbanize_activities(self, raw_data,
                msg_formatter_function=None):
        """
            Used to process activities, grouping by same taskid / date
            Arguments:
            @raw_data - raw_data returned from
                        kanbanize._get_kanbanize_board_activities
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
        if u"No activities found for the specified board and time range" in\
            raw_data:
            return []
        if not msg_formatter_function:
            msg_formatter_function =\
                Feeder._default_message_formatter_function
        raw_activities = raw_data.get(u'activities', [])
        ret_list = []
        UTC_ZONE = tz.tzutc()
        LOCAL_ZONE = tz.tzlocal()

        last_date = self._get_last_action_time()
        new_last_date = last_date

        for raw_activity in raw_activities:
            # converting date comming from utc to local time
            date_in_naive_utc = datetime.datetime.strptime(
                                                  raw_activity[u'date'],
                                                  "%Y-%m-%d %H:%M:%S")
            date_in_aware_utc = date_in_naive_utc.replace(
                                                        tzinfo=UTC_ZONE)
            date_converted_local = date_in_aware_utc.astimezone(
                                                   LOCAL_ZONE).strftime(
                                                           "%Y-%m-%d %H:%M:%S")
            
            if new_last_date:
                if date_in_naive_utc > new_last_date:
                    new_last_date = date_in_naive_utc
            else:
                new_last_date = date_in_naive_utc

            if last_date:
                if date_in_naive_utc <= last_date:
                    continue
            
            activity = {
                u'author': raw_activity[u'author'],
                u'event': raw_activity[u'event'],
                u'text': raw_activity[u'text'],
                u'formatted_message': u''}
            activity[u'formatted_message'] = msg_formatter_function(activity)
            for item in ret_list:
                # if in result yet, update the date / activities
                if item[u'taskid'] == raw_activity[u'taskid']:
                    item[u'activities'].setdefault(date_converted_local, [])
                    item[u'activities'][date_converted_local].append(activity)
                    break
            else:
                # if not in result yet, add new task
                task = {
                    u'taskid': raw_activity[u'taskid'],
                    u'activities': {date_converted_local: [activity]},
                    }
                ret_list.append(task)

        self._save_last_action_time(new_last_date)

        return ret_list

    def _format_slack_messages(self, activities):
        """
            Used to process slack messages returned from
            '_parse_kanbanize_activities' and return formated messages as
            expected by slack api
            Arguments:
            @activities list of parsed kanbanize activities
            Return list with dicts of attachments in slack format
            see tests for example
        """
        ret_list = []
        attachment_template = {
                u'color': u'good',
                u'mrkdwn_in': [u'fields'],
                u'fields': [
                        {
                            u'title': u'Message',
                            u'value': u''
                        },
                        {
                            u'title': u'Task',
                            u'value': u'',
                            u'short': True
                        },
                        {
                            u'title': u'Date',
                            u'value': u'',
                            u'short': True
                        }
                ]
        }

        for activity in activities:
            for date in activity['activities']:
                attach = copy.deepcopy(attachment_template)
                attach[u'fields'][1][u'value'] =\
                    '<https://kanbanize.com/ctrl_board/%s/%s|%s>' %\
                            (self.kanbanize_opts['board_id'],
                             activity['taskid'], activity['taskid'])
                attach[u'fields'][2][u'value'] = date
                msgs = [item['formatted_message'] for item in activity[
                                                        'activities'][date]]
                attach[u'fields'][0][u'value'] = u'\n'.join(msgs)
                ret_list.append(attach)

        return ret_list

    def _get_last_action_file(self):
        home = os.path.expanduser('~')
        file_path = os.path.join(home, self.file_name)
        file = open(file_path, 'a+')
        file.seek(0)
        return file

    def _save_last_action_time(self, date):
        file = self.last_action_file

        file.truncate(0)
        file.write(date.strftime('%Y-%m-%dT%H:%M:%S.%f'))
        file.flush()

    def _get_last_action_time(self):
        file = self.last_action_file
        date_str = file.readline().strip()

        if not date_str:
            return None

        date = datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%f')
        return date

    def run(self):
        """
        Main method to start this Feeder to collect kanbanize activities
        and post the slack message with all collected data
        """
        raw_data = self._get_kanbanize_board_activities()
        activities = self._parse_kanbanize_activities(raw_data,
                            self.kanbanize_opts['kanbanize_message_fomatter'])
        attachments = self._format_slack_messages(activities)

        if attachments:
            kwargs = {
                'text': u"Kanbanize --> Slack",
                'icon_emoji': u':alien:',
                'attachments': json.dumps(attachments)
            }
            self._post_slack_message(**kwargs)

        self.last_action_file.flush()
        self.last_action_file.close()

        return True
