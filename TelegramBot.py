from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import exchange

TOKEN="1275410864:AAH4_Kpy59KY7iq5jQaC8r8XvCGacp2LBNc"

def extractText(text):
     return text.split()[1].strip()

def extractCommand(text):
    return text.split()[0].strip()

def start(update, context):
    print(f'Welcome to @Pynini! You can select the info you want to retrieve:\n 1./photo\n 2./temperature\n 3./humidity')
    update.message.reply_text(f'Welcome to @Pynini! You can select the info you want to retrieve:\n 1./photo\n 2./temperature\n 3./humidity')

def end(update, context):
    print(f'Goodbye! Come back to @Pynini soon')
    update.message.reply_text(f'Goodbye! Come back to @Pynini soon')

def convertUsd(update, context):
     usd=float(extractText(update.message.text))
     eur=exchange.from_usd_to_eur(usd)
     print(f'Eseguita conversione da {usd} USD a {eur} EUR')
     update.message.reply_text(f'{eur} EUR')

def convertEur(update, context):
     eur=float(extractText(update.message.text))
     usd=exchange.from_eur_to_usd(eur)
     print(f'Eseguita conversione da {eur} EUR a {usd} USD')
     #con il comando seguente stampo nella chat del bot
     update.message.reply_text(f'{usd} USD')

# def error(update, context):
#     wrongCmd = extractCommand(update.message.text)
#     print(f'{wrongCmd} This command does not exist')
#     update.message.reply_text(f'{wrongCmd} This command does not exist')
#
# def sendPhoto(update, context):
#     photo = actualParam.getPhoto()
#     update.message.reply_text(f'{photo} Photo')
#
# def sendTemperature(update, context):
#     temp = actualParam.getTemperature()
#     update.message.reply_text(f'{temp} Temperature')
#
# def sendHumidity(update, context):
#     hum = actualParam.getHumidity()
#     update.message.reply_text(f'{hum} Humidity')

def main():

   upd= Updater(TOKEN, use_context=True)
   disp=upd.dispatcher

   # devo prendere il comando: prima parola dopo lo slash
   ### ESEMPIO PROVA
   disp.add_handler(CommandHandler("usd", convertUsd))
   disp.add_handler(CommandHandler("eur", convertEur))
   disp.add_handler(CommandHandler("start", start))
   disp.add_handler(CommandHandler("end", end))

   ### PARAMETRI DI INTERESSE
   # disp.add_handler(CommandHandler("photo", sendPhoto))
   # disp.add_handler(CommandHandler("temperature", sendTemperature))
   # disp.add_handler(CommandHandler("humidity", sendHumidity))

   #disp.add_error_handler(error) #NON FUNZIONA

   upd.start_polling()

   upd.idle()

if __name__=='__main__':
   main()