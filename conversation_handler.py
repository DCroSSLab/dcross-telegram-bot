from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

from state_handlers import *

# Conversation states
# These are imported from state_handlers, specifying here for convenience
# CHOICE_LANGUAGE, CHOICE_START, ASK_PHONE, ASK_DISASTER, ASK_LOCATION, HANDLE_REPORT = range(6)

# start_filters = Filters.text(["Hi", "Hello", "Need help"])
change_language_filters = Filters.regex("language")

conversation_handler = ConversationHandler(
    entry_points=[
        CommandHandler('start', ask_language),
        MessageHandler(change_language_filters, update_language),
        MessageHandler(Filters.text, ask_language)
    ],
    states={
        CHOICE_LANGUAGE: [
            CallbackQueryHandler(start, pattern="^lang_(.*)$")
        ],
        CHOICE_START: [
            CallbackQueryHandler(ask_phone, pattern="^report$"),
            CallbackQueryHandler(cancel, pattern="^goto_webapp$"),
            CallbackQueryHandler(cancel, pattern="^cancel$")
        ],
        ASK_LOCATION: [
            MessageHandler(Filters.contact, ask_location)
        ],
        ASK_DISASTER: [
            MessageHandler(Filters.location, ask_disaster)
        ],
        HANDLE_REPORT: [
            CallbackQueryHandler(handle_earthquake_report, pattern="^earthquake$"),
            CallbackQueryHandler(handle_water_logging_report, pattern="^water_logging$"),
            CallbackQueryHandler(cancel, pattern="^cancel$")
        ],
        DESCRIBE: [
            MessageHandler(Filters.text, catch_description),
            CallbackQueryHandler(skip_description, pattern="^no_description$")
        ],
        UPDATE_LANG: [
            CallbackQueryHandler(catch_update_language, pattern="^lang_(.*)")
        ]
    },
    fallbacks=[
        CommandHandler("cancel", cancel)
    ]
)
