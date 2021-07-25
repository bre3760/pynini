from telegram import (ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler)
import sys
sys.path.append('../')
import os

from database.query import ClientQuery
import requests
import logging
import json
import time
import numpy as np
import paho.mqtt.client as PahoMQTT

TYPOLOGY, PARAM, PARAMS, PARAM2, HOME, INFO, THRESHOLD, EXIT = range(8)

class TelegramBot(object):
    def __init__(self, port, token, ip, catalogPort):
        self.telegramPort = port
        self.token = token
        self.catalogIP = ip
        self.catalogPort = catalogPort
        

    def stop(self):
        self._paho_mqtt.unsubscribe(self.topic)
        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()

    def myOnConnect(self, paho_mqtt, userdata, flags, rc):
        print("Connected to %s with result code: %d" % (self.messageBroker, rc))

    def myPublish(self, message):
        # publish a message with a certain topic
        self._paho_mqtt.publish(self.topic, json.dumps(message), 2)

    def myOnMessageReceived(self, paho_mqtt, userdata, msg, update, context):
        # A new message is received: an alert is sent to the Telegram Bot
        print("Topic:'" + msg.topic + "', QoS: '" + str(msg.qos) + "' Message: '" + str(msg.payload) + "'")

        self.sendAlert(update, context, msg.topic, msg.payload)
        print("send Alert, msg.topic: ", msg.topic, msg.payload)

    def sendAlert(self, update, context, topic, msg):
        if msg['message'] == 'on':
            txt = 'ALERT! Your {} has been activate to improve the environmental conditions!'.format(topic)
        else:
            txt = 'ALERT! Your {} has been deactivate to improve the environmental conditions!'.format(topic)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=txt, parse_mode='HTML')

    def start(self, update, context):

        self._paho_mqtt = PahoMQTT.Client("bot", False)
        self._paho_mqtt.username_pw_set(username="brendan", password="pynini")

        self._paho_mqtt.on_connect = self.myOnConnect
        self._paho_mqtt.on_message = self.myOnMessageReceived
        r = requests.get(f"http://{self.catalogIP}:{self.catalogPort}/broker_ip_outside")
        self.messageBroker = json.loads(r.text)
        r = requests.get(f"http://{self.catalogIP}:{self.catalogPort}/active_arduino")
        self.topics = json.loads(r.text)
        # subscribe for a topic
        for t in self.topics:
            self._paho_mqtt.subscribe("trigger/"+t, 2) # magari prima di trigger per prendere per tutte le case
        print("Subscribed to: ", self.topics)

        self._paho_mqtt.connect(self.messageBroker, 1883)
        self._paho_mqtt.loop_start()

        self.chatID = update.message.chat_id
        requests.post(f"http://{self.catalogIP}:{self.catalogPort}/addBot", json={'ip': self.catalogIP, 'chat_ID': self.chatID, 'last_seen': time.time()})
        print("I'm registered to the catalog")

        update.message.reply_text(
            text = ' <b> Hi {}! &#128522; Welcome to @Pynini! &#128523 </b> \
                    \nHere you can find information about different typologies of bread &#127838'.format(update.message.from_user.first_name), parse_mode = 'HTML')
        pass
        time.sleep(2)
        pass

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Choose the *ID* of the case you are interested in and type it in the chat: \
                                      \n/caseID <your caseID>',
                                 parse_mode='Markdown')
        return TYPOLOGY

    def selectCaseID(self, update, context):
        '''
            The user selects the case typing the caseID
        '''

        user_input = update.effective_message.text.split()
        self.caseID = user_input[1]
        print("Chosen %s: ", self.caseID)

        if self.checkPresence():
            self.getParam(update, context)

        else:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='The selected caseID is not present in the catalog. &#128533; Check if it is correct, you wrote: {}'.format(
                                         self.caseID), parse_mode='HTML')
            self.home(update, context)

        return


    def checkPresence(self):
        '''
            Check if the selected caseID is present in the catalog
        '''

        allCasesID = []
        r = requests.get(f"http://{self.catalogIP}:{self.catalogPort}/cases")
        allCases = json.loads(r.text)

        for c in allCases:
            allCasesID.append(c['caseID'])

        if self.caseID in allCasesID:
            res = True
        else:
            res = False

        return res


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
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Choose the *ID* of the case you are interested in and type it in the chat: \
                                      \n/caseID <your caseID>',
                                 parse_mode='Markdown')
        return TYPOLOGY

    def getParam(self, update, context):
        '''
            Once the caseID has been chosen, the user decides the parameter he/she wants to check (temperature, co2, humidity)
        '''

        keyboard = [[InlineKeyboardButton("Temperature", callback_data='temperature'),
                     InlineKeyboardButton("Humidity", callback_data='humidity'),
                     InlineKeyboardButton("CO2", callback_data='co2'),
                     InlineKeyboardButton("Back", callback_data='home')],
                     [InlineKeyboardButton("Exit", callback_data='exit')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='You have selected the case <b> {} </b>, now you have to select the parameter you want to investigate!'.format(self.caseID), parse_mode = 'HTML')
        pass
        time.sleep(2)
        pass
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='You can retrieve optimal and actual values for: <b> \n temperature,\n humidity, \n CO2 emitted, \n go back, \n or Exit </b>',
                                 reply_markup=reply_markup, parse_mode='HTML')

        params = {'caseID': self.caseID}

        r = requests.get(f"http://{self.catalogIP}:{self.catalogPort}/category", params=params)
        print("Response from getPARAM: ",json.loads(r.text))
        self.category = json.loads(r.text)

        return PARAM

    def getActualParams(self, update, context):

        query = update.callback_query

        keyboard_params = [[InlineKeyboardButton("Temperature", callback_data='temperature'),
                            InlineKeyboardButton("Humidity", callback_data='humidity'),
                            InlineKeyboardButton("CO2", callback_data='co2'),
                            InlineKeyboardButton("Back", callback_data='home')
                            ],
                            [InlineKeyboardButton("Exit", callback_data='exit')]]
        print("in getActualParams query data: ", query.data)
        try:
            print("in TRY IN getActualParams")
            if query.data == 'home':
                TYPOLOGY = self.home(update, context)
                return TYPOLOGY

            elif query.data == 'exit':
                res = self.exit(update, context)
                return res

            elif query.data == 'co2' or query.data == 'temperature' or query.data == 'humidity':
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
        '''
            Data are retrieved from InfluxDB, where the measurements sent by sensors are stored 
        '''

        param = query.data
        print(f"In selected param, with param {query.data}")

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='You have chosen the <b> {} </b> parameter.'.format(param),
                                 parse_mode='HTML')

        print(f"Before ClientQUery INIT")
        self.clientQuery = ClientQuery(sensor = param, category = self.category, caseID = self.caseID)
        actualValues = self.clientQuery.getData()
        print(f"actualValues in selectedParam {actualValues}")
        best = self.clientQuery.getBest()

        if actualValues != []:
            print(f"actualValues in selectedParam is not an empty list {actualValues}")

            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='The optimal {} value for the {} typology is: {}. \n The actual is: {}.'.format(
                                         param, self.category, best, actualValues[0]))
            time.sleep(2)

        elif actualValues == []:
            print(f"actualValues in selectedParam is an empty list {actualValues}")
            self.error(update, context)
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


    def info(self, update, context):
        '''
            The user can see the actual thresholds, retrieve an info link about the bread typology or come back to the home menu
        '''

        query = update.callback_query

        if query.data == 'home':
            TYPOLOGY = self.home(update, context)
            return TYPOLOGY

        elif query.data == 'info':
            link = self.clientQuery.getLink()
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Click on the following link to learn more about the {}: {}.'.format(self.category, link))

            self.endMenu(update, context)

        elif query.data == 'thresholds':
            keyboard_thre = [[InlineKeyboardButton("Min temperature", callback_data='minTemp'),
                              InlineKeyboardButton("Max temperature", callback_data='maxTemp'),
                              InlineKeyboardButton("Min humidity", callback_data='minHum'),
                              InlineKeyboardButton("Max humidity", callback_data='maxHum'),
                              InlineKeyboardButton("Min co2", callback_data='minCO2'),
                              InlineKeyboardButton("Max co2", callback_data='maxCO2')]]

            self.optionThresholds(update, context)


        elif query.data == 'exit':
            res = self.exit(update, context)
            return res

        pass
        time.sleep(2)

        return THRESHOLD

    def minTemp(self, update, context):

        user_input = update.effective_message.text.split()
        self.actual_thresh["min_temperature_th"] = user_input[1]

        requests.post(f"http://{self.catalogIP}:{self.catalogPort}/setThresholds",
                     json=self.actual_thresh)

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='The new configuration of thresholds is: \
                                      \n- min Temperature: {}, \n - max Temperature: {}, \n - min Humidity: {}, \n - max Humidity: {}, \n - min CO2: {}, \n - max CO2: {}.\
                                      \nSelect the threshold you want to modify and type in the chat /<threshold> <value>: \
                                      \ne.g. /minTemperature 14'.format(self.actual_thresh["min_temperature_th"], self.actual_thresh["max_temperature_th"], self.actual_thresh["min_humidity_th"], self.actual_thresh["max_humidity_th"], self.actual_thresh["min_co2_th"], self.actual_thresh["max_co2_th"])
                        )

        self.optionEnd(update,context,first=False)

        return INFO

    def maxTemp(self, update, context):

        user_input = update.effective_message.text.split()
        self.actual_thresh["max_temperature_th"] = user_input[1]

        requests.put(f"http://{self.catalogIP}:{self.catalogPort}/setThresholds",
                      json=self.actual_thresh)

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='The new configuration of thresholds is: \
                                      \n- min Temperature: {}, \n - max Temperature: {}, \n - min Humidity: {}, \n - max Humidity: {}, \n - min CO2: {}, \n - max CO2: {}.\
                                      \nSelect the threshold you want to modify and type in the chat /<threshold> <value>: \
                                      \ne.g. /minTemperature 14'.format(self.actual_thresh["min_temperature_th"], self.actual_thresh["max_temperature_th"], self.actual_thresh["min_humidity_th"], self.actual_thresh["max_humidity_th"], self.actual_thresh["min_co2_th"], self.actual_thresh["max_co2_th"])
                        )

        self.optionEnd(update, context, first=False)

        return INFO

    def minHum(self, update, context):

        user_input = update.effective_message.text.split()
        self.actual_thresh["min_humidity_th"] = user_input[1]

        requests.put(f"http://{self.catalogIP}:{self.catalogPort}/setThresholds",
                     json=self.actual_thresh)

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='The new configuration of thresholds is: \
                                      \n- min Temperature: {}, \n - max Temperature: {}, \n - min Humidity: {}, \n - max Humidity: {}, \n - min CO2: {}, \n - max CO2: {}.\
                                      \nSelect the threshold you want to modify and type in the chat /<threshold> <value>: \
                                      \ne.g. /minTemperature 14'.format(self.actual_thresh["min_temperature_th"], self.actual_thresh["max_temperature_th"], self.actual_thresh["min_humidity_th"], self.actual_thresh["max_humidity_th"], self.actual_thresh["min_co2_th"], self.actual_thresh["max_co2_th"])
                        )

        self.optionEnd(update,context,first=False)

        return INFO

    def maxHum(self, update, context):

        user_input = update.effective_message.text.split()
        self.actual_thresh["max_humidity_th"] = user_input[1]

        requests.put(f"http://{self.catalogIP}:{self.catalogPort}/setThresholds",
                     json=self.actual_thresh)

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='The new configuration of thresholds is: \
                                      \n- min Temperature: {}, \n - max Temperature: {}, \n - min Humidity: {}, \n - max Humidity: {}, \n - min CO2: {}, \n - max CO2: {}.\
                                      \nSelect the threshold you want to modify and type in the chat /<threshold> <value>: \
                                      \ne.g. /minTemperature 14'.format(self.actual_thresh["min_temperature_th"], self.actual_thresh["max_temperature_th"], self.actual_thresh["min_humidity_th"], self.actual_thresh["max_humidity_th"], self.actual_thresh["min_co2_th"], self.actual_thresh["max_co2_th"])
                        )

        self.optionEnd(update,context,first=False)

        return INFO

    def minCO2(self, update, context):

        user_input = update.effective_message.text.split()
        self.actual_thresh["min_co2_th"] = user_input[1]

        requests.put(f"http://{self.catalogIP}:{self.catalogPort}/setThresholds",
                     json=self.actual_thresh)

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='The new configuration of thresholds is: \
                                      \n- min Temperature: {}, \n - max Temperature: {}, \n - min Humidity: {}, \n - max Humidity: {}, \n - min CO2: {}, \n - max CO2: {}.\
                                      \nSelect the threshold you want to modify and type in the chat /<threshold> <value>: \
                                      \ne.g. /minTemperature 14'.format(self.actual_thresh["min_temperature_th"], self.actual_thresh["max_temperature_th"], self.actual_thresh["min_humidity_th"], self.actual_thresh["max_humidity_th"], self.actual_thresh["min_co2_th"], self.actual_thresh["max_co2_th"])
                        )

        self.optionEnd(update,context,first=False)

        return INFO

    def maxCO2(self, update, context):

        user_input = update.effective_message.text.split()
        self.actual_thresh["max_co2_th"] = user_input[1]

        requests.put(f"http://{self.catalogIP}:{self.catalogPort}/setThresholds",
                     json=self.actual_thresh)

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='The new configuration of thresholds is: \
                                      \n- min Temperature: {}, \n - max Temperature: {}, \n - min Humidity: {}, \n - max Humidity: {}, \n - min CO2: {}, \n - max CO2: {}.\
                                      \nSelect the threshold you want to modify and type in the chat /<threshold> <value>: \
                                      \ne.g. /minTemperature 14'.format(self.actual_thresh["min_temperature_th"], self.actual_thresh["max_temperature_th"], self.actual_thresh["min_humidity_th"], self.actual_thresh["max_humidity_th"], self.actual_thresh["min_co2_th"], self.actual_thresh["max_co2_th"])
                        )

        self.optionEnd(update,context,first=False)

        return INFO


    def optionThresholds(self, update, context):
        '''
            The user can modify the thresholds
        '''

        res = requests.get(f"http://{self.catalogIP}:{self.catalogPort}/thresholds")
        for elem in json.loads(res.text):
            if elem['type'] == self.category:
                self.actual_thresh = elem

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
                                      \ne.g. /minTemperature 14'.format(self.category, minTemp, maxTemp, minHum, maxHum, minCo2, maxCo2),
                                 parse_mode='Markdown'
        )

    def optionEnd(self, update, context, first=True):

        if first == False:
            keyboard_info = [[InlineKeyboardButton("Tell Me More", callback_data='info'),
                              InlineKeyboardButton("Main menu", callback_data='home')],
                             [InlineKeyboardButton("Exit", callback_data='exit')]]
            txt = 'If you want more information, click on <b> Tell me more </b> \
                   \nif you want to come back to the main menu, click on <b> Main Menu </b> \
                   \nif you want to exit, click on <b> Exit </b>'
        else:
            keyboard_info = [[InlineKeyboardButton("Tell Me More", callback_data='info'),
                              InlineKeyboardButton("Reset Thresholds", callback_data='thresholds'),
                              InlineKeyboardButton("Main menu", callback_data='home')],
                             [InlineKeyboardButton("Exit", callback_data='exit')]]
            txt = 'If you want to reset some thresholds, click on <b> Reset Thresholds </b>,\
                   \nif you want more information, click on <b> Tell me more </b> \
                   \nif you want to come back to the main menu, click on <b> Main Menu </b>\
                   \nif you want to exit, click on <b> Exit </b>'

        reply_markup_info = InlineKeyboardMarkup(keyboard_info)

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 reply_markup=reply_markup_info,
                                 text= txt, parse_mode='HTML')

        return PARAM2

    def endMenu(self, update, context):
        print("sono in endMenu")
        keyboard_info = [[InlineKeyboardButton("Back", callback_data='home')],
                         [InlineKeyboardButton("Exit", callback_data='exit')]]
        reply_markup_info = InlineKeyboardMarkup(keyboard_info)
        context.bot.send_message(chat_id=update.effective_chat.id, reply_markup=reply_markup_info,
                                 text='If you want to explore other bread typologies, click on *Main menu!*',
                                 parse_mode='Markdown')


    def end(self, update, context):

        print("query in end", update.callback_query.data)
        query = update.callback_query

        if query.data == 'home':
            TYPOLOGY = self.home(update, context)
            return TYPOLOGY

        elif query.data == 'info':
            link = self.clientQuery.getLink()
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Click on the following link to learn more about the {}: {}.'.format(self.category, link))

            self.endMenu(update, context)

        elif query.data == 'exit':
            res = self.exit(update, context)

            return res

    def exit(self, update, context):

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Bye! Have a good day and come back to @Pynini soon. &#128400;',
                                 reply_markup=ReplyKeyboardRemove(), parse_mode='HTML')
        requests.post(f"http://{self.catalogIP}:{self.catalogPort}/removeBot",
                      json={'ip': self.catalogIP, 'chat_ID': self.chatID, 'last_seen': time.time()})
        print("Mi sono eliminato dal catalog")
        
        return ConversationHandler.END

    def image(self, update, context):
        clientQuery = ClientQuery("bot", "Freeboard")
        link = clientQuery.getFreeboard()
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Click on the following link to see the Freeboard: {}'.format(link))
        self.home(update, context)

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

           fallbacks=[
                      CommandHandler('caseID', self.selectCaseID),
                      CommandHandler('cancel', self.cancel),
                      CommandHandler('home', self.home),
                      CommandHandler('exit', self.exit),
                      CommandHandler('minTemperature', self.minTemp),
                      CommandHandler('maxTemperature', self.maxTemp),
                      CommandHandler('minHumidity', self.minHum),
                      CommandHandler('maxHumidity', self.maxHum),
                      CommandHandler('minCO2', self.minCO2),
                      CommandHandler('minCO2', self.maxCO2),
                      CommandHandler('image', self.image)
                      ]
       )

       disp.add_handler(conv_handler)
       disp.add_handler(MessageHandler(Filters.all, self.unknown))

       upd.start_polling()
       upd.idle()


if __name__=='__main__':

    with open("config.json", 'r') as f:
        config = json.load(f)
    ip = config['ip']
    port = config['port']
    data = requests.get(f"http://{ip}:{port}/telegramBot")
    bot = TelegramBot(json.loads(data.text)["telegramPort"], json.loads(data.text)["token"], ip, port)
    bot.main()
