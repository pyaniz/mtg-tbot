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





def inline(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query
    
    match = re.findall(r'\[(.*?)\]', update.inline_query.query)
    asyncio.set_event_loop(asyncio.new_event_loop())
    is_flipcard = False
    photos = []
    button_list = []
    footer_list = []
    header_list = []
    for index, name in enumerate(match):
        if index > max_cards:
            break
        try:
            card = scrython.cards.Named(fuzzy=name)
        except scrython.ScryfallError:
            auto = scrython.cards.Autocomplete(q=name, query=name)
            if len(auto.data()) > 0:
                text = ""
                for index, item in zip(range(5), auto.data()):
                    text += '`{}`\n'.format(item)
                update.inline_query.answer(text=strings.Card.card_autocorrect.format(text),
                                         parse_mode=telegram.ParseMode.MARKDOWN)
                continue
            else:
                update.inline_query.answer(text=strings.Card.card_not_found.format(name),
                                         parse_mode=telegram.ParseMode.MARKDOWN)
                continue
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

        eur = '{}€'.format(card.prices(mode="eur")) if card.prices(mode="eur") is not None else "CardMarket"
        usd = '{}€'.format(card.prices(mode="usd")) if card.prices(mode="usd") is not None else "TCGPlayer"
        usd_link = card.purchase_uris().get("tcgplayer")
        eur_link = card.purchase_uris().get("cardmarket")
        img_caption = emojize(":moneybag: [" + eur + "]" + "(" + eur_link + ")" + " | "
                              + "[" + usd + "]" + "(" + usd_link + ")" + "\n"
                              + legal_text, use_aliases=True)

        try:
            card.card_faces()[0]['image_uris']
            is_flipcard = True
        except KeyError:
            is_flipcard = False
            pass

        if len(match) > 1 or is_flipcard:
            if is_flipcard:
                photos.append(InputMediaPhoto(media=card.card_faces()[0]['image_uris']['normal'],
                                              caption=img_caption,
                                              parse_mode=telegram.ParseMode.MARKDOWN))
                photos.append(InputMediaPhoto(media=card.card_faces()[1]['image_uris']['normal'],
                                              caption=img_caption,
                                              parse_mode=telegram.ParseMode.MARKDOWN))
            else:
                photos.append(InputMediaPhoto(media=card.image_uris(0, image_type="normal"),
                                              caption=img_caption,
                                              parse_mode=telegram.ParseMode.MARKDOWN))
                time.sleep(0.04)
                continue
        else:
            if card.related_uris().get("edhrec") is not None:
                button_list.append(InlineKeyboardButton("Edhrec", url=card.related_uris().get("edhrec")))
            if card.related_uris().get("mtgtop8") is not None:
                button_list.append(InlineKeyboardButton("Top8", url=card.related_uris().get("mtgtop8")))
            button_list.append(InlineKeyboardButton("Scryfall", url=card.scryfall_uri()))
            if card.prices(mode="usd") is not None:
                header_list.append(InlineKeyboardButton('{}$'.format(card.prices(mode="usd")),
                                                        url=card.purchase_uris().get("tcgplayer")))
            else:
                header_list.append(InlineKeyboardButton("TCGPlayer", url=usd_link))
            if card.prices(mode="eur") is not None:
                header_list.append(InlineKeyboardButton('{}€'.format(card.prices(mode="eur")),
                                                        url=card.purchase_uris().get("cardmarket")))
            else:
                header_list.append(InlineKeyboardButton("MKM", url=eur_link))
            reply_markup = InlineKeyboardMarkup(util.build_menu(button_list,
                                                                header_buttons=header_list,
                                                                footer_buttons=footer_list,
                                                                n_cols=3))
            update.inline_query.answer(photo=card.image_uris(0, image_type="normal"),
                                   parse_mode=telegram.ParseMode.MARKDOWN,
                                   reply_markup=reply_markup,
                                   reply_to_message_id=update.message.message_id)
            return
    if len(match) > 1 or is_flipcard:
        update.inline_query.answer(media=photos,
                                     reply_to_message_id=update.message.message_id,
                                     disable_notification=True)



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
