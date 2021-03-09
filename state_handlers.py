from bson import ObjectId
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler
import logging
from strings import locale
from database import Database

import pprint

logger = logging.getLogger(__name__)

# Conversation states
CHOICE_LANGUAGE, UPDATE_LANG, CHOICE_START, ASK_PHONE, ASK_DISASTER, ASK_LOCATION, HANDLE_REPORT, DESCRIBE = range(8)

db = Database()

# update_language and catch_update_language for when a user wants to change language at any point of time
# after he has registered


def update_language(update: Update, context: CallbackContext):
    language_keyboard = [[InlineKeyboardButton("Hello", callback_data="lang_en-in")],
                         [InlineKeyboardButton("नमस्ते", callback_data="lang_hi")],
                         [InlineKeyboardButton("નમસ્તે", callback_data="lang_guj")],
                         [InlineKeyboardButton("नमस्कार", callback_data="lang_mar")]]
    language_keyboard_markup = InlineKeyboardMarkup(language_keyboard)
    update.message.reply_text("Select a language", reply_markup=language_keyboard_markup)
    return UPDATE_LANG


def catch_update_language(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    query = update.callback_query
    lang = query.data
    context.user_data["lang"] = lang
    reporter = db.get_reporter(update.effective_user.id)
    if reporter:
        db.update_reporter(reporter["_id"], {"$set": {"platforms.Telegram.preferred_language": lang[5:]}})
    query.answer()
    query.delete_message()
    context.bot.send_message(chat_id=user_id, text=locale(lang[5:], "language_updated_message"))
    return ConversationHandler.END


def ask_language(update: Update, context: CallbackContext):
    reporter = db.get_reporter(update.effective_user.id)
    if reporter:
        # pprint.pprint(reporter)
        context.user_data["is_new_user"] = False
        context.user_data["reporter_id"] = reporter["_id"]
        # appending "lang_" to language code, because that is how we use it everywhere else (we slice the
        # first 5 characters)
        context.user_data["lang"] = "lang_" + reporter["platforms"]["Telegram"]["preferred_language"]
        context.user_data["phone_number"] = reporter["platforms"]["Telegram"]["phone_number"]
        logger.info("Skipping ask_language")
        return start(update, context, skip_set_language=True)
    # NEW USER -> ASK PREFERRED LANGUAGE
    context.user_data["lang"] = "en-in"
    context.user_data["is_new_user"] = True
    language_keyboard = [[InlineKeyboardButton("Hello", callback_data="lang_en-in")],
                         [InlineKeyboardButton("नमस्ते", callback_data="lang_hi")],
                         [InlineKeyboardButton("નમસ્તે", callback_data="lang_guj")],
                         [InlineKeyboardButton("નમસ્તે", callback_data="lang_mar")]]
    language_keyboard_markup = InlineKeyboardMarkup(language_keyboard)
    update.message.reply_text("Select a language", reply_markup=language_keyboard_markup)
    return CHOICE_LANGUAGE

# CHOICE_LANGUAGE routes to start where we catch the language selected by the user


def set_language(update: Update, context: CallbackContext):
    if update.callback_query:
        query = update.callback_query
        query.answer()
        context.user_data["lang"] = query.data


def start(update: Update, context: CallbackContext, skip_set_language=False):
    if skip_set_language is False:
        set_language(update, context)
    # slice the "lang_" out, in "lang_en-in" for example
    lang = context.user_data["lang"][5:]
    user_id = update.effective_user.id
    if context.user_data["is_new_user"] is True:
        greet = "greet_new"
    else:
        greet = "greet"
    disaster_keyboard = [[InlineKeyboardButton(locale(lang, "start_report_button"), callback_data="report")],
                         [InlineKeyboardButton(locale(lang, "start_webapp_button"), callback_data="goto_webapp")],
                         [InlineKeyboardButton(locale(lang, "cancel_button"), callback_data="cancel")]]
    disaster_keyboard_markup = InlineKeyboardMarkup(disaster_keyboard)
    context.bot.send_message(chat_id=user_id, text=locale(lang, greet), reply_markup=disaster_keyboard_markup)
    return CHOICE_START


def ask_phone(update: Update, context: CallbackContext):
    if context.user_data["is_new_user"] is False:
        return ask_location(update, context, skip_catch_phone=True)
    if update.callback_query:
        # Th next line stops the small loading icon animation seen on the keyboard
        query = update.callback_query
        query.answer()
        query.delete_message()
    lang = context.user_data["lang"][5:]
    phone_keyboard = [[KeyboardButton(locale(lang, "ask_phone_button"), request_contact=True)]]
    phone_reply_markup = ReplyKeyboardMarkup(phone_keyboard, one_time_keyboard=True)
    context.bot.send_message(chat_id=update.effective_user.id, text=locale(lang, "ask_phone_message"),
                             reply_markup=phone_reply_markup)
    return ASK_LOCATION


def catch_phone(update: Update, context: CallbackContext):
    number = update.effective_message.contact.phone_number
    context.user_data["phone_number"] = number


def ask_location(update: Update, context: CallbackContext, skip_catch_phone=False):
    if update.callback_query:
        # Th next line stops the small loading icon animation seen on the keyboard
        query = update.callback_query
        query.answer()
        query.delete_message()
    user_id = update.effective_user.id
    lang = context.user_data["lang"][5:]
    if skip_catch_phone is False:
        # catch the phone number from the update received then proceed with asking location
        catch_phone(update, context)
    location_keyboard = [[KeyboardButton(locale(lang, "ask_location_button"), request_location=True)]]
    location_reply_markup = ReplyKeyboardMarkup(location_keyboard, one_time_keyboard=True)
    # TODO 1 -> Add terms or information message telling user on why we ask for phone and location
    # context.bot.send_message(chat_id=user_id, text="Why do I need your location?")
    context.bot.send_message(chat_id=user_id, text=locale(lang, "ask_location_message"),
                             reply_markup=location_reply_markup)
    return ASK_DISASTER


def catch_location(update: Update, context: CallbackContext):
    coordinates = update.effective_message.location
    context.user_data["coordinates"] = [coordinates.longitude, coordinates.latitude]


def ask_disaster(update: Update, context: CallbackContext):
    # catch the location from the update received then proceed with asking disaster type
    catch_location(update, context)
    lang = context.user_data["lang"][5:]
    disaster_keyboard = [[InlineKeyboardButton(locale(lang, "disaster_earthquake"), callback_data="earthquake")],
                         [InlineKeyboardButton(locale(lang, "disaster_water_logging"), callback_data="water_logging")],
                         [InlineKeyboardButton(locale(lang, "cancel_button"), callback_data="cancel")]]
    disaster_reply_markup = InlineKeyboardMarkup(disaster_keyboard)
    update.message.reply_text(locale(lang, "ask_disaster_message"), reply_markup=disaster_reply_markup)
    return HANDLE_REPORT

# HANDLE_REPORT doesn't directly route to handle_report, see conversation_handler in conversation_handler.py


def handle_report(update: Update, context: CallbackContext, disaster_type: str, associated_disaster: ObjectId = None):
    # We could use print, doesn't matter
    logger.info(msg="We are handling earthquakes")
    if update.callback_query:
        # Th next line stops the small loading icon animation seen on the keyboard
        query = update.callback_query
        query.answer()
        query.delete_message()
    user_id = update.effective_user.id
    lang = context.user_data["lang"][5:]
    phone_number = context.user_data["phone_number"]
    if context.user_data["is_new_user"] is True:
        # Now we create the reporter since he has completed the entire report-filing process
        # create_user returns an id. This is the id of the reporter that was just created
        context.user_data["reporter_id"] = db.create_reporter(user_id, phone_number, lang)
    reporter_id = context.user_data["reporter_id"]
    coordinates = context.user_data["coordinates"]
    report_id = db.create_report(user_id, reporter_id, coordinates, disaster_type, associated_disaster)
    if report_id is False:
        context.bot.send_message(chat_id=user_id, text="Failed to file a report!")
    else:
        # save report_id to context data
        context.user_data["report_id"] = report_id
        no_keyboard = [[InlineKeyboardButton(text=locale(lang, "ask_description_no_button"),
                                             callback_data="no_description")]]
        no_keyboard_markup = InlineKeyboardMarkup(no_keyboard)
        context.bot.send_message(chat_id=user_id, text=locale(lang, "ask_description_message"), parse_mode="html",
                                 reply_markup=no_keyboard_markup)


def handle_earthquake_report(update: Update, context: CallbackContext):
    # do earthquake-specific stuff here. For e.g querying events.disasters for earthquakes near user
    # For @Priya
    # you will use mongodb find, so you will get a cursor object, like a list, you will have to iterate over it using
    # for loop even if there is just one result.
    # For the case, when there are multiple result you can also write a function that given a cursor object and
    # a coordinate, returns the quake which is closest.

    # associated_disaster = earthquake_near_user["_id"]
    # handle_report will also take a associated_disaster argument (see line 156)
    # You will get the _id of a disaster after making a geospatial query
    # finally, you would do,
    # handle_report(update, context, "earthquake", associated_disaster) instead of the next line
    handle_report(update, context, "earthquake")
    return DESCRIBE


def catch_description(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    lang = context.user_data["lang"][5:]
    description = update.message.text
    report_id = context.user_data["report_id"]
    update_result = db.update_report(report_id, {"properties.description.text": description})
    if update_result is True:
        context.bot.send_message(chat_id=user_id, text=locale(lang, "thank_you"))
    else:
        context.bot.send_message(chat_id=user_id, text=locale(lang, "description_error"))
    return ConversationHandler.END


def skip_description(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    lang = context.user_data["lang"][5:]
    update.callback_query.answer()
    context.bot.send_message(chat_id=user_id, text=locale(lang, "thank_you_no_description"))
    return ConversationHandler.END


def handle_water_logging_report(update: Update, context: CallbackContext):
    # call handle_report
    # do flood/water-logging related stuff here
    # once you call handle_report, you will have to change the below line to return DESCRIBE to go to DESCRIBE state
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext):
    if update.callback_query:
        update.callback_query.delete_message()
    context.bot.send_message(chat_id=update.effective_user.id, text="No problem!")
    return ConversationHandler.END
