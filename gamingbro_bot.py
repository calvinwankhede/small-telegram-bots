import telegram
from telegram.ext import CommandHandler, Updater, RegexHandler, ConversationHandler
import re
import requests
import collections
import configparser

config = configparser.ConfigParser()
config.read('/etc/config.txt')
result = {}

GETPRICE = range(1)

def start(bot, update):
    msg = "Hey {username}, I'm {botname}. You can: \n\n"
    msg += "1) Search for all Counter Strike skins. Send a message that starts with 'Search for', followed by your search query.  \n"
    msg += "2) Obtain the median price of any skin. Send a message that starts with 'Price for', followed by your search query.\n"
    msg += "3) Get the inventory worth for any Steam user. Send a message that starts with 'Inventory', followed by the Steam community username."
    update.message.reply_text(msg.format(username=update.message.from_user.first_name, botname=bot.name), quote=False)

def searchfile(query):
    i = 1
    dictionary = collections.OrderedDict()
    with open("csgoitems.txt") as itemlist:
        for line in itemlist:
            if query in line.lower():
                dictionary[str(i)] = line.rstrip()
                i += 1
    return dictionary

def searchlist(bot, update):
    skin = update.message.text[11:].lower()
    result = searchfile(skin)
    msg = ""
    if len(result) == 0:
        update.message.reply_text("Your search returned zero results. Please try as few words as possible, for example 'Redline' or 'Asiimov' or 'Hyper Beast'.", quote=False)
    else:
        for key, value in result.items():
            msg += "{}) {}\n".format(key, value)
        update.message.reply_text(msg, quote=False)

def pricequery(bot, update):
    skin = update.message.text[10:].lower()
    global result
    result = searchfile(skin)
    msg = ""
    if len(result) == 0:
        update.message.reply_text("Your search returned zero results. Please try as few words as possible, for example 'Redline' or 'Asiimov' or 'Hyper Beast'.", quote=False)
        return ConversationHandler.END
    else:
        for key, value in result.items():
            msg += "{}) {}\n".format(key, value)
        msg += "\nReply with the skin number for the price or cancel. For example, reply '2'."
        update.message.reply_text(msg, quote=False)
    return GETPRICE

def getprice(bot, update):
    number = update.message.text
    global result
    query = result.get(number)
    if query != None:
        params = {'id': query}
        url = "http://csgobackpack.net/api/GetItemPrice"
        r = requests.get(url, params=params)
        output = r.json()
        if output["success"] is True:
            update.message.reply_text("The median price for {} is ${}.".format(query, output["median_price"]), quote=False)
        else:
            update.message.reply_text("An error occured, please check the name of the item or try again later.", quote=False)
        return ConversationHandler.END
    else:
        update.message.reply_text("You specified an invalid number. Start over.", quote=False)
        return ConversationHandler.END

def cancel(bot, update):
    update.message.reply_text('You know how to summon me.')
    return ConversationHandler.END

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

updater.start_polling()
updater.idle()