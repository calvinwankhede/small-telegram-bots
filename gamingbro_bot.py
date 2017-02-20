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

GETPRICE = range(1)

def start(bot, update):
    msg = "Hey {username}, I'm {botname}. You can: \n\n"
    msg += "1) Search for all Counter Strike skins. Send a message that starts with 'Search for', followed by your search query.  \n"
    msg += "2) Obtain the median price of any skin. Send a message that starts with 'Price for', followed by your search query.\n"
    msg += "3) Get the inventory worth for any Steam user. Send a message that starts with 'Inventory', followed by the Steam community username."
    update.message.reply_text(msg.format(username=update.message.from_user.first_name, botname=bot.name), quote=False)

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

def searchlist(bot, update):
    skin = update.message.text[11:].lower()
    result = searchfile(skin)
    msg = ""
    if len(result) == 0:
        update.message.reply_text("Your search returned zero results. Please try as few words as possible, for example 'Redline' or 'Asiimov' or 'Hyper Beast'.", quote=False)
    elif len(result) > 50:
        update.message.reply_text("Your search returned >50 results. Please try keywords relating to the skin, for example 'Redline' or 'Asiimov' or 'Hyper Beast'.", quote=False)    
    else:
        for key, value in result.items():
            msg += "{}) {}\n".format(key, value)
        update.message.reply_text(msg, quote=False)

def pricequery(bot, update):
    skin = update.message.text[10:].lower()
    global result
    result = searchfile(skin)
    msg = ""
    customkeyboard = []
    first_row = []
    second_row = []
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
        for key in result:
            if int(key) <= 10:
                if int(key) <= 5:
                    first_row.append(key)
                if int(key) in range(6,11):
                    second_row.append(key)
        customkeyboard.append(first_row)
        customkeyboard.append(second_row)
        reply_markup = telegram.ReplyKeyboardMarkup(customkeyboard, one_time_keyboard=True)
        update.message.reply_text(msg, quote=False, reply_markup=reply_markup, parse_mode="Markdown")
    return GETPRICE

def currencyconversion():
    url = "http://api.fixer.io/latest?base=USD"
    r = requests.get(url)
    output = r.json()
    global available_currencies, exchange_rate
    available_currencies = []
    try:
        exchange_rate = output
        for key in output["rates"].items():
            available_currencies.append(key)
    except:
        return

def currencyset(bot, update, args):
    chatid = str(update.message.chat_id)
    update.message.reply_text("Attempting to set your chat to {}".format(args[0]), quote=False)
    with open("currencyprefs.txt", "r") as currencyprefs:
        for line in currencyprefs:
            if chatid in line:
                update.message.reply_text("Stop updating the currency, you dumbfuck", quote=False)


def getprice(bot, update):
    requested_currency = "USD"
    chatid = str(update.message.chat_id)
    with open("currencyprefs.txt", "r") as currencyprefs:
        for line in currencyprefs:
            if chatid in line:
                requested_currency = line[-4:].rstrip()
    global result, exchange_rate
    number = update.message.text
    query = result.get(number)
    reply_markup = telegram.ReplyKeyboardHide()
    if query != None:
        params = {'id': query}
        url = "http://csgobackpack.net/api/GetItemPrice"
        r = requests.get(url, params=params)
        output = r.json()
        if requested_currency == "USD":
            rounded_price = '{} {}'.format(output["median_price"], requested_currency)
        else:
            correct_price = float(output["median_price"]) * exchange_rate["rates"][requested_currency]
            rounded_price = '{0:,.2f}'.format(correct_price) + " " + requested_currency
        if output["success"] is True:
            update.message.reply_text("The median price for {} is {}.".format(query, rounded_price), quote=False, reply_markup=reply_markup)
        else:
            update.message.reply_text("An error occured, please check the name of the item or try again later.", quote=False, reply_markup=reply_markup)
        return ConversationHandler.END
    else:
        update.message.reply_text("You specified an invalid number. Start over.", quote=False, reply_markup=reply_markup)
        return ConversationHandler.END

def cancel(bot, update):
    update.message.reply_text('You know how to summon me.')
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

def main():
    currencyconversion()
    updater = Updater(config['configuration']['gamingbro_token'])
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(RegexHandler("^[Ss]earch for\s.*", searchlist))

    conv_handler = ConversationHandler(
        entry_points=[RegexHandler("^[Pp]rice for\s.*", pricequery)],

        states={
            GETPRICE: [RegexHandler("^[0-9]*", getprice)]
        },

        fallbacks=[RegexHandler("[Cc]ancel", cancel)]
    )
    dp.add_handler(conv_handler)

    dp.add_handler(RegexHandler("^[Ii]nventory\s.*", inventory))
    dp.add_handler(CommandHandler("currency", currencyset, pass_args=True))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()