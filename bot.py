"""
Project Name: 	DCroSS
Author List: 	Priya Pathak
Filename: 		bot.py
Description: 	Bot entrypoint
"""

import logging
from telegram.ext import Updater
from conversation_handler import conversation_handler
from config_vars import bot_token


def main():
    updater = Updater(bot_token, use_context=True)
    dispatcher = updater.dispatcher
    # Register the conversation handler with the updates dispatcher
    dispatcher.add_handler(conversation_handler)

    def error(update, context):
        logger.warning('Update "%s" caused error "%s"', update, context.error)

    dispatcher.add_error_handler(error)
    updater.start_polling()


# <----------------------- START BOT -------------------------->
if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.WARNING)
    logger = logging.getLogger(__name__)
    main()
