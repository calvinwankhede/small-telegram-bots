import telegram
from telegram.ext import CommandHandler, Updater, RegexHandler
import re
import requests
import configparser

config = configparser.ConfigParser()
config.read('/etc/config.txt')

def start(bot, update):
    msg = "Hey {username}, I'm {botname}. You can: \n\n"
    msg += "1) Search for Counter Strike skins. Send a message that starts with 'Search for', followed by your search query.  \n"
    msg += """2) Obtain the average price of any skin. Send a message that starts with 'Price for', followed by your search query. Please note that this feature is experimental and you'll need exact names such as 'AK-47 | Redline (Field-Tested)'
            """
    update.message.reply_text(msg.format(username=update.message.from_user.first_name, botname=bot.name), quote=False)

def searchfile(query):
    found_skins = ""
    with open("csgoitems.txt") as itemlist:
        for line in itemlist:
            if re.search("{0}".format(query),line):
                print(line)
                found_skins += line
    return found_skins

def searchlist(bot, update):
    skin = update.message.text[11:]
    result = searchfile(skin)
    if len(result) == 0:
        update.message.reply_text("Not found", quote=False)
    elif len(result.split("\n")) >= 40:
        update.message.reply_text("More than 40 results found", quote=False)
    else:
        update.message.reply_text(result, quote=False)

def price(bot, update):
    query = update.message.text[10:]
    params = {'id': query}
    url = "http://csgobackpack.net/api/GetItemPrice/"
    r = requests.get(url, params=params)
    output = r.json()
    if output["success"] is True:
        update.message.reply_text("The median price for {} is ${}.".format(query, output["median_price"]), quote=False)
    else:
        update.message.reply_text("An error occured, please check the name of the item or try again later.", quote=False)

updater = Updater(config['configuration']['gamingbro_token'])
print(config['configuration']['gamingbro_token'])
dp = updater.dispatcher

dp.add_handler(CommandHandler("start", start))
dp.add_handler(RegexHandler("^[Ss]earch for\s.*", searchlist))
dp.add_handler(RegexHandler("^[Pp]rice for\s.*", price))
updater.start_polling()
updater.idle()