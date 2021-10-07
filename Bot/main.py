# some useful links:
# https://python-telegram-bot.org/
# http://docs.peewee-orm.com/en/latest/peewee/quickstart.html
# https://python-telegram-bot.readthedocs.io/en/stable

from on_pvt import *
from on_group import *
from on_common import *
from telegram import InlineQueryResultArticle, InputTextMessageContent
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


""" def inline(update: Update, context: CallbackContext):
    try:
        user = tables.User.get(tables.User.user_id == update.inline_query.from_user.id)
        text = strings.Inline.player_card_text.format(user.name if not None else "", user.user_id,
                                                      user.dci if not None else "",
                                                      user.arena if not None else "")
    except DoesNotExist:
        text = strings.Global.user_not_exist

    results = list()
    results.append(
        InlineQueryResultArticle(
            id="PLAYERCARD",
            title=strings.Inline.player_card_title,
            description=strings.Inline.player_card_desc,
            input_message_content=InputTextMessageContent(text,
                                                          parse_mode=telegram.ParseMode.MARKDOWN,
                                                          disable_web_page_preview=True)
        )
    )
    context.bot.answer_inline_query(update.inline_query.id, results, cache_time=10) """

""" def inline(update: Update, context: CallbackContext) -> None:

    query = update.inline_query.query

    if query == "":
        return

    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="Caps",
            input_message_content=InputTextMessageContent(query.upper()),
        ),
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="Bold",
            input_message_content=InputTextMessageContent(
                f"*{escape_markdown(query)}*", parse_mode=ParseMode.MARKDOWN
            ),
        ),
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="Italic",
            input_message_content=InputTextMessageContent(
                f"_{escape_markdown(query)}_", parse_mode=ParseMode.MARKDOWN
            ),
        ),
    ]

    update.inline_query.answer(results)
 """



"""
def inline(update: Update, context: CallbackContext) -> None:
    match = re.findall(r'\[(.*?)\]', update.message.text)
    asyncio.set_event_loop(asyncio.new_event_loop())
    is_flipcard = False
"""
def inline(update: Update, context: CallbackContext):
    query = update.inline_query.query
    asyncio.set_event_loop(asyncio.new_event_loop())
    is_flipcard = False #defines whether its a flipcard or not. This is just a variable, will be used to determine multiple images.
    print(query)
    if query == "":
        return
    
    auto = scrython.cards.Autocomplete(q=query, query=query)
    if len(auto.data()) > 0:
        text = ""
        results_data = []
        for index, item in zip(range(9), auto.data()):
            card = scrython.cards.Named(fuzzy=item)            
            results_data.append(
                InlineQueryResultArticle(
                    id=card.id(),
                    title=card.name(),
                    input_message_content=InputTextMessageContent(
                        f"*{escape_markdown(card.name())}*", parse_mode=ParseMode.MARKDOWN
                        ),            
                    ),
                )            
        #print(index)
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
dispatcher.add_handler(MessageHandler(Filters.regex('\[ex(.*?)\]'), cards))
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
