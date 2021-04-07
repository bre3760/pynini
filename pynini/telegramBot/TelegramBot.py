from telegram import (ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler)
from telegramBot.sensors_db import SensorsDB
import requests
import logging
import json
import time
import numpy as np
from catalog import *

# https://iaassassari.files.wordpress.com/2012/07/panificazione.pdf

# IDEA: l'utente seleziona una tipologia di pane (comune, integrale, semola, etc..).
# Ciascuna tipologia è caratterizzata da uno specifico processo di lievitazione, si può monitorare temperatura, umidità, co2 emessa, (pH?)
# -> per ciascun tipo di pane: breve mex esplicativo, parametri ottimali di temp-umid-co2-pH, media valori reali
# Statistcihe relative alle vendite: diagrammi a torta presi da freeboard? oppure leggo valori da db e realizzo grafici python

# Mi serve un db per salvare dati relativi a ciascun tipo di pane e per plottare i dati sulle vendite

TYPOLOGY, PARAM, PARAM2, HOME, INFO, EXIT = range(6)

class TelegramBot(object):
    def __init__(self, db, port, token):
        self.telegramPort = port
        self.token = token
        self.db = db

        self.ip = "127.0.0.0"
        self.id = "pippo"

    def start(self, update, context):

        requests.post("http://localhost:9090/addBot", json={'ip': self.ip, 'name': self.id, 'last_seen': time.time()})
        print("Mi sono registrato al catalog")
        # print(f'Welcome to @Pynini! You can select the info you want to retrieve:\n 1./photo\n 2./temperature\n 3./humidity')
        # update.message.reply_text(f'Welcome to @Pynini! You can select the info you want to retrieve:\n 1./photo\n 2./temperature\n 3./humidity')

        #body = {'chat_id': update.effective_chat.id}
        #temp = requests.get('http://' + str(self.catalogAddress) + ':' + str(self.catalogPort) + '?chatToSearch=' + str(update.effective_chat.id))
        #print('++++\n\nStampo la get \n\n')
        #print(temp.json())
        #if temp.json() != False:
        #    temp = temp.json()
        #    for t in temp['values']:
        #        a = str(t)[2:len(t) - 3]
        #        print(a)

        options = ["Standard", "Wheat", "Gluten-free", "Sales Statistics"]
        reply_keyboard = []
        for elem in options:
            print(elem)
            reply_keyboard.append([InlineKeyboardButton(elem, callback_data=elem)])
        reply_markup = InlineKeyboardMarkup(reply_keyboard)
        update.message.reply_text(
            'Hi {}! Welcome to @Pynini! Here you can find information about different typologies of bread'.format(update.message.from_user.first_name))
        pass
        time.sleep(2)
        pass
        context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Choose the one you are interested in: ', reply_markup=reply_markup,
                                     parse_mode='Markdown')
        # else:
        #     update.message.reply_text(
        #         'Hi {}| There was an error, you are alread in the system!'.format(update.message.from_user.first_name))
        #     self.error()
        return TYPOLOGY


    def unknown(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='I could not understand the command you typed. For this bot all you need to do is to push the buttons in the chat.\n You wrote: {}'.format(
                                     update.message.text))


    def error(self, update, context):
        logger = logging.getLogger(__name__)
        logger.warning('Update "%s" caused error "%s"', update, context.error)


    def cancel(self, update, context):
        logger = logging.getLogger(__name__)
        user = update.message.from_user
        #body = {'whatPut': 3, 'chat_id': update.effective_chat.id}
        #requests.put('http://' + str(self.catalogAddress) + ':' + str(self.catalogPort), json=body)
        logger.info("User %s canceled the conversation.", user.first_name)
        update.message.reply_text('Bye! I hope we can talk again some day.',
                                  reply_markup=ReplyKeyboardRemove())

        return ConversationHandler.END

    def home(self,update,context):
        options = ["Standard", "Wheat", "Gluten-free", "Sales Statistics"]
        reply_keyboard = []
        for elem in options:
            print(elem)
            reply_keyboard.append([InlineKeyboardButton(elem, callback_data=elem)])
        reply_markup = InlineKeyboardMarkup(reply_keyboard)
        update.message.reply_text(
            'Hi {}! Welcome to @Pynini! Here you can find information about different typologies of bread'.format(
                update.message.from_user.first_name))
        pass
        time.sleep(2)
        pass
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Choose the one you are interested in: ', reply_markup=reply_markup,
                                 parse_mode='Markdown')
        return TYPOLOGY

    def getParam(self, update, context):
        query = update.callback_query
        print("Ho selezionato %s: (getParam)", query.data)
        #body = {'whatPut': 2, 'choice': query.data, 'chat_id': update.effective_chat.id}
        #requests.put('http://' + str(self.catalogAddress) + ':' + str(self.catalogPort), json=body)
        keyboard = [[InlineKeyboardButton("Temperature", callback_data='temp'),
                     InlineKeyboardButton("Humidity", callback_data='hum'),
                     InlineKeyboardButton("CO2", callback_data='co2'),
                     InlineKeyboardButton("Back", callback_data='home')
                     ],
                    [InlineKeyboardButton("Exit", callback_data='exit')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if query.data != 'home' and query.data != 'exit':
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='You have selected {} typology, now you have to select the parameter you want to investigate!'.format(query.data))
            pass
            time.sleep(2)
            pass
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='You can retrieve optimal and actual values for: \n *temperature*,\n *humidity*, \n *CO2 emitted*, \n *go back*, \n or *Exit*',
                                     reply_markup=reply_markup, parse_mode='Markdown')
        self.type = query.data
        return PARAM

    def getActualParams(self, update, context):
        query = update.callback_query
        print("self.type", self.type)
         # tramite get accedo al db per ritornare i parametri (ottimali e reali) richiesti dall'utente
    #     #paths = []
    #     #address_path = self.ipGeneratePath
    #     #port_path = self.portGeneratePath
        try:
             #if query.data == 'temp' or query.data == 'hum' or \
             if query.data == 'home':
                 options = ["Standard", "Wheat", "Gluten-free", "Sales Statistics"]
                 reply_keyboard = []
                 for elem in options:
                     print(elem)
                     reply_keyboard.append([InlineKeyboardButton(elem, callback_data=elem)])
                 reply_markup = InlineKeyboardMarkup(reply_keyboard)
                 context.bot.send_message(chat_id=update.effective_chat.id,
                                          text='Here you can find information about different typologies of bread. \n Choose the one you are interested in: ',
                                          reply_markup=reply_markup, parse_mode='Markdown')
                 return TYPOLOGY

             elif query.data == 'exit':
                # body = {'whatPut': 3, 'chat_id': update.effective_chat.id}
                # requests.put('http://' + str(self.catalogAddress) + ':' + str(self.catalogPort), json=body)
                # self.exit(update, context)
                print(f'Goodbye! Come back to @Pynini soon')
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text='Bye! Have a good day and come back to @Pynini soon.',
                                         reply_markup=ReplyKeyboardRemove())
                # update.message.reply_text(f'Goodbye! Come back to @Pynini soon')
                requests.post("http://localhost:9090/removeBot",
                              json={'ip': self.ip, 'name': self.id, 'last_seen': time.time()})
                print("Mi sono eliminato dal catalog")
                return ConversationHandler.END


             elif query.data == 'co2':
                context.bot.send_message(chat_id=update.effective_chat.id,
                                          text='You have chosen the {} parameter.'.format(query.data))
                 # se non riesco a trovare il modo di passare la variabile alla query sql, devo fare la cascata di if per ciascun type
                sql = '''select VALUE from co2 where TYPE = %s '''
                db.cursor.execute(sql, [self.type])
                res = db.cursor.fetchall()
                print("values:", res)
                values = []
                for v in res:
                    values.append(round(v[0],2))
    #             # interrogo db su parametri ottimali e di temperatura per il tipo di pane
    #             # -> cerco in tabella "TEMP" il type = "TYPE" ed estraggo tutti i valori della colonna "value"
                  # -> cerco in tabella "BEST" il type = "TYPE" ed estraggo il valore della colonna "temp"
    #                  [il mio db è costruito con tabelle per ogni parametro (temp, hum, co2) le cui colonne sono (timestamp, value, type = common, whole, gluten-free)]
    #             # res = requests.get('http://' + str(address_path) + ':' + str(port_path) + "?duration=30")
    #               best = requests.get('http://' + str(address_path) + ':' + str(port_path) + "?duration=30")
    #               if res.json()['value']!=False and res.json()['value']!=[]:
                if values != []:
                    context.bot.send_message(chat_id=update.effective_chat.id,
                          text='The optimal value {} for the {} typology is: {}. \n The actual minimum is: {}, \n the actual maximum is: {}, \n the actual mean is: {}.'.format(query.data, self.type, 0, min(values), max(values), round(np.mean(values),2)))

    #         elif rdb.json()['value'] == []:
                elif values == []:
                    self.error(update, context)
                    print("No data avaiable")
                    keyboard = [[InlineKeyboardButton("Temperature", callback_data='temp'),
                             InlineKeyboardButton("Humidity", callback_data='hum'),
                             InlineKeyboardButton("CO2", callback_data='co2')#,
                             #InlineKeyboardButton("pH", callback_data='ph')
                             ],
                            [InlineKeyboardButton("Exit", callback_data='exit')]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    context.bot.send_message(chat_id=update.effective_chat.id,
                                             text='Hey, an error occoured. Wait a little bit, try again. \nTo try again, push one of the buttons below!',
                                             reply_markup=reply_markup, parse_mode='Markdown')

                else:
                    self.error(update, context)
                    print("Error: something went wrong with your request. Try again!")
                    keyboard = [[InlineKeyboardButton("Temperature", callback_data='temp'),
                                 InlineKeyboardButton("Humidity", callback_data='hum'),
                                 InlineKeyboardButton("CO2", callback_data='co2')  # ,
                                 # InlineKeyboardButton("pH", callback_data='ph')
                                 ],
                                [InlineKeyboardButton("Exit", callback_data='exit')]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    context.bot.send_message(chat_id=update.effective_chat.id,
                                             text='Hey, an error occoured. Wait a little bit, try again. \nTo try again, push one of the buttons below!',
                                             reply_markup=reply_markup, parse_mode='Markdown')

        except Exception as e:
            try:
                self.error(update, context)
                reply_markup = InlineKeyboardMarkup(keyboard)
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text='Hey, an error occured. Wait a little bit, try again. \nTo try again, push one of the buttons below!',
                                         reply_markup=reply_markup, parse_mode='Markdown')
                # print("Status code: " + str(res.status_code))
                # print("Status code: " + str(res.reason))
                return PARAM2
            except:
                pass
                print(e)
                return PARAM2

        pass
        time.sleep(2)
        pass
        keyboard_info = [[InlineKeyboardButton("Tell Me More", callback_data='info')],
                    [InlineKeyboardButton("Exit", callback_data='exit')]]
        reply_markup_info = InlineKeyboardMarkup(keyboard_info)
        context.bot.send_message(chat_id=update.effective_chat.id, reply_markup=reply_markup_info, text='If you want more information, click on *Tell me more!*', parse_mode='Markdown')

        return PARAM2

    def info(self, update, context):
        # keyboard = [[InlineKeyboardButton("Tell Me More", callback_data='info')],
        #             [InlineKeyboardButton("Exit", callback_data='exit')]]
        # reply_markup = InlineKeyboardMarkup(keyboard)
        query = update.callback_query
    #     right_info = False
        if query.data == 'info':
            sql = '''select INFO from best where TYPOLOGY = %s '''
            db.cursor.execute(sql, [self.type])
            res = db.cursor.fetchall()
            print("link:", res)
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Click on the following link to learn more about the {}: {}.'.format(self.type,res))
    #         right_info = interrogo db: link per further info
    #         if right_info == False:
    #             print('wrong info')
    #             return -1

        elif query.data == 'exit':
            # body = {'whatPut': 3, 'chat_id': update.effective_chat.id}
            # requests.put("http://localhost:9090", json=body)
            requests.post("http://localhost:9090/removeBot",
                          json={'ip': self.ip, 'name': self.id, 'last_seen': time.time()})
            print("Mi sono eliminato dal catalog")

            # self.exit(update, context)
            print(f'Goodbye! Come back to @Pynini soon')
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Bye! Have a good day and come back to @Pynini soon.',
                                     reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END

        #         else:
    #             context.bot.send_message(chat_id=update.effective_chat.id,
    #                                      text="To find out more follow this link: " + "[" + right_info['link'] + "]",
    #                                      parse_mode='Markdown')
    #             pass
    #             time.sleep(2)
    #             pass
    #             context.bot.send_message(chat_id=update.effective_chat.id, text="Please select what you want me to do:",
    #                                      reply_markup=reply_markup)

        pass
        time.sleep(2)
        pass
        keyboard_info = [[InlineKeyboardButton("Main menu", callback_data='home')],
                    [InlineKeyboardButton("Exit", callback_data='exit')]]
        reply_markup_info = InlineKeyboardMarkup(keyboard_info)
        context.bot.send_message(chat_id=update.effective_chat.id, reply_markup=reply_markup_info, text='If you want to explore other bread typologies, click on *Main menu!*', parse_mode='Markdown')

        return INFO

    def end(self, update, context):
        query = update.callback_query

        if query.data == 'home':
            options = ["Standard", "Wheat", "Gluten-free", "Sales Statistics"]
            reply_keyboard = []
            for elem in options:
                print(elem)
                reply_keyboard.append([InlineKeyboardButton(elem, callback_data=elem)])
            reply_markup = InlineKeyboardMarkup(reply_keyboard)
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Here you can find information about different typologies of bread. \n Choose the one you are interested in: ',
                                     reply_markup=reply_markup, parse_mode='Markdown')
            return TYPOLOGY

        elif query.data == 'exit':
            #body = {'whatPut': 3, 'chat_id': update.effective_chat.id}
            #requests.put('http://' + str(self.catalogAddress) + ':' + str(self.catalogPort), json=body)

            # self.exit(update, context)
            print(f'Goodbye! Come back to @Pynini soon')
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Bye! Have a good day and come back to @Pynini soon.',
                                     reply_markup=ReplyKeyboardRemove())
            # update.message.reply_text(f'Goodbye! Come back to @Pynini soon')
            requests.post("http://localhost:9090/removeBot",
                          json={'ip': self.ip, 'name': self.id, 'last_seen': time.time()})
            print("Mi sono eliminato dal catalog")
            return ConversationHandler.END

    def exit(self, update, context):
        # body = {'whatPut': 3, 'chat_id': update.effective_chat.id}
        # requests.put('http://' + str(self.catalogAddress) + ':' + str(self.catalogPort), json=body)
        print(f'Goodbye! Come back to @Pynini soon')
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Bye! Have a good day and come back to @Pynini soon.',
                                 reply_markup=ReplyKeyboardRemove())
        # update.message.reply_text(f'Goodbye! Come back to @Pynini soon')
        requests.post("http://localhost:9090/removeBot",
                      json={'ip': self.ip, 'name': self.id, 'last_seen': time.time()})
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
               INFO: [CallbackQueryHandler(self.end)]
           },

           fallbacks=[CommandHandler('cancel', self.cancel),
                      CommandHandler('home', self.home),
                      CommandHandler('exit', self.exit)
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
    db.mydb.commit()
    db.mydb.close()

    data = requests.get("http://localhost:9090/telegramBot")
    bot = TelegramBot(db, json.loads(data.text)["telegramPort"], json.loads(data.text)["token"])
    bot.main()
