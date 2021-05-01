from telegram import (ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler)
from database.query import ClientQuery
import requests
import logging
import json
import time
import numpy as np
import paho.mqtt.client as PahoMQTT

# IDEA: l'utente seleziona una tipologia di pane (comune, integrale, semola, etc..).
# Ciascuna tipologia è caratterizzata da uno specifico processo di lievitazione, si può monitorare temperatura, umidità, co2 emessa, (pH?)
# -> per ciascun tipo di pane: breve mex esplicativo, parametri ottimali di temp-umid-co2-pH, media valori reali
# Statistcihe relative alle vendite: diagrammi a torta presi da freeboard? oppure leggo valori da db e realizzo grafici python

# Mi serve un db per salvare dati relativi a ciascun tipo di pane e per plottare i dati sulle vendite

# devo ciclare sui cases e registrarmi alle topiche degli arduino connessi

TYPOLOGY, PARAM, PARAMS, PARAM2, HOME, INFO, THRESHOLD, EXIT = range(8)

class TelegramBot(object):
    def __init__(self, port, token, ip):
        self.telegramPort = port
        self.token = token
        self.ip = ip # prendi da config specifico

    def stop(self):
        self._paho_mqtt.unsubscribe(self.topic)
        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()

    def myOnConnect(self, paho_mqtt, userdata, flags, rc):
        print("Connected to %s with result code: %d" % (self.messageBroker, rc))

    def myPublish(self, message):
        # publish a message with a certain topic
        self._paho_mqtt.publish(self.topic, json.dumps(message), 2)
        self.influxDB.write(message)

    #	self.influxDB.clean()

    def myOnMessageReceived(self, paho_mqtt, userdata, msg, update, context):
        # A new message is received: non mi interessa distinguere le topiche, quando leggo un messaggio devo mandare l'alert
        print("Topic:'" + msg.topic + "', QoS: '" + str(msg.qos) + "' Message: '" + str(msg.payload) + "'")

        self.sendAlert(update, context, msg.topic)
        print("send Alert, msg.topic: ", msg.topic)

    def sendAlert(self, update, context, topic):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='ALERT! Your {} threshold is over!'.format(topic), parse_mode='HTML')

    def start(self, update, context):

        self._paho_mqtt = PahoMQTT.Client("bot", False)
        self._paho_mqtt.on_connect = self.myOnConnect
        self._paho_mqtt.on_message = self.myOnMessageReceived
        r = requests.get("http://localhost:9090/broker_ip")
        self.messageBroker = json.loads(r.text)
        r = requests.get("http://localhost:9090/active_arduino")
        self.topics = json.loads(r.text)
        # subscribe for a topic
        for t in self.topics:
            self._paho_mqtt.subscribe("trigger/"+t, 2)
        print("Subscribed to: ", self.topics)

        self._paho_mqtt.connect(self.messageBroker, 1883)
        self._paho_mqtt.loop_start()

        self.chatID = update.message.chat_id
        requests.post("http://localhost:9090/addBot", json={'ip': self.ip, 'chat_ID': self.chatID, 'last_seen': time.time()})
        print("Mi sono registrato al catalog")

        options = ["White", "Wheat", "Gluten-free", "Statistics"]
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
        options = ["White", "Wheat", "Gluten-free", "Statistics"]
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
        if query.data == "Statistics":
            self.image(update,context)
        else:
            keyboard = [[InlineKeyboardButton("Temperature", callback_data='temperature'),
                         InlineKeyboardButton("Humidity", callback_data='humidity'),
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
        self.category = query.data
        return PARAM

    def getActualParams(self, update, context):

        query = update.callback_query
        print("category", self.category)
        print("query.data in getActualParams", query.data)

        keyboard_params = [[InlineKeyboardButton("Temperature", callback_data='temperature'),
                            InlineKeyboardButton("Humidity", callback_data='humidity'),
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

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='You have chosen the <b> {} </b> parameter.'.format(query.data),
                                 parse_mode='HTML')

        self.clientQuery = ClientQuery(query.data, self.category)
        actualValues = self.clientQuery.getData()

        best = self.clientQuery.getBest(query.data)

        if actualValues != []:
            print("actualValues != []")
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='The optimal value {} for the {} typology is: {}. \n The actual minimum is: {}, \n the actual maximum is: {}, \n the actual mean is: {}.'.format(
                                         query.data, self.category, best, min(actualValues), max(actualValues), round(np.mean(actualValues), 2)))
            time.sleep(2)

        elif actualValues == []:
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


    def info(self, update, context):

        query = update.callback_query

        if query.data == 'home':
            TYPOLOGY = self.home(update, context)
            return TYPOLOGY

        elif query.data == 'info':
            link = self.clientQuery.getBest(query.data)
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
            if elem['type'] == self.category:
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
                                      \ne.g. /minTemperature 14'.format(self.category, minTemp, maxTemp, minHum, maxHum, minCo2, maxCo2),
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
            link = self.clientQuery.getBest(query.data)
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
        requests.post("http://localhost:9090/removeBot",
                      json={'ip': self.ip, 'chat_ID': self.chatID, 'last_seen': time.time()})
        print("Mi sono eliminato dal catalog")
        self.clientQuery.end()
        
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

           fallbacks=[CommandHandler('cancel', self.cancel),
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
    bot = TelegramBot(json.loads(data.text)["telegramPort"], json.loads(data.text)["token"], ip)
    bot.main()
