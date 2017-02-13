import telegram
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater
from telegram import bot

import data
import data.clients
import packetFactory
from config import YAMLConfig
import plugins

gchatSettings = YAMLConfig("cfg/gchat.config.yml",
                           {'displayMode': 0, 'bubblePrefix': '', 'systemPrefix': '{whi}', 'prefix': ''}, True)
telegramSettings = YAMLConfig("cfg/telegram-bot.config.yml",
                              {'enabled': False, 'output': True, 'token': "", 'botId': ""}, True)

telegramBot = None
telegramEnabled = telegramSettings.get_key('enabled')
telegramToken = telegramSettings.get_key('token')
telegramOutput = telegramSettings.get_key('output')

if telegramEnabled:
    telegramUpdater = Updater(token=telegramToken)
    telegramDispatcher = telegramUpdater.dispatcher
    telegramBot = telegram.Bot(token=telegramToken)


def onReceiveTelegramChat(bot, update):
    msg = update.message.text
    if telegramOutput:
        print("[Telegram] <%s> %s" % (update.message.from_user.username, update.message.text))
    for client in data.clients.connectedClients.values():
        if client.preferences.get_preference('globalChat') and client.get_handle() is not None:
            if lookup_gchatmode(client.preferences) == 0:
                client.get_handle().send_crypto_packet(
                    packetFactory.TeamChatPacket(update.message.from_user.id,
                                                 "[Telegram] %s" % update.message.from_user.username,
                                                 "[Telegram] %s" % update.message.from_user.username, "%s%s" % (
                                                     client.preferences.get_preference('globalChatPrefix'),
                                                     msg.decode('utf-8', 'ignore'))).build())
            else:
                client.get_handle().send_crypto_packet(packetFactory.SystemMessagePacket("[Telegram] <%s> %s" % (
                    update.message.from_user.username, "%s%s" % (client.preferences.get_preference('globalChatPrefix'),
                                                                 msg.decode('utf-8', 'ignore'))), 0x3).build())

def count(bot, update):
    countMesage = "*[Command]* \nThere are %s user(s) currently connected to the proxy." % len(data.clients.connectedClients)
    bot.sendMessage(chat_id=update.message.chat_id, text=countMesage, parse_mode="Markdown")


def lookup_gchatmode(client_preferences):
    if client_preferences['gchatMode'] is not -1:
        return client_preferences['gchatMode']
    return gchatSettings['displayMode']


@plugins.on_start_hook
def onStart():
    if telegramEnabled:
        gChatHandler = MessageHandler(Filters.text, onReceiveTelegramChat)
        countHandler = CommandHandler("count", count)
        telegramDispatcher.add_handler(gChatHandler)
        telegramDispatcher.add_handler(countHandler)
        telegramUpdater.start_polling()
