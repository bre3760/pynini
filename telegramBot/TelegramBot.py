from telegram import (ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler)
from telegramBot.sensors_db import SensorsDB
import requests
import logging
import json
import time
import numpy as np

# https://iaassassari.files.wordpress.com/2012/07/panificazione.pdf

# IDEA: l'utente seleziona una tipologia di pane (comune, integrale, semola, etc..).
# Ciascuna tipologia è caratterizzata da uno specifico processo di lievitazione, si può monitorare temperatura, umidità, co2 emessa, (pH?)
# -> per ciascun tipo di pane: breve mex esplicativo, parametri ottimali di temp-umid-co2-pH, media valori reali
# Statistcihe relative alle vendite: diagrammi a torta presi da freeboard? oppure leggo valori da db e realizzo grafici python

# Mi serve un db per salvare dati relativi a ciascun tipo di pane e per plottare i dati sulle vendite

TYPOLOGY, PARAM, PARAMS, PARAM2, HOME, INFO, THRESHOLD, EXIT = range(8)

class TelegramBot(object):
    def __init__(self, db, port, token):
        self.telegramPort = port
        self.token = token
        self.db = db
        self.ip = "127.0.0.0"

    def start(self, update, context):

        self.chatID = update.message.chat_id
        requests.post("http://localhost:9090/addBot", json={'ip': self.ip, 'chat_ID': self.chatID, 'last_seen': time.time()})
        print("Mi sono registrato al catalog")

        options = ["White", "Wheat", "Gluten-free", "Sales Statistics"]
        reply_keyboard = []
        for elem in options:
            reply_keyboard.append([InlineKeyboardButton(elem, callback_data=elem)])
        reply_markup = InlineKeyboardMarkup(reply_keyboard)
        update.message.reply_text(
            text = ' <b> Hi {}! &#128522; Welcome to @Pynini! &#128523 </b> \
                    \nHere you can find information about different typologies of bread &#127838'.format(update.message.from_user.first_name), parse_mode = 'HTML')
        pass
        time.sleep(2)
        pass
        context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Choose the one you are interested in: ', reply_markup=reply_markup,
                                     parse_mode='Markdown')
        return TYPOLOGY


    def unknown(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='I could not understand the command you typed. &#128533; You wrote: {}'.format(
                                     update.message.text), parse_mode = 'HTML')


    def error(self, update, context):
        logger = logging.getLogger(__name__)
        logger.warning('Update "%s" caused error "%s"', update, context.error)


    def cancel(self, update, context):
        logger = logging.getLogger(__name__)
        user = update.message.from_user
        logger.info("User %s canceled the conversation.", user.first_name)
        update.message.reply_text(text = 'Bye! I hope we can talk again some day. &#128400;',
                                  reply_markup=ReplyKeyboardRemove(), parse_mode = 'HTML')

        return ConversationHandler.END

    def home(self, update, context):
        print("SONO IN HOME")
        options = ["White", "Wheat", "Gluten-free", "Sales Statistics"]
        reply_keyboard = []
        for elem in options:
            reply_keyboard.append([InlineKeyboardButton(elem, callback_data=elem)])
        reply_markup = InlineKeyboardMarkup(reply_keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Here you can find information about different typologies of bread &#127838 \
                                 \nChoose the one you are interested in: ',
                                 reply_markup=reply_markup, parse_mode='HTML')

        return TYPOLOGY

    def getParam(self, update, context):
        query = update.callback_query
        print("Ho selezionato %s: (getParam)", query.data)
        keyboard = [[InlineKeyboardButton("Temperature", callback_data='temp'),
                     InlineKeyboardButton("Humidity", callback_data='hum'),
                     InlineKeyboardButton("CO2", callback_data='co2'),
                     InlineKeyboardButton("Back", callback_data='home')],
                     [InlineKeyboardButton("Exit", callback_data='exit')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if query.data != 'home' and query.data != 'exit':
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='You have selected <b> {} </b> typology, now you have to select the parameter you want to investigate!'.format(query.data), parse_mode = 'HTML')
            pass
            time.sleep(2)
            pass
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='You can retrieve optimal and actual values for: <b> \n temperature,\n humidity, \n CO2 emitted, \n go back, \n or Exit </b>',
                                     reply_markup=reply_markup, parse_mode='HTML')
        self.type = query.data
        return PARAM

    def getActualParams(self, update, context):

        query = update.callback_query
        print("self.type", self.type)
        print("query.data in getActualParams", query.data)

        keyboard_params = [[InlineKeyboardButton("Temperature", callback_data='temp'),
                            InlineKeyboardButton("Humidity", callback_data='hum'),
                            InlineKeyboardButton("CO2", callback_data='co2'),
                            InlineKeyboardButton("Back", callback_data='home')
                            ],
                            [InlineKeyboardButton("Exit", callback_data='exit')]]

         # tramite get accedo al db per ritornare i parametri (ottimali e reali) richiesti dall'utente
        try:
             if query.data == 'home':
                 TYPOLOGY = self.home(update, context)
                 return TYPOLOGY

             elif query.data == 'exit':
                 res = self.exit(update, context)
                 return res

             elif query.data == 'co2' or query.data == 'temp' or query.data == 'hum':
                 self.selectedParam(update, context, query, keyboard_params)

        except Exception as e:
            try:
                self.error(update, context)
                reply_markup = InlineKeyboardMarkup(keyboard_params)
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text='Hey, an error occured. Wait a little bit, try again. &#128532;\
                                         \nTo try again, push one of the buttons below!',
                                         reply_markup=reply_markup, parse_mode='HTML')
                return PARAM2
            except:
                pass
                print(e)
                return PARAM2

        pass
        time.sleep(2)
        pass
        self.optionEnd(update, context)
        return PARAM2


    def selectedParam(self, update, context, query, keyboard_params):

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='You have chosen the <b> {} </b> parameter.'.format(query.data),
                                 parse_mode='HTML')

        if query.data == 'co2':
            res = self.sqlCO2()

        elif query.data == 'temp':
            res = self.sqlTemp()

        elif query.data == 'hum':
            res = self.sqlHum()

        best = res['best'][0]

        values = []
        for v in res['actualValues']:
            values.append(round(v[0], 2))
        #             # interrogo db su parametri ottimali e di temperatura per il tipo di pane
        #             # -> cerco in tabella "TEMP" il type = "TYPE" ed estraggo tutti i valori della colonna "value"
        # -> cerco in tabella "BEST" il type = "TYPE" ed estraggo il valore della colonna "temp"
        #                  [il mio db è costruito con tabelle per ogni parametro (temp, hum, co2) le cui colonne sono (timestamp, value, type = common, whole, gluten-free)]

        if values != []:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='The optimal value {} for the {} typology is: {}. \n The actual minimum is: {}, \n the actual maximum is: {}, \n the actual mean is: {}.'.format(
                                         query.data, self.type, best, min(values), max(values), round(np.mean(values), 2)))
            time.sleep(2)

        elif values == []:
            self.error(update, context)
            print("No data avaiable")
            reply_markup = InlineKeyboardMarkup(keyboard_params)
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Hey, an error occoured. Wait a little bit, try again. \nTo try again, push one of the buttons below!',
                                     reply_markup=reply_markup, parse_mode='Markdown')

        else:
            self.error(update, context)
            print("Error: something went wrong with your request. Try again!")
            reply_markup = InlineKeyboardMarkup(keyboard_params)
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Hey, an error occoured. Wait a little bit, try again. \nTo try again, push one of the buttons below!',
                                     reply_markup=reply_markup, parse_mode='Markdown')

    def sqlCO2(self):
        res = {}

        sql1 = '''select VALUE from co2 where TYPE = %s '''
        self.db.cursor.execute(sql1, [self.type])
        res['actualValues'] = self.db.cursor.fetchall()

        sql2 = '''select CO2 from best where TYPOLOGY = %s '''
        self.db.cursor.execute(sql2, [self.type])
        res['best'] = self.db.cursor.fetchone()

        return res

    def sqlTemp(self):
        res = {}

        sql1 = '''select VALUE from temperature where TYPE = %s '''
        self.db.cursor.execute(sql1, [self.type])
        res = self.db.cursor.fetchall()

        sql2 = '''select TEMPERATURE from best where TYPOLOGY = %s '''
        self.db.cursor.execute(sql2, [self.type])
        res['best'] = self.db.cursor.fetchall()

        return res

    def sqlHum(self):
        res = {}

        sql1 = '''select VALUE from humidity where TYPE = %s '''
        self.db.cursor.execute(sql1, [self.type])
        res['actualValues'] = self.db.cursor.fetchall()

        sql2 = '''select HUMIDITY from best where TYPOLOGY = %s '''
        self.db.cursor.execute(sql2, [self.type])
        res['best'] = self.db.cursor.fetchall()

        return res

    def sqlInfo(self):
        sql = '''select INFO from best where TYPOLOGY = %s '''
        self.db.cursor.execute(sql, [self.type])
        res = self.db.cursor.fetchall()

        return res

    def info(self, update, context):

        query = update.callback_query

        if query.data == 'home':
            TYPOLOGY = self.home(update, context)
            return TYPOLOGY

        elif query.data == 'info':
            link = self.sqlInfo()
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Click on the following link to learn more about the {}: {}.'.format(self.type, link))

            self.endMenu(update, context)

        elif query.data == 'thresholds':
            keyboard_thre = [[InlineKeyboardButton("Min temperature", callback_data='minTemp'),
                              InlineKeyboardButton("Max temperature", callback_data='maxTemp'),
                              InlineKeyboardButton("Min humidity", callback_data='minHum'),
                              InlineKeyboardButton("Max humidity", callback_data='maxHum'),
                              InlineKeyboardButton("Min co2", callback_data='minCO2'),
                              InlineKeyboardButton("Max co2", callback_data='maxCO2')]]

            # per come è strutturato il catalog, bisogna re-inserire le soglie di tutti i sensori:
            # posso interrogare il cataolg e copiare le soglie già in vigore per i sensori che non voglio modificare e
            # risettare solo le soglie che voglio aggiornare

            self.optionThresholds(update, context, keyboard_thre)


        elif query.data == 'exit':
            res = self.exit(update, context)
            return res

        pass
        time.sleep(2)

        return THRESHOLD

    def minTemp(self, update, context):

        user_input = update.effective_message.text.split()
        self.actual_thresh["min_temperature_th"] = user_input[1]

        requests.post("http://localhost:9090/setThresholds",
                     json=self.actual_thresh)

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='The new configuration of thresholds is: \
                                      \n- min Temperature: {}, \n - max Temperature: {}, \n - min Humidity: {}, \n - max Humidity: {}, \n - min CO2: {}, \n - max CO2: {}.\
                                      \nSelect the threshold you want to modify and type in the chat /<threshold> <value>: \
                                      \ne.g. /minTemperature 34'.format(self.actual_thresh["min_temperature_th"], self.actual_thresh["max_temperature_th"], self.actual_thresh["min_humidity_th"], self.actual_thresh["max_humidity_th"], self.actual_thresh["min_co2_th"], self.actual_thresh["max_co2_th"])
                        )

        self.optionEnd(update,context)

        return INFO

    def maxTemp(self, update, context):

        user_input = update.effective_message.text.split()
        self.actual_thresh["max_temperature_th"] = user_input[1]

        # requests.post("http://localhost:9090/setThresholds",
        #               json=self.actual_thresh)
        requests.put("http://localhost:9090/setThresholds",
                      json=self.actual_thresh)
        print("new config in maxTemp", self.actual_thresh)

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='The new configuration of thresholds is: \
                                      \n- min Temperature: {}, \n - max Temperature: {}, \n - min Humidity: {}, \n - max Humidity: {}, \n - min CO2: {}, \n - max CO2: {}.\
                                      \nSelect the threshold you want to modify and type in the chat /<threshold> <value>: \
                                      \ne.g. /minTemperature 34'.format(self.actual_thresh["min_temperature_th"], self.actual_thresh["max_temperature_th"], self.actual_thresh["min_humidity_th"], self.actual_thresh["max_humidity_th"], self.actual_thresh["min_co2_th"], self.actual_thresh["max_co2_th"])
                        )

        self.optionEnd(update,context)

        return INFO

    def minHum(self, update, context):

        user_input = update.effective_message.text.split()
        self.actual_thresh["min_humidity_th"] = user_input[1]

        requests.put("http://localhost:9090/setThresholds",
                     json=self.actual_thresh)

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='The new configuration of thresholds is: \
                                      \n- min Temperature: {}, \n - max Temperature: {}, \n - min Humidity: {}, \n - max Humidity: {}, \n - min CO2: {}, \n - max CO2: {}.\
                                      \nSelect the threshold you want to modify and type in the chat /<threshold> <value>: \
                                      \ne.g. /minTemperature 34'.format(self.actual_thresh["min_temperature_th"], self.actual_thresh["max_temperature_th"], self.actual_thresh["min_humidity_th"], self.actual_thresh["max_humidity_th"], self.actual_thresh["min_co2_th"], self.actual_thresh["max_co2_th"])
                        )

        self.optionEnd(update,context)

        return INFO

    def maxHum(self, update, context):

        user_input = update.effective_message.text.split()
        self.actual_thresh["max_humidity_th"] = user_input[1]

        requests.put("http://localhost:9090/setThresholds",
                     json=self.actual_thresh)

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='The new configuration of thresholds is: \
                                      \n- min Temperature: {}, \n - max Temperature: {}, \n - min Humidity: {}, \n - max Humidity: {}, \n - min CO2: {}, \n - max CO2: {}.\
                                      \nSelect the threshold you want to modify and type in the chat /<threshold> <value>: \
                                      \ne.g. /minTemperature 34'.format(self.actual_thresh["min_temperature_th"], self.actual_thresh["max_temperature_th"], self.actual_thresh["min_humidity_th"], self.actual_thresh["max_humidity_th"], self.actual_thresh["min_co2_th"], self.actual_thresh["max_co2_th"])
                        )

        self.optionEnd(update,context)

        return INFO

    def minCO2(self, update, context):

        user_input = update.effective_message.text.split()
        self.actual_thresh["min_co2_th"] = user_input[1]

        requests.put("http://localhost:9090/setThresholds",
                     json=self.actual_thresh)

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='The new configuration of thresholds is: \
                                      \n- min Temperature: {}, \n - max Temperature: {}, \n - min Humidity: {}, \n - max Humidity: {}, \n - min CO2: {}, \n - max CO2: {}.\
                                      \nSelect the threshold you want to modify and type in the chat /<threshold> <value>: \
                                      \ne.g. /minTemperature 34'.format(self.actual_thresh["min_temperature_th"], self.actual_thresh["max_temperature_th"], self.actual_thresh["min_humidity_th"], self.actual_thresh["max_humidity_th"], self.actual_thresh["min_co2_th"], self.actual_thresh["max_co2_th"])
                        )

        self.optionEnd(update,context)

        return INFO

    def maxCO2(self, update, context):

        user_input = update.effective_message.text.split()
        self.actual_thresh["max_co2_th"] = user_input[1]

        requests.put("http://localhost:9090/setThresholds",
                     json=self.actual_thresh)

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='The new configuration of thresholds is: \
                                      \n- min Temperature: {}, \n - max Temperature: {}, \n - min Humidity: {}, \n - max Humidity: {}, \n - min CO2: {}, \n - max CO2: {}.\
                                      \nSelect the threshold you want to modify and type in the chat /<threshold> <value>: \
                                      \ne.g. /minTemperature 34'.format(self.actual_thresh["min_temperature_th"], self.actual_thresh["max_temperature_th"], self.actual_thresh["min_humidity_th"], self.actual_thresh["max_humidity_th"], self.actual_thresh["min_co2_th"], self.actual_thresh["max_co2_th"])
                        )

        self.optionEnd(update,context)

        return INFO

    def optionThresholds(self, update, context, keyboard_thre):

        res = requests.get("http://localhost:9090/thresholds")
        for elem in json.loads(res.text):
            if elem['type'] == self.type:
                self.actual_thresh = elem
        print("sono in optionThresh", self.actual_thresh)

        minTemp = self.actual_thresh["min_temperature_th"]
        maxTemp = self.actual_thresh["max_temperature_th"]
        minHum = self.actual_thresh["min_humidity_th"]
        maxHum = self.actual_thresh["max_humidity_th"]
        minCo2 = self.actual_thresh["min_co2_th"]
        maxCo2 = self.actual_thresh["max_co2_th"]

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='This is the actual configuration for the * {} * bread typology: \
                                      \n- min Temperature: {},\
                                      \n- max Temperature: {},\
                                      \n- min Humidity: {}, \
                                      \n- max Humidity: {},\
                                      \n- min CO2: {},\
                                      \n- max CO2: {}.\
                                      \nSelect the threshold you want to modify and type in the chat \
                                      \n/<threshold> <value>: \
                                      \ne.g. /minTemperature 14'.format(self.type, minTemp, maxTemp, minHum, maxHum, minCo2, maxCo2),
                                 parse_mode='Markdown'
        )

    def optionEnd(self, update, context):
        print("sono in optionEnd")
        keyboard_info = [[InlineKeyboardButton("Tell Me More", callback_data='info'),
                          InlineKeyboardButton("Reset Thresholds", callback_data='thresholds'),
                          InlineKeyboardButton("Main menu", callback_data='home')],
                         [InlineKeyboardButton("Exit", callback_data='exit')]]
        reply_markup_info = InlineKeyboardMarkup(keyboard_info)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 reply_markup=reply_markup_info,
                                 text='If you want to reset some thresholds, click on <b> Reset Thresholds </b>,\
                                      \nif you want more information, click on <b> Tell me more </b> \
                                      \nif you want to come back to the main menu, click on <b> Main Menu </b>', parse_mode='HTML')

        return PARAM2

    def endMenu(self, update, context):
        print("sono in endMenu")
        keyboard_info = [[InlineKeyboardButton("Back", callback_data='home')],
                         [InlineKeyboardButton("Exit", callback_data='exit')]]
        reply_markup_info = InlineKeyboardMarkup(keyboard_info)
        context.bot.send_message(chat_id=update.effective_chat.id, reply_markup=reply_markup_info,
                                 text='If you want to explore other bread typologies, click on *Main menu!*',
                                 parse_mode='Markdown')
        #return THRESHOLD

    def end(self, update, context):

        print("query in end", update.callback_query.data)
        query = update.callback_query

        if query.data == 'home':
            TYPOLOGY = self.home(update, context)
            return TYPOLOGY

        elif query.data == 'info':
            link = self.sqlInfo()
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Click on the following link to learn more about the {}: {}.'.format(self.type, link))

            self.endMenu(update, context)

        elif query.data == 'exit':
            res = self.exit(update, context)

            return res

    def exit(self, update, context):

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Bye! Have a good day and come back to @Pynini soon. &#128400;',
                                 reply_markup=ReplyKeyboardRemove(), parse_mode='HTML')
        requests.post("http://localhost:9090/removeBot",
                      json={'ip': self.ip, 'chat_ID': self.chatID, 'last_seen': time.time()})
        print("Mi sono eliminato dal catalog")
        return ConversationHandler.END

    def main(self):

       upd= Updater(self.token, use_context=True)
       disp=upd.dispatcher
       logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
       logger = logging.getLogger(__name__)

       conv_handler = ConversationHandler(
           entry_points=[CommandHandler('start', self.start)],

           states={
               # devo dare la funzione successiva, è una sorta di indice che il codice deve seguire
               TYPOLOGY: [CallbackQueryHandler(self.getParam)],
               HOME: [CallbackQueryHandler(self.home)],
               PARAM: [CallbackQueryHandler(self.getActualParams)],
               PARAM2: [CallbackQueryHandler(self.info)],
               THRESHOLD: [CallbackQueryHandler(self.optionEnd)],
               INFO: [CallbackQueryHandler(self.end)]
           },

           fallbacks=[CommandHandler('cancel', self.cancel),
                      CommandHandler('home', self.home),
                      CommandHandler('exit', self.exit),
                      CommandHandler('minTemperature', self.minTemp),
                      CommandHandler('maxTemperature', self.maxTemp),
                      CommandHandler('minHumidity', self.minHum),
                      CommandHandler('maxHumidity', self.maxHum),
                      CommandHandler('minCO2', self.minCO2),
                      CommandHandler('minCO2', self.maxCO2)
                      ]
       )

       disp.add_handler(conv_handler)
       disp.add_handler(MessageHandler(Filters.all, self.unknown))

       upd.start_polling()
       upd.idle()


if __name__=='__main__':

    dataDB = requests.get("http://localhost:9090/db")
    db = SensorsDB(json.loads(dataDB.text))
    db.start()
    db.db.commit()
    #db.mydb.close()

    data = requests.get("http://localhost:9090/telegramBot")
    bot = TelegramBot(db, json.loads(data.text)["telegramPort"], json.loads(data.text)["token"])
    bot.main()

# TODO:
# file config con indirizzi url
# ritornare la nuova configurazione delle threshold tramite get
