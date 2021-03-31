"""
Project Name: 	DCroSS
Author List: 	Priya Pathak, Faraaz Biyabani
Filename: 		state_handlers.py
Description: 	Has functions that usually take an update and a CallbackContext type arguments,
                these functions define what happens in a particular conversation state.
"""


from datetime import datetime
from bson import ObjectId
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler
import logging

from config_vars import dir_images
from strings import locale
from database import Database
# import pprint

logger = logging.getLogger(__name__)

# Conversation states
CHOICE_LANGUAGE, UPDATE_LANG, CHOICE_START, ASK_PHONE, ASK_DISASTER, ASK_LOCATION, HANDLE_REPORT, DESCRIBE, IMAGE = \
    range(9)

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
        # Th next line stops the small loading/processing icon animation seen on the inline keyboard button
        query = update.callback_query
        query.answer()
        query.delete_message()
    user_id = update.effective_user.id
    lang = context.user_data["lang"][5:]
    phone_number = context.user_data["phone_number"]
    if context.user_data["is_new_user"] is True:
        # Now we create the reporter since he has completed the entire report-filing process
        # create_user returns an id. This is the id of the reporter that was just created.
        # language preferences are persisted in database, so that they can survive a bot restart,
        # since context.user_data will be lost.
        context.user_data["reporter_id"] = db.create_reporter(user_id, phone_number, lang)
    reporter_id = context.user_data["reporter_id"]
    coordinates = context.user_data["coordinates"]
    report_id = db.create_report(user_id, reporter_id, phone_number, coordinates, disaster_type, associated_disaster)
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
    # TODO -> Incomplete
    coordinates = context.user_data["coordinates"]
    earthquake_near_user = db.test_events.find_one({"geometry":
                                                        {"$within": {"$center": [coordinates, 0.0089992801]}}})
    if earthquake_near_user:
        "There IS an earthquake near the user"
        handle_report(update, context, "earthquake", earthquake_near_user["_id"])
        return DESCRIBE
    else:
        handle_report(update, context, "earthquake")
        return DESCRIBE


def catch_description(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    lang = context.user_data["lang"][5:]
    description = update.message.text
    report_id = context.user_data["report_id"]
    update_result = db.update_report(report_id, {"$set": {"properties.description.text": description}})
    if update_result is False:
        context.bot.send_message(chat_id=user_id, text=locale(lang, "description_error"))
    no_keyboard = [[InlineKeyboardButton(text=locale(lang, "ask_description_no_button"),
                                         callback_data="no_image")]]
    no_keyboard_markup = InlineKeyboardMarkup(no_keyboard)
    if datetime.now().strftime("image_%d%m%y") in context.user_data:
        for file_id in context.user_data[datetime.now().strftime("image_%d%m%y")]:
            # ignoring expecting str got None, None helps us in not sending a message for every single image
            # noinspection PyTypeChecker
            attach_photo_to_report(update, context, file_id, report_id, greet=None)
        context.bot.send_message(chat_id=user_id, text=locale(lang, "thank_you_more_information"))
        return ConversationHandler.END
    context.bot.send_message(chat_id=user_id, text="Do you have any images to share? Please send them now or press "
                                                   "\"No\"", reply_markup=no_keyboard_markup)
    return IMAGE


def skip_image(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    lang = context.user_data["lang"][5:]
    update.callback_query.answer()
    context.bot.send_message(chat_id=user_id, text=locale(lang, "thank_you_no_description"))
    return ConversationHandler.END


def skip_description(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    lang = context.user_data["lang"][5:]
    update.callback_query.answer()
    report_id = context.user_data["report_id"]
    # context.bot.send_message(chat_id=user_id, text=locale(lang, "thank_you_no_description"))
    no_keyboard = [[InlineKeyboardButton(text=locale(lang, "ask_description_no_button"),
                                         callback_data="no_image")]]
    no_keyboard_markup = InlineKeyboardMarkup(no_keyboard)
    if datetime.now().strftime("image_%d%m%y") in context.user_data:
        for file_id in context.user_data[datetime.now().strftime("image_%d%m%y")]:
            # ignoring expecting str got None, warning for time being
            # noinspection PyTypeChecker
            attach_photo_to_report(update, context, file_id, report_id, greet=None)
        context.bot.send_message(chat_id=user_id, text=locale(lang, "thank_you_more_information"))
        return ConversationHandler.END
    # need localization
    context.bot.send_message(chat_id=user_id, text="Do you have any images to share? Please send them now or press "
                                                   "\"No\"", reply_markup=no_keyboard_markup)
    return IMAGE


def handle_water_logging_report(update: Update, context: CallbackContext):
    # call handle_report
    # do flood/water-logging related stuff here
    # once you call handle_report, you will have to change the below line to return DESCRIBE to go to DESCRIBE state
    return ConversationHandler.END


def handle_images(update: Update, context: CallbackContext):
    # Currently, only adding images to only the latest report is possible.
    user_id = update.effective_user.id
    file_id = update.message.photo[-1].file_id
    new_media_group = True
    greet = None
    media_group_id = None
    # Maintain an image cache for handling multiple image updates
    # If a user sends multiple images, every image is received as an individual update
    # So we need to handle each update, depending on whether media_group_id is present or not
    payload = image_cache_maintenance(update, context)
    greet, new_media_group = payload[0], payload[1]
    # Now check if the current user is an existing reporter
    reporter = db.get_reporter(user_id)
    recent_report = None
    if reporter:
        recent_report = db.get_recent_report(reporter["_id"])
        context.user_data["is_new_user"] = False
        context.user_data["reporter_id"] = reporter["_id"]
        # appending "lang_" to language code, because that is how we consume it everywhere else (by slicing the
        # first 5 characters)
        context.user_data["lang"] = "lang_" + reporter["platforms"]["Telegram"]["preferred_language"]
        context.user_data["phone_number"] = reporter["platforms"]["Telegram"]["phone_number"]
    elif reporter is None:
        if new_media_group is True:
            # need localization
            context.bot.send_message(chat_id=user_id, text="You seem new! You are filing a report with the DCroSS Bot")
            state = ask_language(update, context)
            return state
    if recent_report:
        # User is an existing reporter, and has a recent report, so just attach photo to report and greet
        # greet is none if the photo is from an existing media_group, hence no message is sent to the user for THIS
        # image If the photo is first from a media_group, meaning a new media_group, greet is
        # thank_you_more_information. So, ultimately, when a user sends 3 images together, he is only greeted once.
        # if greet is not None:
        #     greet = "thank_you_more_information"
        attach_photo_to_report(update, context, file_id, recent_report["_id"], greet)
        return ConversationHandler.END
    else:
        # User is an existing reporter, but doesn't have any recent report, so send him to LOCATION state
        if new_media_group is True:
            state = ask_location(update, context, skip_catch_phone=True)
            return state
            # return ConversationHandler.END


def attach_photo_to_report(update: Update, context: CallbackContext, file_id: str, report_id,
                           greet="thank_you_more_information"):
    user_id = update.effective_user.id
    lang = context.user_data["lang"][5:]
    photo = context.bot.get_file(file_id)
    photo.download(dir_images + file_id + ".jpg")
    # payload = bson.encode({"directory": dir_images, "filename": file_id + ".jpg"})
    result = db.update_report(report_id, {"$push": {"properties.description.images": {
        "directory": dir_images,
        "filename": file_id,
        "extension": ".jpg"
    }}})
    if result is True and greet is not None:
        context.bot.send_message(chat_id=user_id, text=locale(lang, greet))
    elif result is False:
        # need localization
        context.bot.send_message(chat_id=user_id, text="There was some problem while attaching an image! "
                                                       "Your report is still filed.")


def image_cache_maintenance(update: Update, context: CallbackContext):
    file_id = update.message.photo[-1].file_id
    new_media_group = True
    # greet = None
    greet = "thank_you_more_information"
    media_group_id = None
    if update.message.media_group_id is not None:
        media_group_id = update.message.media_group_id
        if media_group_id in context.user_data:
            new_media_group = False
            greet = None
            context.user_data[media_group_id].append(file_id)
        else:
            context.user_data[media_group_id] = [file_id]
            # greet = "thank_you_more_information"
        context.user_data[datetime.now().strftime("image_%d%m%y")] = context.user_data[media_group_id]
    if media_group_id is None and datetime.now().strftime("image_%d%m%y") in context.user_data:
        # Single image sent, existing cache case
        context.user_data[datetime.now().strftime("image_%d%m%y")].append(file_id)
    elif media_group_id is None and datetime.now().strftime("image_%d%m%y") not in context.user_data:
        # Single image sent, no cache case
        context.user_data[datetime.now().strftime("image_%d%m%y")] = [file_id]
    return [greet, new_media_group]


def cancel(update: Update, context: CallbackContext):
    if update.callback_query:
        update.callback_query.delete_message()
    context.bot.send_message(chat_id=update.effective_user.id, text="No problem!")
    return ConversationHandler.END
