import telegram
from telegram.ext import CommandHandler, Updater, RegexHandler, ConversationHandler
import re
import requests
import collections
import configparser
import time

config = configparser.ConfigParser()
config.read('/etc/config.txt')
result = {}
exchange_rate = 0

SENDPRICE = range(1)

def start(bot, update):
    msg = "Hey {username}, I'm {botname}. You can: \n\n"
    msg += "1) Obtain the median price of any skin. Send a message that starts with 'Price for', followed by your search query.\n"
    msg += "2) Get the inventory worth for any Steam user. Send a message that starts with 'Inventory', followed by the Steam community username."
    update.message.reply_text(msg.format(username=update.message.from_user.first_name, botname=bot.name), quote=False)

def currencyconversion():
    url = "http://api.fixer.io/latest?base=USD"
    r = requests.get(url)
    try:
        exchange_rate = r.json()
        with open("currencies.txt", "w") as f:
            for currency, value in exchange_rate["rates"].items():
                f.write("{} {}\n".format(currency, value))
    except:
        return

def currencyset(bot, update, args):
    with open("currencies.txt", "r") as currencies:
        available_currencies = [x[0:3] for x in currencies]
    currency = args[0]
    update.message.reply_text("Attempting to set this chat's currency to {}".format(currency.upper()), quote=False)
    if currency.upper() in available_currencies:
        chatid = str(update.message.chat_id)
        with open("currencyprefs.txt", "r") as currencyprefs:
            for line in currencyprefs:
                if chatid in line:
                    update.message.reply_text("You have already set your currency to {}. This cannot be changed as of now. Please contact @Sharpened if you have to.".format(line[-4:]), quote=False)
                    return
        with open("currencyprefs.txt", "a") as currencyprefs:
            currencyprefs.write("{} {}\n".format(chatid, currency.upper()))
            update.message.reply_text("Currency was changed successfully.", quote=False)
    elif currency.upper() == "USD":
        update.message.reply_text("The default currency was USD. Why do you want to keep changing it, huh?", quote=False)
    else:
        update.message.reply_text("{} is not a valid currency, please try again.\nAcceptable forms are INR or CAD for example.".format(currency.upper()), quote=False)

def searchfile(query):
    i = 1
    keywords = query.lower().split() 
    dictionary = collections.OrderedDict()
    with open("csgoitems.txt") as itemlist:
        for line in itemlist:
            all_present = True
            for word in keywords:
                if word not in line.lower():
                    all_present = False
            if all_present == True:
                dictionary[str(i)] = line.rstrip()
                i += 1
    return dictionary

def getprice(skin, requested_currency, currency_rate):
    params = {'id': skin}
    url = "http://csgobackpack.net/api/GetItemPrice"
    r = requests.get(url, params=params)
    output = r.json()
    if requested_currency == "USD":
        rounded_price = '{} {}'.format(output["median_price"], requested_currency)
        return "The median price for {} is {}.".format(skin, rounded_price)
    elif output["success"] is True:
        correct_price = float(output["median_price"]) * currency_rate
        rounded_price = '{0:,.2f}'.format(correct_price) + " " + requested_currency
        return "The median price for {} is {}.".format(skin, rounded_price)
    else:
        return "Our contact with Steam's market seems to be broken due to too many requests, please try again in an hour."

def pricequery(bot, update):
    skin = update.message.text[10:].lower()
    global result
    result = searchfile(skin)
    msg = ""
    customkeyboard = []
    if len(result) == 0:
        update.message.reply_text("Your search returned zero results. Please try as few words as possible, for example 'Redline' or 'Asiimov' or 'Hyper Beast'.", quote=False)
        return ConversationHandler.END
    elif len(result) > 50:
        update.message.reply_text("Your search returned >50 results. Please try keywords relating to the skin, for example 'Redline' or 'Asiimov' or 'Hyper Beast'.", quote=False)
        return ConversationHandler.END
    else:
        for key, value in result.items():
            if int(key) in range(0, 11):
                msg += "{}) {}\n".format(key, value)
        if len(result) > 10:
            msg += "\n_Your search was automatically truncated to the first 10 results only._"
        first_row = [key for key in result if int(key) in range(0, 6)]
        second_row = [key for key in result if int(key) in range(6, 11)]
        customkeyboard.append(first_row)
        customkeyboard.append(second_row)
        reply_markup = telegram.ReplyKeyboardMarkup(customkeyboard, one_time_keyboard=True)
        update.message.reply_text(msg, quote=False, reply_markup=reply_markup, parse_mode="Markdown")
    return SENDPRICE

def sendprice(bot, update):
    requested_currency = "USD"
    currency_rate = 1
    chatid = str(update.message.chat_id)
    global result
    with open("currencyprefs.txt", "r") as currencyprefs:
        for line in currencyprefs:
            if chatid in line:
                requested_currency = line[-4:].rstrip()
                with open("currencies.txt", "r") as currencies:
                    for line in currencies:
                        if requested_currency in line:
                            currency_rate = float(line[4:].rstrip())
    query = result.get(update.message.text)
    if query != None:
        reply_markup = telegram.ReplyKeyboardRemove()
        response = getprice(query, requested_currency, currency_rate)
        update.message.reply_text(response, quote=False, reply_markup=reply_markup)
        return ConversationHandler.END
    else:
        update.message.reply_text("You specified an invalid number. Please start the search again.", quote=False, reply_markup=reply_markup)
        return ConversationHandler.END

def cancel(bot, update):
    reply_markup = telegram.ReplyKeyboardRemove()
    update.message.reply_text("You know how to summon me.", quote=False, reply_markup=reply_markup)
    return ConversationHandler.END

# Code for inventory check
def inventory(bot, update):
    account = update.message.text[10:]
    params = {'id': account}
    url = "http://csgobackpack.net/api/GetInventoryValue/"
    r = requests.get(url, params=params)
    output = r.json()
    if output["success"] == "true":
        update.message.reply_text("{}'s inventory value is ${}.".format(account, output["value"]), quote=False)
    else:
        update.message.reply_text("An error occured, please check the Steam ID and if the requested profile has a public inventory.", quote=False)

def overwatch(bot, update, args):
    if len(args) > 0:
        headers = {'User-Agent': 'GamingBro Bot for Telegram'}
        url = "https://owapi.net/api/v3/u/{}/stats".format(args[0])
        r = requests.get(url, headers=headers)
        try:
            output = r.json()
            player_competitive_stats = output["us"]["stats"]["competitive"]["overall_stats"]
            msg = "Stats for args[0] are:\n"
            msg += "Win rate: {}%\n".format(player_competitive_stats["win_rate"])
            msg += "Competitive Rank: {}\n".format(player_competitive_stats["comprank"])
            update.message.reply_text(msg, quote=False)
        except:
            update.message.reply_text("Sorry, invalid profile", quote=False)
    elif len(args) == 0:
        update.message.reply_text("Usage: /ow PlayerName", quote=False)

def main():
    currencyconversion()
    updater = Updater(config['configuration']['gamingbro_token'])
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    conv_handler = ConversationHandler(
        entry_points=[RegexHandler("^[Pp]rice for\s.*", pricequery)],

        states={
            SENDPRICE: [RegexHandler("^[0-9]*", sendprice)]
        },

        fallbacks=[CommandHandler("cancel", cancel)]
    )
    dp.add_handler(conv_handler)

    dp.add_handler(RegexHandler("^[Ii]nventory\s.*", inventory))
    dp.add_handler(CommandHandler("currency", currencyset, pass_args=True))
    dp.add_handler(CommandHandler("ow", overwatch, pass_args=True))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()