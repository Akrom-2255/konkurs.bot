import json
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramBadRequest

API_TOKEN = "8171811933:AAGyvVekWPrUELwaThPnIb1x7pJKC34VYrs"

bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

CHANNELS = [
    "@saviya_bekati",
    "@naa_for_myself",
    "@Hikmatulloh_qizi"
]
PRIVATE_CHANNEL_LINK = "https://t.me/+ACclWwn2n_VjMmVi"
MIN_REFERALS_REQUIRED = 5

REFERAL_FILE = "referals.json"
PENDING_FILE = "pending.json"

try:
    with open(REFERAL_FILE, "r", encoding="utf-8") as f:
        referals = json.load(f)
except:
    referals = {}

try:
    with open(PENDING_FILE, "r", encoding="utf-8") as f:
        pending = json.load(f)
except:
    pending = {}

def save_referals():
    with open(REFERAL_FILE, "w", encoding="utf-8") as f:
        json.dump(referals, f, ensure_ascii=False, indent=4)

def save_pending():
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(pending, f, ensure_ascii=False, indent=4)

async def check_both_subscribed(user_id: int) -> bool:
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ("member", "administrator", "creator"):
                return False
        except TelegramBadRequest:
            return False
    return True

def get_channel_buttons() -> InlineKeyboardMarkup:
    keyboard = []
    for ch in CHANNELS:
        keyboard.append([
            InlineKeyboardButton(
                text=f"📢 {ch[1:]} kanaliga obuna bo‘lish",
                url=f"https://t.me/{ch[1:]}"
            )
        ])
    keyboard.append([InlineKeyboardButton(text="✅ Obuna bo‘ldim", callback_data="check_subs")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_continue_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Davom etish", callback_data="continue")]
    ])

def get_results_buttons() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="♻️ Natijalarni yangilash", callback_data="refresh_results")],
        [InlineKeyboardButton(text="🔙 Referalga qaytish", callback_data="to_referal")]
    ])

@dp.message(CommandStart())
async def start_command(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name
    args = message.text.split(maxsplit=1)
    start_arg = args[1] if len(args) > 1 else None

    if start_arg and start_arg != str(user_id):
        pending[str(user_id)] = start_arg
        save_pending()

    if await check_both_subscribed(user_id):
        await message.answer(
            "✅ Siz allaqachon barcha kanallarga obuna bo‘lgansiz.",
            reply_markup=get_continue_button()
        )
    else:
        await message.answer(
            "Assalomu alaykum!\n\n"
            "Iltimos, quyidagi 3 ta kanaldan ham a’zo bo‘ling va «✅ Obuna bo‘ldim» tugmasini bosing.",
            reply_markup=get_channel_buttons()
        )

@dp.callback_query(F.data == "check_subs")
async def check_subs_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    if await check_both_subscribed(user_id):
        await callback.message.answer(
            "✅ Siz muvaffaqiyatli obuna bo‘ldingiz!",
            reply_markup=get_continue_button()
        )
    else:
        await callback.answer("❌ Hali barcha kanallarga obuna bo‘lmadingiz!", show_alert=True)

async def get_username(user_id: int) -> str:
    try:
        user = await bot.get_chat(user_id)
        return user.username or user.full_name or "Nomaʼlum"
    except:
        return "Nomaʼlum"

async def send_ref_info(user_id: int, send_func):
    if not await check_both_subscribed(user_id):
        await send_func(
            "❌ Iltimos, barcha kanallarga a’zo bo‘ling va keyin yana urinib ko‘ring.",
            reply_markup=get_channel_buttons()
        )
        return

    if str(user_id) in pending:
        referrer = pending.pop(str(user_id))
        save_pending()
        referals.setdefault(referrer, [])
        if str(user_id) not in referals[referrer]:
            referals[referrer].append(str(user_id))
            save_referals()
            try:
                new_user = await get_username(user_id)
                await bot.send_message(
                    int(referrer),
                    f"👤 Yangi foydalanuvchi sizning havolangiz orqali qo‘shildi: <b>@{new_user}</b>"
                )
                if len(referals[referrer]) == MIN_REFERALS_REQUIRED:
                    await bot.send_message(
                        int(referrer),
                        f"🎉 🎁 Siz {MIN_REFERALS_REQUIRED} ta do‘st taklif qildingiz!\n"
                        f"Maxfiy kanal havolasi:\n{PRIVATE_CHANNEL_LINK}"
                    )
            except Exception:
                pass

    referal_link = f"https://t.me/Anglang_konkurs_bot?start={user_id}"
    user_list = referals.get(str(user_id), [])
    count = len(user_list)

    extra = ""
    if count >= MIN_REFERALS_REQUIRED:
        extra = (
            f"\n\n🎁 Siz {MIN_REFERALS_REQUIRED} yoki undan ortiq do‘st taklif qildingiz!\n"
            f"Maxfiy kanal havolasi:\n{PRIVATE_CHANNEL_LINK}"
        )

    text = (
        f"✅ Siz kanallarga a’zo bo‘lgansiz!\n\n"
        f"📨 Shaxsiy referal havolangiz:\n<code>{referal_link}</code>\n\n"
        f"👥 Hozirgacha <b>{count}</b> ta odam referal havolangiz orqali qo‘shildi.{extra}\n\n"
        "♻️ Natijalarni yangilash uchun pastdagi tugmani bosing."
    )
    await send_func(text, reply_markup=get_results_buttons())

@dp.callback_query(F.data == "continue")
async def continue_callback(callback: CallbackQuery):
    await send_ref_info(callback.from_user.id, callback.message.answer)
    await callback.answer()

@dp.message(Command(commands=["continue"]))
async def continue_command(message: Message):
    await send_ref_info(message.from_user.id, message.answer)

@dp.callback_query(F.data == "refresh_results")
async def refresh_results_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not await check_both_subscribed(user_id):
        await callback.message.edit_text(
            "❌ Siz hali barcha kanallarga a’zo bo‘lmagansiz!",
            reply_markup=get_channel_buttons()
        )
        await callback.answer()
        return

    user_list = referals.get(str(user_id), [])
    count = len(user_list)

    user_lines = []
    for uid in user_list:
        username = await get_username(int(uid))
        user_lines.append(f"- @{username}")

    text = f"📊 Sizning referal orqali qo‘shilganlar soni: <b>{count}</b>\n\n"
    if count > 0:
        text += "👥 Referallar ro‘yxati:\n" + "\n".join(user_lines)
    else:
        text += "Hozircha hech kimni taklif qilmagansiz."

    await callback.message.edit_text(text, reply_markup=get_results_buttons())
    await callback.answer("✅ Natija yangilandi.")

@dp.callback_query(F.data == "to_referal")
async def to_referal_callback(callback: CallbackQuery):
    await send_ref_info(callback.from_user.id, callback.message.edit_text)
    await callback.answer()

# --- PythonAnywhere uchun ishga tushirish ---
if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
