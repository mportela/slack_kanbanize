# coding=utf-8
import argparse


def process():
    parser = argparse.ArgumentParser(description='Slack - Kanbanize feeder!!')

    parser.add_argument('--slack_token', nargs='?', help='slack token api',
                        required=True)
    parser.add_argument('--slack_channel', nargs='?',
                        help='slack channel to post', required=True)
    parser.add_argument('--slack_user', nargs='?',
                        help='slack username to post', default='slackbot')

    args = parser.parse_args()
