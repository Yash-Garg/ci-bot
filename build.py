#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import configparser
import logging
import os
import subprocess

import time

import sys
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler
from telegram.ext.dispatcher import run_async
from telegram import InlineQueryResultArticle, ChatAction, InputTextMessageContent
from uuid import uuid4
import urllib.request

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read('bot.ini')

updater = Updater(token=config['KEYS']['bot_api'])
path = config['PATH']['path']
sudo_users = config['ADMIN']['sudo']
sudo_usernames =  config['ADMIN']['usernames']
dispatcher = updater.dispatcher


def id(bot, update):
    update.message.reply_text(str(update.message.chat_id))

def build(bot, update):
    if isAuthorized(update):
        bot.sendChatAction(chat_id=update.message.chat_id,
                           action=ChatAction.TYPING)
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Building and uploading to the chat")
        os.chdir(path)
        build_command = ['./build.sh']
        subprocess.call(build_command)
        filename = path + "out/" + open(path + ".final_ver").read().strip() + ".zip"
        bot.sendChatAction(chat_id=update.message.chat_id,
                           action=ChatAction.UPLOAD_DOCUMENT)
        bot.sendDocument(
            document=open(filename, "rb"),
            chat_id=update.message.chat_id)
    else:
        sendNotAuthorizedMessage(bot, update)


def upload(bot, update):
    if isAuthorized(update):
        bot.sendChatAction(chat_id=update.message.chat_id,
                           action=ChatAction.TYPING)
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Uploading to the chat")
        os.chdir(path + "/out")
        filename = path + "out/" + open(path + ".final_ver").read().strip() + ".zip"
        bot.sendChatAction(chat_id=update.message.chat_id,
                           action=ChatAction.UPLOAD_DOCUMENT)
        bot.sendDocument(
            document=open(filename, "rb"),
            chat_id=update.message.chat_id)
    else:
        sendNotAuthorizedMessage(bot, update)


def restart(bot, update):
    if isAuthorized(update):
        bot.sendMessage(update.message.chat_id, "Bot is restarting...")
        time.sleep(0.2)
        os.execl(sys.executable, sys.executable, *sys.argv)
    else:
        sendNotAuthorizedMessage(bot, update)

def ip(bot, update):
    with urllib.request.urlopen("https://icanhazip.com/") as response:
        bot.sendMessage(update.message.chat_id, response.read().decode('utf8'))

def update(bot, update):
    if isAuthorized(update):
        subprocess.call(['bash', 'update.sh'])
        restart(bot, update)

def execute(bot, update, direct=True):

    try:
        user_id = update.message.from_user.id
        command = update.message.text
        inline = False
    except AttributeError:
        # Using inline
        user_id = update.inline_query.from_user.id
        command = update.inline_query.query
        inline = True

    if isAuthorizedID(user_id, update.inline_query.from_user.name):
        if not inline:
            bot.sendChatAction(chat_id=update.message.chat_id,
                               action=ChatAction.TYPING)
        output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = output.stdout.read().decode('utf-8')
        output = '`{0}`'.format(output)

        if not inline:
            bot.sendMessage(chat_id=update.message.chat_id,
                        text=output, parse_mode="Markdown")
            return False

        if inline:
            return output
    else:
        return "Die " + update.inline_query.from_user.name

@run_async
def exec(bot, update, args):
    chat_id = update.message.chat_id
    command = update.message.text.replace('/exec ','')
    if isAuthorizedID(update.message.from_user.id, update.message.from_user.name):
        bot.sendChatAction(chat_id=update.message.chat_id,
                           action=ChatAction.TYPING)
        output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = output.stdout.read().decode('utf-8')
        output = '`{0}`'.format(output)

        bot.sendMessage(chat_id=update.message.chat_id,
                    text=output, parse_mode="Markdown")
    else:
        return "Don't try " + update.message.from_user.name

def inlinequery(bot, update):
    query = update.inline_query.query
    o = execute(query, update, direct=False)
    results = list()

    results.append(InlineQueryResultArticle(id=uuid4(),
                                            title=query,
                                            description=o,
                                            input_message_content=InputTextMessageContent(
                                                '*{0}*\n\n{1}'.format(query, o),
                                                parse_mode="Markdown")))

    bot.answerInlineQuery(update.inline_query.id, results=results, cache_time=10)

def isAuthorized(update):
    return str(update.message.from_user.id) in sudo_users or update.message.from_user.name in sudo_usernames

def isAuthorizedID(userid, username):
    return str(userid) in sudo_users and username in sudo_usernames

def sendNotAuthorizedMessage(bot, update):
    bot.sendChatAction(chat_id=update.message.chat_id,
                        action=ChatAction.TYPING)
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="@" + update.message.from_user.username + " isn't authorized for this task!")


build_handler = CommandHandler('build', build)
exec_handler = CommandHandler('exec', exec, pass_args=True)
upload_handler = CommandHandler('upload', upload)
restart_handler = CommandHandler('restart', restart)
id_handler = CommandHandler('id', id)
ip_handler = CommandHandler('ip', ip)
update_handler = CommandHandler('update', update)

dispatcher.add_handler(build_handler)
dispatcher.add_handler(upload_handler)
dispatcher.add_handler(restart_handler)
dispatcher.add_handler(InlineQueryHandler(inlinequery))
dispatcher.add_handler(id_handler)
dispatcher.add_handler(exec_handler)
dispatcher.add_handler(ip_handler)
dispatcher.add_handler(update_handler)

updater.start_polling()
updater.idle()
