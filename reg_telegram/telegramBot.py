#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler
)
import json
import logging
from io import StringIO

class StringIOHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.buffer = StringIO()

    def emit(self, record):
        msg = self.format(record)
        self.buffer.write(msg + '\n')

logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.INFO)
logging.getLogger("httpcore.http11").setLevel(logging.INFO)
logging.getLogger("apscheduler.scheduler").setLevel(logging.INFO)
logging.getLogger("httpcore.connection").setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram.ext.ExtBot").setLevel(logging.INFO)
logging.getLogger("telegram.ext.Updater").setLevel(logging.INFO)
logging.getLogger("telegram.ext.Application").setLevel(logging.INFO)

"""
Simple Bot to reply to Telegram messages.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

################################################################################
class RegTelegramBot:

    # _______________________________________________________________________________
    def get_user_id(self, update):
        return str(update.message.from_user.id)

    def get_user_first_name(self, update):
        return str(update.message.from_user.first_name)

    def get_user_full_name(self, update):
        return str(update.message.from_user.full_name)

    def get_user_alias(self, update):
        return str(update.message.from_user.name)

    def get_cmd(self, update):
        return str(update.message.text).lower()

    # _______________________________________________________________________________
    def isAdmin(self, update):
        if self.admin_id == self.get_user_id(update):
            return True
        else:
            logger.error("User id: " + self.get_user_id(update))
            return False

    # _______________________________________________________________________________
    async def ErrorHandler(self, update, context):
        """Log Errors caused by Updates."""
        logger.error(
            "ERROR HANDLER: Update "
            + str(update)
            + " caused error "
            + str(context.error)
        )

    # _______________________________________________________________________________
    async def Handler_help(self, update, context):
        if not self.isAdmin(update):
            return

        """Send a message when the command /help is issued."""
        text = "Usage:\n"
        text = text + "/hola /ola /hello - retorna la salutació\n"
        text = (
            text
            + "/rega /water <valve> [time=10] - rega durant <time> la valvula <valve>\n"
        )
        text = (
            text
            + "/open /close <valve> - activa o desactiva l'electrovalvula <valve>\n"
        )
        text = text + "/esp-gio <hostname> <gpio> <value>"
        # text = text + "/aemet\n"
        # text = text + "/todo\n"
        # text = text + "/done\n"
        # text = text + "/AddAdmin\n"
        # text = text + "/AddUser\n"
        # text = text + "/ShowAdmins\n"
        # text = text + "/ShowUsers\n"
        # text = text + "/ShowAllUsers\n"
        text = text + "/help: show this message"
        await update.message.reply_text(text)

    # _______________________________________________________________________________
    async def Handler_hello(self, update, context):
        logger.debug(update.message.chat.id)
        text = "Hola " + self.get_user_first_name(update) + " com estas?"
        await update.message.reply_text(text)

    # _______________________________________________________________________________
    async def Handler_reg(self, update, contex):
        if not self.isAdmin(update):
            return

        for reg in self.reg:
            #message_text = f'```json\n{self.reg[reg]}\n```'
            #await update.message.reply_text(message_text, parse_mode='Markdown')
            await update.message.reply_text(reg + ': ' + str(self.reg[reg]))

    # _______________________________________________________________________________
    async def Handler_log(self, update, contex):
        if not self.isAdmin(update):
            return

        cmd = self.get_cmd(update).split()
        ip = "0.0.0.0"
        port = "0"
        level = "DEBUG"
        if len(cmd) == 1:
            log = self.stringio_handler.buffer.getvalue()
            await update.message.reply_text(log)
        elif len(cmd) == 2:
            reg = str(cmd[1]).lower()
            if cmd[1] in self.reg:
                ip = self.reg[reg]['ip']
                port = self.reg[reg]['port']
            else:
                await update.message.reply_text(reg + ' unknown')
        elif len(cmd) == 3:
            reg = str(cmd[1]).lower()
            level = str(cmd[2]).upper()
            if cmd[1] in self.reg:
                ip = self.reg[reg]['ip']
                port = self.reg[reg]['port']
            else:
                await update.message.reply_text(reg + ' unknown')
        else:
            await update.message.reply_text('too many arguments')

        logger.debug('requested log ' + reg + '. Level: ' + level)
        ok, log = get_rest_log(ip, port, level=level)
        await update.message.reply_text(log)

    # _______________________________________________________________________________
    async def Handler_valves(self, update, contex):
        if not self.isAdmin(update):
            return
        
        if 'reg_valves' in self.reg:
            ip = str(self.reg['reg_valves']['ip'])
            port = str(self.reg['reg_valves']['port'])
            ok, valves = get_rest_valve_dict(ip, port)
            for valve in valves:
                await update.message.reply_text(valve + ': ' + str(valves[valve]))
        else:
            await update.message.reply_text("no reg_valve ip and port information")

    # _______________________________________________________________________________
    async def Handler_water(self, update, contex):
        import requests
        if not 'reg_valves' in self.reg:
            await update.message.reply_text("no reg_valve ip and port information")
            return

        cmd = self.get_cmd(update).split()
        valve = ''
        if len(cmd) == 2:
            valve = cmd[1]
        else:
            await update.message.reply_text("Command error: " + str(cmd) + ' (' + str(len(cmd)) + ')')
            return

        ip = str(self.reg['reg_valves']['ip'])
        port = str(self.reg['reg_valves']['port'])
        url = 'http://' + str(ip) + ':' + str(port) + '/reg'
        headers = {'Content-Type': 'application/json'}
        body = { "value" : "0", "valve" : valve, "duration_s" : "10"}
        logger.debug('PUT ' + url + ' ' + str(body))

        r = requests.put(url, headers=headers, data=json.dumps(body))
        #if r.status_code != requests.codes.ok:
        #    logging.error('GET ' + url + ' error: ' + r.status_code)
        #    return
        await update.message.reply_text("Returned: " + str(r.status_code))

    # _______________________________________________________________________________
    async def Handler_reset(self, update, contex):
        await update.message.reply_text("not supported")

    # Function to send a startup message_____________________________________________
    async def send_message(self, text):
        bot = Bot(token=self.token)
        await bot.send_message(chat_id=self.chat_id, text=text)

    # _______________________________________________________________________________
    def __init__(self, token, chat_id, admin_id, reg={}):
        self.token = token
        self.chat_id = chat_id

        #logger
        self.stringio_handler = StringIOHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.stringio_handler.setFormatter(formatter)
        logger.addHandler(self.stringio_handler)

        #reg_valves services
        self.reg = reg
        logging.debug('reg: ' + str(reg))

        logger.debug("Create the Updater and pass it your bot's token")
        self.chat_id = chat_id
        self.admin_id = admin_id
        application = Application.builder().token(token).build()

        logger.debug("declare different commands - answer in Telegram")
        application.add_handler(CommandHandler("help", self.Handler_help))
        application.add_handler(CommandHandler("help", self.Handler_hello))
        application.add_handler(CommandHandler("hola", self.Handler_hello))
        application.add_handler(CommandHandler("ola", self.Handler_hello))
        application.add_handler(CommandHandler("hello", self.Handler_hello))
        application.add_handler(CommandHandler("reg", self.Handler_reg))
        application.add_handler(CommandHandler("log", self.Handler_log))
        application.add_handler(CommandHandler("valves", self.Handler_valves))
        application.add_handler(CommandHandler("water", self.Handler_water))
        application.add_handler(CommandHandler("rega", self.Handler_water))
        application.add_handler(CommandHandler("reset", self.Handler_reset))

        logger.debug("log all errors")
        application.add_error_handler(self.ErrorHandler)

        # TODO: needs refactor, problems with await
        # Send the startup message
        # import asyncio
        # asyncio.run(self.send_message("The bot has started!"))

        logger.debug("Start the Bot")
        # Run the bot until the user presses Ctrl-C
        # We pass 'allowed_updates' handle *all* updates including `chat_member` updates
        # To reset this, simply pass `allowed_updates=[]`
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    def setValvesServer(self, reg):
        self.reg = reg
        logging.debug('reg: ' + str(self.reg))

### GET REST ########################################################################################################
# rest GET http://<ip>:<port>/valves/<vañve>
# returns <ok>, <dictioary>
# <ok> is true if communications was ok and a json was recieved from REST server
def get_rest_valve_dict(ip, port, valve=''):
    valves = {}
    url = 'http://' + str(ip) + ':' + str(port) + '/valves/' + str(valve)
    import requests
    try:
        r = requests.get(url)
        if r.status_code != requests.codes.ok:
            logging.error('GET ' + url + ' error: ' + r.status_code)
            return False, valves
        else:
            valves = r.json()
            return True, valves
    except Exception as e:
        logging.error("exception on GET " + url + ": " + e.__class__.__name__)
        return False, valves

### GET REST log ########################################################################################################
# rest GET http://<ip>:<port>/log?level=DEBUG
# returns <ok>, <string>
# <ok> is true if communications was ok and a json was recieved from REST server
def get_rest_log(ip, port, level='DEBUG'):
    valves = {}
    url = 'http://' + str(ip) + ':' + str(port) + '/log?level=' + level
    import requests
    try:
        r = requests.get(url)
        if r.status_code != requests.codes.ok:
            logging.error('GET ' + url + ' error: ' + r.status_code)
            return False, valves
        else:
            valves = r.json()
            return True, valves
    except Exception as e:
        logging.error("exception on GET " + url + ": " + e.__class__.__name__)
        return False, valves
