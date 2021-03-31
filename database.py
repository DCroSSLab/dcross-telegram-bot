"""
Project Name: 	DCroSS
Author List: 	Priya Pathak, Faraaz Biyabani
Filename: 		database.py
Description: 	Database functions
"""


from datetime import datetime, timedelta
from pymongo import MongoClient
from config_vars import mongo_uri


class Database:
    def __init__(self):
        client = MongoClient(mongo_uri)
        # self.connection = client
        self.events = client.events
        self.test_events = client.dcross_test.earthquakes
        self.users = client.users
        self.reports = client.reports

    def get_reporter(self, telegram_user_id):
        users = self.users
        user = users.reporters.find_one({"platforms.Telegram.user_id": telegram_user_id})
        return user

    def update_reporter(self, reporter_id, updates: dict):
        users = self.users
        update_result = users.reporters.update_one({"_id": reporter_id}, updates)
        # return True if doc updated else return False
        if update_result.matched_count == 1:
            return True
        else:
            return False

    def create_reporter(self, telegram_user_id, phone_number, language_code):
        users = self.users
        user = {"create_datetime": datetime.now(),
                "platforms": {
                    "Telegram": {
                        "user_id": telegram_user_id,
                        "phone_number": phone_number,
                        "reports": [],
                        "preferred_language": language_code
                    }
                },
                "helpful_reports": [],
                "spam_warnings": 0,
                "is_banned": False
                }
        insert_result = users.reporters.insert_one(user)
        return insert_result.inserted_id

    def create_report(self, telegram_user_id, reporter_id, reporter_contact, coordinates, disaster_type,
                      associated_disaster=None, description=None):
        reports = self.reports
        report = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": coordinates
            },
            "properties": {
                "reporter_id": reporter_id,
                "source": {
                    "platform": "Telegram",
                    "user_id": telegram_user_id,
                    "bot_id": 1656561641,
                    "phone_number": reporter_contact
                },
                "disaster": {
                    "type": disaster_type,
                    "id": associated_disaster
                },
                "time": datetime.now(),
                "description": {
                    "text": description,
                    "images": []
                },
                "is_spam": False,
                "is_removed": False
            }
        }
        insert_result = reports.telegram.insert_one(report)
        report_id = insert_result.inserted_id
        update_reports = {"platforms.Telegram.reports": report_id}
        # Link the reporter to the report he filed
        update_result = self.update_reporter(reporter_id, {"$push": update_reports})
        # [Faraaz] Maybe see if matched_count of update_result should be equal to 1
        if report_id and update_result:
            # Return report_id if report id was created and linked with the reporter
            return report_id
        else:
            # else returns False, indicating failure
            return False

    def update_report(self, report_id, updates):
        reports = self.reports
        update_result = reports.telegram.update_one({"_id": report_id}, updates)
        if update_result:
            return True
        else:
            return False

    def get_recent_report(self, reporter_id):
        # Get a day recent report
        reports = self.reports
        time = datetime.now() - timedelta(days=1)
        result = reports.telegram.find({"$and": [{"properties.time": {"$gte": time}},
                                                 {"properties.reporter_id": reporter_id}]})\
            .sort([("properties.time", -1)])\
            .limit(1)
        if result:
            for item in result:
                return item
        else:
            return None
