strings = {
    "en-in": {
        "start_report_button": "Report a disaster",
        "start_webapp_button": "Visit the DCroSS Web App",
        "greet_new": "Hello! You have reached the DCroSS bot!\nI can help you report disasters.",
        "greet": "Hello again!",
        "ask_phone_button": "Share Phone Number",
        "ask_phone_message": "Please share your phone number by pressing the button that has come up",
        "ask_location_button": "Share Location",
        "ask_location_message": "Please share your location by pressing the button that has come up",
        "ask_description_message": "Can you describe the situation?\n"
                                   "<i>Send me a message describing the situation OR press No</i>",
        "ask_description_no_button": "No",
        "ask_disaster_message": "Which disaster do you face and want to report?",
        "disaster_earthquake": "Earthquake",
        "disaster_water_logging": "Water-logging",
        "description_error": "There was a problem while updating the description. Your report was still filed.",
        "thank_you": "Thank you for providing a detailed report!",
        "thank_you_no_description": "No problem!\nThanks for your time.",
        "cancel_button": "Cancel",
        "language_updated_message": "Language was updated to English (India)"
    },
    "hi": {
        "start_report_button": "आपदा की सूचना दें",
        "start_webapp_button": "DCroSS वेब ऐप पर जाएं",
        "greet_new": "हैलो! में DCroSS बॉट हू !\nमैं आपको आपदाओं की रिपोर्ट करने में मदद कर सकता हू।",
        "greet": "हैलो!",
        "ask_phone_button": "अपना फोन नंबर दें",
        "ask_phone_message": "क्रिपिया नीचे वाला बटन दबाकर अपना फोन नंबर शेयर करें",
        "ask_location_button": "अपना स्थान / लोकैशन शेयर करें ",
        "ask_location_message": "क्रिपिया नीचे वाला बटन दबाकर अपना स्थान / लोकैशन शेयर करें",
        "ask_description_message": "क्या आप स्थिति का वर्णन कर सकते हैं?\n"
                                   "<i>मुझे स्थिति का वर्णन करने वाला एक संदेश भेजें या नहीं दबाएं</i>",
        "ask_description_no_button": "नहीं",
        "ask_disaster_message": "आप किस आपदा का सामना कर रहे हैं और रिपोर्ट करना चाहते हैं?",
        "disaster_earthquake": "भूकंप",
        "disaster_water_logging": "जल भराव / पानी भरजाना",
        "description_error": "विवरण अपडेट करते समय एक समस्या होगई । आपकी रिपोर्ट फिर भी दर्ज की गई है ।",
        "thank_you": "एक विस्तृत रिपोर्ट प्रदान करने के लिए धन्यवाद!",
        "thank_you_no_description": "कोई बात नहीं!\nआपके समय के लिए धन्यवाद।",
        "cancel_button": "रद्द करें",
        "language_updated_message": "भाषा हिन्दी में बदल दी गई है।"
    }
}


def locale(lang, message):
    return strings[lang][message]
