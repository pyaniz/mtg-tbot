# some useful links:
# https://python-telegram-bot.org/
# http://docs.peewee-orm.com/en/latest/peewee/quickstart.html
# https://python-telegram-bot.readthedocs.io/en/stable

from on_pvt import *
from on_group import *
from on_common import *
from telegram import InlineQueryResultPhoto, InputTextMessageContent, InlineQueryResultArticle
from telegram.ext import Updater, InlineQueryHandler, CallbackQueryHandler
from telegram.ext import MessageHandler, CommandHandler, Filters
import tasks
import os #dev env check

#test
from uuid import uuid4
from telegram import InlineQueryResultArticle, ParseMode, InputTextMessageContent, Update
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, CallbackContext
from telegram.utils.helpers import escape_markdown
import telegram, scrython, re, asyncio, time, strings, util, logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto
from telegram import ChatAction
from emoji import emojize
from telegram.ext import CallbackContext
from config import max_cards
import cacheable







db = SqliteDatabase(config["database"]["path"])


path = '.dev'
if os.path.exists(path):
    updater = Updater(token=config["token-dev"], use_context=True)
    print("Using Dev environment")
else:
    updater = Updater(token=config["token"], use_context=True)


dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


try:
    open(config["database"]["path"])
    logger.info(strings.Log.database_ready)
except FileNotFoundError:
    logger.info(strings.Log.database_not_found)
    db.create_tables([tables.User, tables.Event, tables.Round, tables.Feed])
    logger.log(logging.INFO, strings.Log.database_ok)
finally:
    db.connect()


def error(update, context):
    logger.error('An error occurred! "%s"', context.error)
    raise


def test(update: Update, context: CallbackContext):
    print("worked")

def inline(update: Update, context: CallbackContext):
    query = update.inline_query.query
    asyncio.set_event_loop(asyncio.new_event_loop())
    is_flipcard = False #defines whether its a flipcard or not. This is just a variable, will be used to determine multiple images.
#    print(query)
    if query == "":
        return

    match = re.findall('/r', query)
    cleanmatch = re.findall(r'\/r ([\s\S]*)$', query)            
    print(match)
    print(cleanmatch)
    print(query)
    
    
    if len(query) > 0:
        
        text = ""
        results_data = []
        footer_list = []
        if match == ['/r']:
            auto = scrython.cards.Autocomplete(q=cleanmatch, query=cleanmatch)
        
            for index, item in zip(range(5), auto.data()):
                card = scrython.cards.Named(fuzzy=item)            
                rule = scrython.rulings.Id(id=card.id())               
                message = ""

                if rule.data_length() == 0:
                    message = strings.Card.card_ruling_unavailable
                else:
                    for index, rule_text in enumerate(rule.data()):
                        message += (str(index + 1) + ". " + rule.data(index=index, key="comment") + "\n\n")
                
                time.sleep(0.07)                
 
                results_data.append(
                    InlineQueryResultArticle(
                        id=card.id(),
                        title=card.name(),
                        thumb_url=card.image_uris(0, image_type="normal"),
                        input_message_content=InputTextMessageContent(
                            f"*{escape_markdown(card.name())}*" + "\n\n" + message, parse_mode=ParseMode.MARKDOWN
                            ),            
                        url=card.image_uris(0, image_type="normal"),
                        hide_url=True,
                        )
                    )
        else:
            auto = scrython.cards.Autocomplete(q=query, query=query)
            for index, item in zip(range(10), auto.data()):
                card = scrython.cards.Named(fuzzy=item)            
############ Card legalities ######################
                del card.legalities()["penny"]
                del card.legalities()["oldschool"]
                del card.legalities()["future"]
                del card.legalities()["duel"]
                banned_in = [k for k, v in card.legalities().items() if v == "banned" or v == "not_legal"]
                legal_in = [k for k, v in card.legalities().items() if v == "legal"]
                legal_text = ""

                if len(banned_in) == 0:
                    legal_text = strings.Card.card_legal
                else:
                    footer_list.append(InlineKeyboardButton("Legalities", callback_data=card.name()))
                    for v in legal_in:
                        legal_text += ':white_check_mark: {}\n'.format(v)
                    for v in banned_in:
                        legal_text += ':no_entry: {}\n'.format(v)
                    cacheable.CACHED_LEGALITIES.update({card.name(): legal_text})
############ Card legalities ######################
                results_data.append(
                    InlineQueryResultPhoto(
                        id=card.id(),
                        title=card.name(),
                        caption=card.name(),
                        photo_url=card.image_uris(0, image_type="normal"),
                        thumb_url=card.image_uris(0, image_type="normal"),                        
                        description=card.name(),
                        reply_markup = InlineKeyboardMarkup(util.build_menu(buttons=footer_list,
                                                    n_cols=1))
                    ),                            
                )            
            #print(index)
                time.sleep(0.07)
        update.inline_query.answer(results_data)


  

    
#    context.bot.send_message(chat_id=update.effective_chat.id, text=context.args)
    
    
#    card = scrython.cards.Named(fuzzy=context.args[0])
#    print(card.id(), "-" + card.name())
#    context.bot.send_message(chat_id=update.effective_chat.id, text=card.id(), parse_mode=telegram.ParseMode.MARKDOWN)



if config["welcome"]:
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome_message))
dispatcher.add_handler(CommandHandler('start', callback=start_pvt, filters=Filters.private))
dispatcher.add_handler(CommandHandler('start', callback=start_group, filters=Filters.group))
dispatcher.add_handler(CommandHandler('rotation', callback=check_rotation, filters=(Filters.private | Filters.group)))
dispatcher.add_handler(CommandHandler('banlist', callback=cards_banlist, filters=(Filters.private | Filters.group)))
dispatcher.add_handler(CommandHandler('social', callback=social_pvt, filters=Filters.private))
dispatcher.add_handler(CommandHandler('social', callback=social, filters=Filters.group))
dispatcher.add_handler(CommandHandler('friendlist', callback=friend_list, filters=Filters.group))
dispatcher.add_handler(CommandHandler('status', callback=arena_status, filters=Filters.group))
dispatcher.add_handler(CommandHandler('dci', callback=dci, filters=Filters.private))
dispatcher.add_handler(CommandHandler('arena', callback=arena, filters=Filters.private))
dispatcher.add_handler(CommandHandler('name', callback=name, filters=Filters.private))
dispatcher.add_handler(CommandHandler('help', callback=help_pvt, filters=Filters.private))
dispatcher.add_handler(MessageHandler(Filters.private and Filters.document, logparser))
dispatcher.add_handler(MessageHandler(Filters.regex('\[(.*?)\]'), cards))
dispatcher.add_handler(MessageHandler(Filters.regex('\(\((.*?)\)\)'), rulings))
dispatcher.add_handler(MessageHandler(Filters.text & Filters.group, register_users))
dispatcher.add_handler(InlineQueryHandler(inline))
# dispatcher.add_handler(CallbackQueryHandler(callback=help_cb))
dispatcher.add_handler(CallbackQueryHandler(legalities, pattern=r'.*'))
#dispatcher.add_handler(CommandHandler('test', callback=test, filters=Filters.private))

dispatcher.add_error_handler(error)
# start the bot
updater.start_polling(clean=True)

# start the loop to check for rss feeds
loop = asyncio.get_event_loop()
task = loop.create_task(tasks.check_rss(updater))

try:
    loop.run_until_complete(task)
except asyncio.CancelledError:
    pass
