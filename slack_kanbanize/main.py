# coding=utf-8
import argparse
import datetime
import importlib

import feeder


def process():
    parser = argparse.ArgumentParser(description='Slack - Kanbanize feeder!!')

    parser.add_argument('--slack_token', nargs='?', help='slack token api',
                        required=True)
    parser.add_argument('--slack_channel', nargs='?',
                        help='slack channel to post', required=True)
    parser.add_argument('--slack_user', nargs='?',
                        help='slack username to post', default='slackbot')
    parser.add_argument('--kanbanize_api_key', nargs='?',
                        help='kanbanize api key to be used', required=True)
    parser.add_argument('--kanbanize_board_id', nargs='?',
                        help='kanbanize board id to colled activities from',
                        required=True)
    parser.add_argument('--kanbanize_timedelta_collect', nargs='?',
                        help='kanbanize collect past N minutes from now',
                        default='60')
    parser.add_argument('--kanbanize_message_formater', nargs='?',
                        help='optional kanbanize message formatter to be user')
    args = parser.parse_args()

    kanbanize_timedelta_collect =\
                datetime.timedelta(
                            minutes=int(args.kanbanize_timedelta_collect))
    kanbanize_message_formater = None
    # if external function formatter passed, import this and pass as argument
    if args.kanbanize_message_formater:
        try:
            external_module = args.kanbanize_message_formater.split('.')
            if len(external_module) >= 2:
                function_name = external_module[-1]
                del external_module[-1]
                module=importlib.import_module(".".join(external_module))
                kanbanize_message_formater = module.__getattribute__(
                                                                 function_name)
            else:
                print u'--kanbanize_message_formater arg must be a path to a'\
                      u' python external function, ex: "module.formatter"'
        except Exception, e:
            print u'Error with message format override, using default, error'\
                  u'was: %s' % e
            kanbanize_message_formater = None

    obj_feeder = feeder.Feeder(args.kanbanize_api_key, args.kanbanize_board_id,
                               args.slack_token, args.slack_channel,
                               args.slack_user, kanbanize_timedelta_collect,
                               kanbanize_message_formater)
    obj_feeder.run()
