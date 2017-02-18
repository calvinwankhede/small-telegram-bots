import logging
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import xkcd
import sqlite3
import configparser
import re

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read('/etc/config.txt')

xkcdexplanation = "Request an XKCD comic first with the /xkcd command."

def start(bot, update):
    msg = "Hey {username}, I'm {botname}. You can: \n\n"
    msg += "1) Request a random XKCD with /xkcd. \n"
    msg += "2) Access our shared to-do list with /list and add items to it with /add."
    update.message.reply_text(msg.format(username=update.message.from_user.first_name, botname=bot.name), quote=False)

# Start XKCD
def randomxkcd(bot, update):
    update.message.reply_text("One random XKCD comic, coming right up!", quote=False)
    randomcomic = xkcd.getRandomComic()
    getlink = randomcomic.getImageLink()
    comlink = str(getlink)
    update.message.reply_photo(comlink, caption="%s.\nReply with /xkcd_explain for an explanation."% (randomcomic.getTitle()),quote=False)
    global xkcdexplanation
    xkcdexplanation = str(randomcomic.getExplanation())
    return

def explanation(bot, update):
    update.message.reply_text(xkcdexplanation, quote=False)
# End XKCD

# Start list
def list():
    global msg
    msg = ""
    conn = sqlite3.connect('list.db')
    c = conn.cursor()
    listitems = c.execute('SELECT item FROM todo')
    i = 0
    try:
        for item in listitems:
            i += 1
            msg += "{}. {}\n".format(str(i), item[0])
    except:
        return
    conn.commit()
    conn.close()

def sendlist(bot, update):
    list()
    if len(msg) == 0:
        update.message.reply_text("Nothing has been added yet.", quote=False)
    else:
        update.message.reply_text(msg, quote=False)

# Start add
def additem(bot, update, args):
    conn = sqlite3.connect('list.db')
    c = conn.cursor()
    if len(args) == 0:
        update.message.reply_text("The command you entered is incomplete.", quote=False)
    else:
        for thing in args:
            c.execute("INSERT INTO todo VALUES (?)", (thing,))
        update.message.reply_text("Added successfully!\nReply with /list to see all items.", quote=False)
    conn.commit()
    conn.close()

# Start remove
def removeitem(bot, update, args):
    conn = sqlite3.connect('list.db')
    c = conn.cursor()
    if len(args) == 0:
        update.message.reply_text("The command you entered is incomplete.", quote=False)
    else:
        for thing in args:
            c.execute("DELETE from todo where ITEM='%s';"%(thing,))
        update.message.reply_text("Items removed successfully!", quote=False)
    conn.commit()
    conn.close()

def removeall(bot, update, args):
    conn = sqlite3.connect('list.db')
    c = conn.cursor()
    if len(args) == 0:
        update.message.reply_text("The command you entered is incomplete.", quote=False)
    elif args[0] == "YES":
        c.execute("DELETE from todo")
        update.message.reply_text("All items removed successfully! I hope you know what you just did...", quote=False)
    else:
        update.message.reply_text("The command you entered is incomplete.", quote=False)
    conn.commit()
    conn.close()

def log(bot, update):
    file = open("log.txt", "a")
    sender = update.message.from_user.first_name
    incoming_message = update.message.text.replace("/n", " ")
    edited_mess = re.sub(r'\n', r' ', incoming_message)
    file.write(sender + ": " + edited_mess + "\n")

def getlog(bot, update, args):
    if len(args) > 0:
        fileHandle = open ('log.txt',"r")
        lineList = fileHandle.readlines()
        fileHandle.close()
        x = int(args[0])
        update.message.reply_text(lineList[-x], quote=False)

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

def main():
    # login to Telegram with the bot token
    updater = Updater(config['configuration']['multipurpose_token'])
    dp = updater.dispatcher

    # handlers for all commands that this bot supports
    dp.add_handler(CommandHandler("start", start))
    # XKCD
    dp.add_handler(CommandHandler("xkcd", randomxkcd))
    dp.add_handler(CommandHandler("xkcd_explain", explanation))
    # list
    dp.add_handler(CommandHandler("list", sendlist))
    dp.add_handler(CommandHandler("add", additem, pass_args=True))
    dp.add_handler(CommandHandler("remove", removeitem, pass_args=True))
    dp.add_handler(CommandHandler("removeall", removeall, pass_args=True))

    dp.add_handler(MessageHandler(Filters.text, log))
    dp.add_handler(CommandHandler("print", getlog, pass_args=True))

    # miscellaneous
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
