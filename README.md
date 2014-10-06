slack_kanbanize integration
===============

publish notifications on slack, of kambanize activity

see this projects to know more about the interfaces of slack and kambanize apps:

- api used to integrate with slack - https://github.com/mportela/pyslack
- api used to integrate with kambanize - https://github.com/mportela/python-kanbanize

#to run this app just create a script and call this in your crontab:
slack_kanbanize_feeder --slack_token xoxp-2 --slack_channel \#general --kanbanize_api_key asdasdasdsad --kanbanize_board_id 4 --kanbanize_timedelta_collect 60

#for example, to use an external message_formater, just pass the new --kanbanize_message_formater parameter:
slack_kanbanize_feeder --slack_token xoxp-2365845474-2368470509-2737497112-7f7415 --slack_channel G02N9TE7Y --kanbanize_api_key OQd1cjcrXqvLvY2BoCQ1WiawNIrf9QpKvqv2ffzf --kanbanize_board_id 4 --kanbanize_message_formater ispm_formatter.formatter --kanbanize_timedelta_collect 60

The examplo above used the plugin to make some specific format for each message, and for this example i have made an project showing how to do this "kanbanize_message_formater", here: https://github.com/mportela/slack_kanbanize_plugin_ispm


