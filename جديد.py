import logging
import telebot
import requests
import json
import os
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from requests.exceptions import ConnectionError, ReadTimeout

# إعدادات التسجيل
logging.basicConfig(
    filename="log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# التحقق من التوكن
try:
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("❌ خطأ: لم يتم العثور على التوكن!")
        logging.error("لم يتم العثور على التوكن!")
        exit()
except Exception as e:
    logging.error(f"خطأ في جلب التوكن: {e}")
    print(f"خطأ في جلب التوكن: {e}")
    exit()

# إنشاء البوت
try:
    bot = telebot.TeleBot(TOKEN)
    logging.info("البوت بدأ يشتغل")
except Exception as e:
    logging.error(f"خطأ في إنشاء البوت: {e}")
    print(f"خطأ في إنشاء البوت: {e}")
    exit()

# المتغيرات العامة
last_messages = {}
page_history = {}
user_states = {}
user_inputs = {}
pagination_state = {}

DATA_FILE = "users.json"
global_data = None

# تحميل البيانات
try:
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({"users": {}, "verified_bots": []}, f)
    with open(DATA_FILE, "r") as f:
        global_data = json.load(f)
except Exception as e:
    logging.error(f"خطأ في إنشاء أو تحميل ملف البيانات: {e}")
    print(f"خطأ في إنشاء أو تحميل ملف البيانات: {e}")
    exit()

ADMIN_IDS = [7920989999]  # قائمة معرفات الأدمن

# دوال مساعدة
def save_data():
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(global_data, f)
    except Exception as e:
        logging.error(f"خطأ في حفظ البيانات: {e}")

def get_rank(points):
    try:
        if points >= 100:
            return "محترف"
        elif points >= 50:
            return "متوسط"
        else:
            return "مبتدئ"
    except Exception as e:
        logging.error(f"خطأ في تحديد الرتبة: {e}")
        return "مبتدئ"

def delete_previous_messages(chat_id, user_id):
    try:
        if user_id in last_messages:
            messages_to_delete = last_messages[user_id][-10:]
            for message_id in messages_to_delete:
                try:
                    bot.delete_message(chat_id, message_id)
                except Exception:
                    pass
        last_messages[user_id] = []
    except Exception as e:
        logging.error(f"خطأ في مسح الرسائل القديمة لـ {user_id}: {e}")

def add_message_to_history(chat_id, user_id, message_id):
    try:
        if user_id not in last_messages:
            last_messages[user_id] = []
        last_messages[user_id].append(message_id)
    except Exception as e:
        logging.error(f"خطأ في إضافة رسالة للتاريخ لـ {user_id}: {e}")

def add_to_page_history(user_id, page):
    if user_id not in page_history:
        page_history[user_id] = []
    if not page_history[user_id] or page_history[user_id][-1] != page:
        page_history[user_id].append(page)

# القوائم
def main_menu(chat_id, user_id):
    start_time = time.time()
    try:
        delete_previous_messages(chat_id, user_id)
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("📁 ملفي", callback_data="my_profile"),
            InlineKeyboardButton("📚 المكتبة", callback_data="library")
        )
        markup.add(
            InlineKeyboardButton("👥 دعوة أصدقاء", callback_data="invite_friends"),
            InlineKeyboardButton("📋 المهام", callback_data="tasks")
        )
        markup.add(
            InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings"),
            InlineKeyboardButton("ℹ️ التعريف", callback_data="about")
        )
        markup.add(
            InlineKeyboardButton("📩 شكوى", callback_data="complaint"),
            InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")
        )
        if user_id in ADMIN_IDS:
            markup.add(InlineKeyboardButton("🛠️ لوحة الأدمن", callback_data="admin_panel"))
        
        msg = bot.send_message(chat_id, "مرحبًا بك في البوت! اختر خيارًا:", reply_markup=markup)
        add_message_to_history(chat_id, user_id, msg.message_id)
        page_history[user_id] = ["main_menu"]
    except Exception as e:
        logging.error(f"فشل في إرسال القايمة الرئيسية لـ {user_id}: {e}")
    finally:
        duration = time.time() - start_time
        if duration > 2:
            logging.warning(f"تأخير في إرسال القايمة الرئيسية لـ {user_id}: {duration} ثانية")

def library_menu(chat_id, user_id):
    try:
        delete_previous_messages(chat_id, user_id)
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("➕ إضافة بوت", callback_data="add_bot"),
            InlineKeyboardButton("📜 بوتاتي", callback_data="my_bots_page_1")
        )
        markup.add(
            InlineKeyboardButton("✅ البوتات المعتمدة", callback_data="verified_bots"),
            InlineKeyboardButton("🔍 بحث", callback_data="search_bots")
        )
        markup.row(
            InlineKeyboardButton("🏠 رجوع للقايمة الرئيسية", callback_data="main_menu"),
            InlineKeyboardButton("⬅️ رجوع للسابقة", callback_data="go_back")
        )
        
        msg = bot.send_message(chat_id, "📚 المكتبة:", reply_markup=markup)
        add_message_to_history(chat_id, user_id, msg.message_id)
        add_to_page_history(user_id, "library")
    except Exception as e:
        logging.error(f"فشل في إرسال قايمة المكتبة لـ {user_id}: {e}")

def search_bots(chat_id, user_id):
    try:
        delete_previous_messages(chat_id, user_id)
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("❌ إلغاء", callback_data="cancel_search"))
        msg = bot.send_message(chat_id, "🔍 أرسل كلمة للبحث عن بوت (بالاسم أو الوصف):", reply_markup=markup)
        user_states[user_id] = "searching_bots"
        add_message_to_history(chat_id, user_id, msg.message_id)
        add_to_page_history(user_id, "search_bots")
    except Exception as e:
        logging.error(f"فشل في بدء البحث لـ {user_id}: {e}")

def show_search_results(chat_id, user_id, query):
    try:
        delete_previous_messages(chat_id, user_id)
        user_data = global_data["users"].get(str(user_id), {"bots": []})
        bots = user_data.get("bots", [])
        
        results = [(i, bot) for i, bot in enumerate(bots) if query.lower() in bot["name"].lower() or query.lower() in bot["description"].lower()]
        
        if not results:
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("🏠 رجوع للقايمة الرئيسية", callback_data="main_menu"),
                InlineKeyboardButton("⬅️ رجوع للسابقة", callback_data="go_back")
            )
            msg = bot.send_message(chat_id, "❌ لا توجد نتائج مطابقة!", reply_markup=markup)
            add_message_to_history(chat_id, user_id, msg.message_id)
            return
        
        markup = InlineKeyboardMarkup()
        for bot_index, bot_item in results:
            markup.row(InlineKeyboardButton(f"{bot_item['name']}", callback_data=f"view_bot_{bot_index}"))
        markup.row(
            InlineKeyboardButton("🏠 رجوع للقايمة الرئيسية", callback_data="main_menu"),
            InlineKeyboardButton("⬅️ رجوع للسابقة", callback_data="go_back")
        )
        
        msg = bot.send_message(chat_id, f"🔍 نتائج البحث عن '{query}':", reply_markup=markup)
        add_message_to_history(chat_id, user_id, msg.message_id)
        add_to_page_history(user_id, "search_results")
    except Exception as e:
        logging.error(f"فشل في عرض نتائج البحث لـ {user_id}: {e}")

def my_bots_menu(chat_id, user_id, page=1):
    try:
        delete_previous_messages(chat_id, user_id)
        user_data = global_data["users"].get(str(user_id), {"bots": []})
        bots = user_data.get("bots", [])
        
        if not bots:
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("🏠 رجوع للقايمة الرئيسية", callback_data="main_menu"),
                InlineKeyboardButton("⬅️ رجوع للسابقة", callback_data="go_back")
            )
            msg = bot.send_message(chat_id, "📜 لا يوجد بوتات مضافة!", reply_markup=markup)
            add_message_to_history(chat_id, user_id, msg.message_id)
            return
        
        items_per_page = 10
        total_pages = (len(bots) + items_per_page - 1) // items_per_page
        page = max(1, min(page, total_pages))
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        current_bots = bots[start_idx:end_idx]
        
        markup = InlineKeyboardMarkup()
        for i, bot_item in enumerate(current_bots):
            bot_idx = start_idx + i
            markup.row(InlineKeyboardButton(f"{bot_item['name']}", callback_data=f"view_bot_{bot_idx}"))
        
        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️ السابقة", callback_data=f"my_bots_page_{page-1}"))
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton("➡️ التالية", callback_data=f"my_bots_page_{page+1}"))
        if nav_buttons:
            markup.row(*nav_buttons)
        
        markup.row(
            InlineKeyboardButton("🏠 رجوع للقايمة الرئيسية", callback_data="main_menu"),
            InlineKeyboardButton("⬅️ رجوع للسابقة", callback_data="go_back")
        )
        
        msg = bot.send_message(chat_id, f"📜 بوتاتك (الصفحة {page} من {total_pages}):", reply_markup=markup)
        add_message_to_history(chat_id, user_id, msg.message_id)
        add_to_page_history(user_id, "my_bots")
        pagination_state[user_id] = page
    except Exception as e:
        logging.error(f"فشل في إرسال قايمة بوتاتي لـ {user_id}: {e}")

def view_bot_details(chat_id, user_id, bot_index):
    try:
        delete_previous_messages(chat_id, user_id)
        user_data = global_data["users"].get(str(user_id), {"bots": []})
        bots = user_data.get("bots", [])
        
        if bot_index >= len(bots):
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("🏠 رجوع للقايمة الرئيسية", callback_data="main_menu"),
                InlineKeyboardButton("⬅️ رجوع للسابقة", callback_data="go_back")
            )
            msg = bot.send_message(chat_id, "❌ البوت غير موجود!", reply_markup=markup)
            add_message_to_history(chat_id, user_id, msg.message_id)
            return
        
        bot_item = bots[bot_index]
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("🔗 فتح البوت", url=bot_item["link"]),
            InlineKeyboardButton("ℹ️ معلومات", callback_data=f"show_bot_info_{bot_index}")
        )
        markup.row(
            InlineKeyboardButton("✏️ تعديل", callback_data=f"edit_bot_{bot_index}"),
            InlineKeyboardButton("🗑️ حذف", callback_data=f"confirm_delete_bot_{bot_index}")
        )
        markup.row(
            InlineKeyboardButton("🏠 رجوع للقايمة الرئيسية", callback_data="main_menu"),
            InlineKeyboardButton("⬅️ رجوع للسابقة", callback_data="go_back")
        )
        
        msg = bot.send_message(chat_id, f"🤖 {bot_item['name']}", reply_markup=markup)
        add_message_to_history(chat_id, user_id, msg.message_id)
        add_to_page_history(user_id, "view_bot")
    except Exception as e:
        logging.error(f"فشل في عرض تفاصيل البوت لـ {user_id}: {e}")

def show_bot_info(chat_id, user_id, bot_index):
    try:
        delete_previous_messages(chat_id, user_id)
        user_data = global_data["users"].get(str(user_id), {"bots": []})
        bots = user_data.get("bots", [])
        bot_item = bots[bot_index]
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("🏠 رجوع للقايمة الرئيسية", callback_data="main_menu"),
            InlineKeyboardButton("⬅️ رجوع للسابقة", callback_data="go_back")
        )
        msg = bot.send_message(chat_id, f"ℹ️ معلومات {bot_item['name']}:\n{bot_item['description']}", reply_markup=markup)
        add_message_to_history(chat_id, user_id, msg.message_id)
        add_to_page_history(user_id, "show_bot_info")
    except Exception as e:
        logging.error(f"فشل في عرض معلومات البوت لـ {user_id}: {e}")

def admin_panel(chat_id, user_id):
    try:
        delete_previous_messages(chat_id, user_id)
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("📚 إدارة المكتبة", callback_data="admin_library"),
            InlineKeyboardButton("👤 إدارة المستخدمين", callback_data="admin_users")
        )
        markup.add(
            InlineKeyboardButton("📋 إدارة المهام", callback_data="admin_tasks"),
            InlineKeyboardButton("📊 إحصائيات المشروع", callback_data="admin_stats")
        )
        markup.add(
            InlineKeyboardButton("🗑️ تنظيف القروب", callback_data="admin_clean"),
            InlineKeyboardButton("⚙️ الإعدادات", callback_data="admin_settings")
        )
        markup.row(
            InlineKeyboardButton("🏠 رجوع للقايمة الرئيسية", callback_data="main_menu"),
            InlineKeyboardButton("⬅️ رجوع للسابقة", callback_data="go_back")
        )
        
        msg = bot.send_message(chat_id, "🛠️ لوحة الأدمن:", reply_markup=markup)
        add_message_to_history(chat_id, user_id, msg.message_id)
        add_to_page_history(user_id, "admin_panel")
    except Exception as e:
        logging.error(f"فشل في إرسال لوحة الأدمن لـ {user_id}: {e}")

def admin_library_menu(chat_id, user_id):
    try:
        delete_previous_messages(chat_id, user_id)
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("📜 عرض البوتات", callback_data="admin_view_bots"),
            InlineKeyboardButton("✅ اعتماد بوت", callback_data="admin_verify_bot")
        )
        markup.row(
            InlineKeyboardButton("🏠 رجوع للقايمة الرئيسية", callback_data="main_menu"),
            InlineKeyboardButton("⬅️ رجوع للسابقة", callback_data="go_back")
        )
        
        msg = bot.send_message(chat_id, "📚 إدارة المكتبة:", reply_markup=markup)
        add_message_to_history(chat_id, user_id, msg.message_id)
        add_to_page_history(user_id, "admin_library")
    except Exception as e:
        logging.error(f"فشل في إرسال إدارة المكتبة لـ {user_id}: {e}")

def admin_view_bots(chat_id, user_id):
    try:
        delete_previous_messages(chat_id, user_id)
        all_bots = []
        for uid, user_data in global_data["users"].items():
            bots = user_data.get("bots", [])
            for i, bot_item in enumerate(bots):
                all_bots.append((uid, i, bot_item))
        
        if not all_bots:
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("🏠 رجوع للقايمة الرئيسية", callback_data="main_menu"),
                InlineKeyboardButton("⬅️ رجوع للسابقة", callback_data="go_back")
            )
            msg = bot.send_message(chat_id, "📜 لا يوجد بوتات مضافة!", reply_markup=markup)
            add_message_to_history(chat_id, user_id, msg.message_id)
            return
        
        markup = InlineKeyboardMarkup()
        for uid, bot_index, bot_item in all_bots:
            markup.row(
                InlineKeyboardButton(f"{bot_item['name']} (المستخدم: {uid})", callback_data=f"view_admin_bot_{uid}_{bot_index}"),
                InlineKeyboardButton("✅ اعتماد", callback_data=f"verify_bot_{uid}_{bot_index}")
            )
        markup.row(
            InlineKeyboardButton("🏠 رجوع للقايمة الرئيسية", callback_data="main_menu"),
            InlineKeyboardButton("⬅️ رجوع للسابقة", callback_data="go_back")
        )
        
        msg = bot.send_message(chat_id, "📜 البوتات المضافة:", reply_markup=markup)
        add_message_to_history(chat_id, user_id, msg.message_id)
        add_to_page_history(user_id, "admin_view_bots")
    except Exception as e:
        logging.error(f"فشل في عرض البوتات للأدمن لـ {user_id}: {e}")

# معالجة الأوامر
@bot.message_handler(commands=['start'])
def command_start(message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        delete_previous_messages(chat_id, user_id)
        bot.delete_message(chat_id, message.message_id)
        
        args = message.text.split()
        if len(args) > 1 and args[1].startswith("ref_"):
            referrer_id = args[1].split("_")[1]
            if referrer_id != str(user_id):
                if str(user_id) not in global_data["users"]:
                    global_data["users"][str(user_id)] = {"points": 0, "referrals": 0, "bots": []}
                    if str(referrer_id) in global_data["users"]:
                        global_data["users"][str(referrer_id)]["referrals"] += 1
                        global_data["users"][str(referrer_id)]["points"] += 10
                        save_data()
                        bot.send_message(int(referrer_id), "🎉 صديق جديد انضم برابطك! +10 نقاط")
        
        if str(user_id) not in global_data["users"]:
            global_data["users"][str(user_id)] = {"points": 0, "referrals": 0, "bots": []}
            save_data()
        
        main_menu(chat_id, user_id)
    except Exception as e:
        logging.error(f"خطأ في معالجة /start لـ {user_id}: {e}")

# معالجة الضغطات
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        delete_previous_messages(chat_id, user_id)
        
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("🏠 رجوع للقايمة الرئيسية", callback_data="main_menu"),
            InlineKeyboardButton("⬅️ رجوع للسابقة", callback_data="go_back")
        )
        
        if call.data == "main_menu":
            main_menu(chat_id, user_id)
        elif call.data == "go_back":
            if user_id in page_history and len(page_history[user_id]) > 1:
                page_history[user_id].pop()
                previous_page = page_history[user_id][-1]
                if previous_page == "main_menu":
                    main_menu(chat_id, user_id)
                elif previous_page == "library":
                    library_menu(chat_id, user_id)
                elif previous_page == "my_bots":
                    page = pagination_state.get(user_id, 1)
                    my_bots_menu(chat_id, user_id, page)
                elif previous_page == "admin_panel":
                    admin_panel(chat_id, user_id)
                elif previous_page == "admin_library":
                    admin_library_menu(chat_id, user_id)
                elif previous_page == "admin_view_bots":
                    admin_view_bots(chat_id, user_id)
                elif previous_page == "view_bot":
                    bot_index = user_inputs.get(user_id, {}).get("bot_index", 0)
                    view_bot_details(chat_id, user_id, bot_index)
                else:
                    main_menu(chat_id, user_id)
            else:
                main_menu(chat_id, user_id)
        elif call.data == "my_profile":
            user_data = global_data["users"].get(str(user_id), {"points": 0, "referrals": 0})
            user_name = call.from_user.first_name or "مستخدم"
            username = call.from_user.username or "غير متاح"
            points = user_data["points"]
            referrals = user_data["referrals"]
            rank = get_rank(points)
            profile_text = (
                f"📁 ملفك الشخصي:\n"
                f"الاسم: {user_name}\n"
                f"المعرف: @{username}\n"
                f"ID: {user_id}\n"
                f"نقاطك: {points}\n"
                f"رتبتك: {rank}\n"
                f"إحالاتك: {referrals}"
            )
            msg = bot.send_message(chat_id, profile_text, reply_markup=markup)
            add_message_to_history(chat_id, user_id, msg.message_id)
            add_to_page_history(user_id, "my_profile")
        elif call.data == "library":
            library_menu(chat_id, user_id)
        elif call.data == "search_bots":
            search_bots(chat_id, user_id)
        elif call.data == "cancel_search":
            library_menu(chat_id, user_id)
        elif call.data == "add_bot":
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_bot"))
            msg = bot.send_message(chat_id, "📝 أرسل لينك البوت (مثال: t.me/bot):", reply_markup=markup)
            user_states[user_id] = "adding_bot_link"
            add_message_to_history(chat_id, user_id, msg.message_id)
            add_to_page_history(user_id, "add_bot")
        elif call.data.startswith("my_bots_page_"):
            page = int(call.data.split("_")[-1])
            my_bots_menu(chat_id, user_id, page)
        elif call.data.startswith("view_bot_"):
            bot_index = int(call.data.split("_")[-1])
            user_inputs[user_id] = {"bot_index": bot_index}
            view_bot_details(chat_id, user_id, bot_index)
        elif call.data.startswith("show_bot_info_"):
            bot_index = int(call.data.split("_")[-1])
            user_inputs[user_id] = {"bot_index": bot_index}
            show_bot_info(chat_id, user_id, bot_index)
        elif call.data.startswith("edit_bot_"):
            bot_index = int(call.data.split("_")[-1])
            user_inputs[user_id] = {"bot_index": bot_index}
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_bot"))
            msg = bot.send_message(chat_id, "📝 أرسل لينك البوت الجديد (مثال: t.me/bot):", reply_markup=markup)
            user_states[user_id] = "editing_bot_link"
            add_message_to_history(chat_id, user_id, msg.message_id)
            add_to_page_history(user_id, "edit_bot")
        elif call.data.startswith("confirm_delete_bot_"):
            bot_index = int(call.data.split("_")[-1])
            user_inputs[user_id] = {"bot_index": bot_index}
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("✅ تأكيد الحذف", callback_data=f"delete_bot_{bot_index}"),
                InlineKeyboardButton("❌ إلغاء", callback_data="cancel_delete_bot")
            )
            msg = bot.send_message(chat_id, "⚠️ هل أنت متأكد من حذف هذا البوت؟", reply_markup=markup)
            add_message_to_history(chat_id, user_id, msg.message_id)
            add_to_page_history(user_id, "confirm_delete_bot")
        elif call.data.startswith("delete_bot_"):
            bot_index = int(call.data.split("_")[-1])
            user_data = global_data["users"].get(str(user_id), {"bots": []})
            user_data["bots"].pop(bot_index)
            global_data["users"][str(user_id)] = user_data
            save_data()
            msg = bot.send_message(chat_id, "🗑️ تم حذف البوت بنجاح!", reply_markup=markup)
            add_message_to_history(chat_id, user_id, msg.message_id)
        elif call.data == "cancel_delete_bot":
            bot_index = user_inputs.get(user_id, {}).get("bot_index", 0)
            view_bot_details(chat_id, user_id, bot_index)
        elif call.data == "cancel_add_bot":
            user_states.pop(user_id, None)
            user_inputs.pop(user_id, None)
            library_menu(chat_id, user_id)
        elif call.data == "confirm_bot_link":
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("✅ تأكيد", callback_data="confirm_bot_description"),
                InlineKeyboardButton("✏️ تعديل", callback_data="edit_bot_link"),
                InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_bot")
            )
            bot_link = user_inputs.get(user_id, {}).get("link", "")
            msg = bot.send_message(chat_id, f"📝 لينك البوت:\n{bot_link}", reply_markup=markup)
            add_message_to_history(chat_id, user_id, msg.message_id)
        elif call.data == "edit_bot_link":
            user_states[user_id] = "editing_bot_link"
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_bot"))
            msg = bot.send_message(chat_id, "📝 أرسل لينك البوت الجديد (مثال: t.me/bot):", reply_markup=markup)
            add_message_to_history(chat_id, user_id, msg.message_id)
        elif call.data == "confirm_bot_description":
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("✅ تأكيد", callback_data="confirm_bot_name"),
                InlineKeyboardButton("✏️ تعديل", callback_data="edit_bot_description"),
                InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_bot")
            )
            bot_description = user_inputs.get(user_id, {}).get("description", "")
            msg = bot.send_message(chat_id, f"📝 وصف البوت:\n{bot_description}", reply_markup=markup)
            add_message_to_history(chat_id, user_id, msg.message_id)
        elif call.data == "edit_bot_description":
            user_states[user_id] = "editing_bot_description"
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_bot"))
            msg = bot.send_message(chat_id, "📝 أرسل وصف البوت الجديد:", reply_markup=markup)
            add_message_to_history(chat_id, user_id, msg.message_id)
        elif call.data == "confirm_bot_name":
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("✅ تأكيد", callback_data="confirm_add_bot"),
                InlineKeyboardButton("✏️ تعديل", callback_data="edit_bot_name"),
                InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_bot")
            )
            bot_name = user_inputs.get(user_id, {}).get("name", "")
            msg = bot.send_message(chat_id, f"📝 اسم البوت:\n{bot_name}", reply_markup=markup)
            add_message_to_history(chat_id, user_id, msg.message_id)
        elif call.data == "edit_bot_name":
            user_states[user_id] = "editing_bot_name"
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_bot"))
            msg = bot.send_message(chat_id, "📝 أرسل اسم البوت الجديد:", reply_markup=markup)
            add_message_to_history(chat_id, user_id, msg.message_id)
        elif call.data == "confirm_add_bot":
            user_data = global_data["users"].get(str(user_id), {"bots": []})
            bot_info = user_inputs.get(user_id, {})
            if "bot_index" in bot_info:  # تعديل بوت موجود
                bot_index = bot_info["bot_index"]
                user_data["bots"][bot_index] = {"link": bot_info["link"], "description": bot_info["description"], "name": bot_info["name"]}
            else:  # إضافة بوت جديد
                user_data.setdefault("bots", []).append(bot_info)
            global_data["users"][str(user_id)] = user_data
            save_data()
            user_states.pop(user_id, None)
            user_inputs.pop(user_id, None)
            msg = bot.send_message(chat_id, "✅ تمت العملية بنجاح!", reply_markup=markup)
            add_message_to_history(chat_id, user_id, msg.message_id)
        elif call.data == "verified_bots":
            verified_bots = global_data.get("verified_bots", [])
            if not verified_bots:
                msg = bot.send_message(chat_id, "✅ لا يوجد بوتات معتمدة!", reply_markup=markup)
            else:
                bots_text = "\n".join([f"{i+1}. {bot['name']} - {bot['description']}" for i, bot in enumerate(verified_bots)])
                msg = bot.send_message(chat_id, f"✅ البوتات المعتمدة:\n{bots_text}", reply_markup=markup)
            add_message_to_history(chat_id, user_id, msg.message_id)
        elif call.data == "invite_friends":
            referral_link = f"https://t.me/{bot.get_me().username}?start=ref_{user_id}"
            user_data = global_data["users"].get(str(user_id), {"points": 0, "referrals": 0})
            referrals = user_data["referrals"]
            points = user_data["points"]
            msg_text = (
                f"👥 رابط الدعوة الخاص بك:\n{referral_link}\n"
                f"شارك الرابط لكسب 10 نقاط لكل صديق!\n"
                f"إحالاتك: {referrals} | نقاطك: {points}"
            )
            msg = bot.send_message(chat_id, msg_text, reply_markup=markup)
            add_message_to_history(chat_id, user_id, msg.message_id)
            add_to_page_history(user_id, "invite_friends")
        elif call.data == "tasks":
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("📩 إرسال شكوى (10 نقاط)", callback_data="complaint"),
                InlineKeyboardButton("👥 دعوة صديق (10 نقاط)", callback_data="invite_friends")
            )
            markup.row(
                InlineKeyboardButton("🏠 رجوع للقايمة الرئيسية", callback_data="main_menu"),
                InlineKeyboardButton("⬅️ رجوع للسابقة", callback_data="go_back")
            )
            msg = bot.send_message(chat_id, "📋 المهام المتاحة:", reply_markup=markup)
            add_message_to_history(chat_id, user_id, msg.message_id)
            add_to_page_history(user_id, "tasks")
        elif call.data == "settings":
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("⚙️ لسه تحت التطوير", callback_data="under_dev"))
            markup.row(
                InlineKeyboardButton("🏠 رجوع للقايمة الرئيسية", callback_data="main_menu"),
                InlineKeyboardButton("⬅️ رجوع للسابقة", callback_data="go_back")
            )
            msg = bot.send_message(chat_id, "⚙️ الإعدادات:", reply_markup=markup)
            add_message_to_history(chat_id, user_id, msg.message_id)
            add_to_page_history(user_id, "settings")
        elif call.data == "about":
            msg = bot.send_message(chat_id, "ℹ️ بوت لإدارة الأيردروبات!", reply_markup=markup)
            add_message_to_history(chat_id, user_id, msg.message_id)
            add_to_page_history(user_id, "about")
        elif call.data == "complaint":
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("❌ إلغاء", callback_data="cancel_action"))
            msg = bot.send_message(chat_id, "📩 أرسل شكواك:", reply_markup=markup)
            user_states[user_id] = "sending_complaint"
            add_message_to_history(chat_id, user_id, msg.message_id)
            add_to_page_history(user_id, "complaint")
        elif call.data == "stats":
            total_users = len(global_data["users"])
            total_bots = sum(len(user_data.get("bots", [])) for user_data in global_data["users"].values())
            total_verified = len(global_data["verified_bots"])
            stats_text = (
                f"📊 الإحصائيات:\n"
                f"عدد المستخدمين: {total_users}\n"
                f"عدد البوتات المضافة: {total_bots}\n"
                f"عدد البوتات المعتمدة: {total_verified}"
            )
            msg = bot.send_message(chat_id, stats_text, reply_markup=markup)
            add_message_to_history(chat_id, user_id, msg.message_id)
            add_to_page_history(user_id, "stats")
        elif call.data == "admin_panel":
            if user_id in ADMIN_IDS:
                admin_panel(chat_id, user_id)
            else:
                msg = bot.send_message(chat_id, "🚫 متاح للأدمن فقط!", reply_markup=markup)
                add_message_to_history(chat_id, user_id, msg.message_id)
        elif call.data == "admin_library":
            if user_id in ADMIN_IDS:
                admin_library_menu(chat_id, user_id)
        elif call.data == "admin_view_bots":
            if user_id in ADMIN_IDS:
                admin_view_bots(chat_id, user_id)
        elif call.data.startswith("verify_bot_"):
            if user_id in ADMIN_IDS:
                uid, bot_index = map(int, call.data.split("_")[2:])
                user_data = global_data["users"].get(str(uid), {"bots": []})
                bot_to_verify = user_data["bots"].pop(bot_index)
                global_data["verified_bots"].append(bot_to_verify)
                global_data["users"][str(uid)] = user_data
                save_data()
                msg = bot.send_message(chat_id, "✅ تم اعتماد البوت!", reply_markup=markup)
                add_message_to_history(chat_id, user_id, msg.message_id)
        elif call.data == "admin_users":
            if user_id in ADMIN_IDS:
                markup = InlineKeyboardMarkup()
                for uid in global_data["users"].keys():
                    user_data = global_data["users"][uid]
                    markup.add(InlineKeyboardButton(f"ID: {uid} - نقاط: {user_data['points']}", callback_data=f"view_user_{uid}"))
                markup.row(
                    InlineKeyboardButton("🏠 رجوع للقايمة الرئيسية", callback_data="main_menu"),
                    InlineKeyboardButton("⬅️ رجوع للسابقة", callback_data="go_back")
                )
                msg = bot.send_message(chat_id, "👤 إدارة المستخدمين:", reply_markup=markup)
                add_message_to_history(chat_id, user_id, msg.message_id)
                add_to_page_history(user_id, "admin_users")
        elif call.data == "admin_clean":
            if user_id in ADMIN_IDS:
                last_messages.clear()
                msg = bot.send_message(chat_id, "🗑️ تم تنظيف الرسائل!", reply_markup=markup)
                add_message_to_history(chat_id, user_id, msg.message_id)
        elif call.data.startswith("admin_"):
            if user_id not in ADMIN_IDS:
                msg = bot.send_message(chat_id, "🚫 متاح للأدمن فقط!", reply_markup=markup)
                add_message_to_history(chat_id, user_id, msg.message_id)
            else:
                msg = bot.send_message(chat_id, "⚙️ تحت التطوير!", reply_markup=markup)
                add_message_to_history(chat_id, user_id, msg.message_id)
        else:
            msg = bot.send_message(chat_id, "عذرًا، هذا الخيار غير متاح!", reply_markup=markup)
            add_message_to_history(chat_id, user_id, msg.message_id)
    except Exception as e:
        logging.error(f"خطأ في معالجة الضغط لـ {user_id}: {e}")

# معالجة الإدخال
@bot.message_handler(func=lambda message: True)
def handle_user_input(message):
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        text = message.text
        bot.delete_message(chat_id, message.message_id)
        
        if user_id in user_states:
            delete_previous_messages(chat_id, user_id)
            state = user_states[user_id]
            
            if state == "searching_bots":
                user_states.pop(user_id)
                show_search_results(chat_id, user_id, text)
            elif state == "adding_bot_link":
                user_inputs.setdefault(user_id, {})["link"] = text
                user_states[user_id] = "adding_bot_description"
                markup = InlineKeyboardMarkup()
                markup.row(InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_bot"))
                msg = bot.send_message(chat_id, "📝 أرسل وصف البوت:", reply_markup=markup)
                add_message_to_history(chat_id, user_id, msg.message_id)
            elif state == "adding_bot_description":
                user_inputs[user_id]["description"] = text
                user_states[user_id] = "adding_bot_name"
                markup = InlineKeyboardMarkup()
                markup.row(InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_bot"))
                msg = bot.send_message(chat_id, "📝 أرسل اسم البوت:", reply_markup=markup)
                add_message_to_history(chat_id, user_id, msg.message_id)
            elif state == "adding_bot_name":
                user_inputs[user_id]["name"] = text
                markup = InlineKeyboardMarkup()
                markup.row(
                    InlineKeyboardButton("✅ تأكيد", callback_data="confirm_bot_link"),
                    InlineKeyboardButton("✏️ تعديل", callback_data="edit_bot_link"),
                    InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_bot")
                )
                msg = bot.send_message(chat_id, f"📝 لينك البوت:\n{user_inputs[user_id]['link']}", reply_markup=markup)
                add_message_to_history(chat_id, user_id, msg.message_id)
            elif state == "editing_bot_link":
                user_inputs[user_id]["link"] = text
                markup = InlineKeyboardMarkup()
                markup.row(
                    InlineKeyboardButton("✅ تأكيد", callback_data="confirm_bot_description"),
                    InlineKeyboardButton("✏️ تعديل", callback_data="edit_bot_link"),
                    InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_bot")
                )
                msg = bot.send_message(chat_id, f"📝 لينك البوت المعدل:\n{text}", reply_markup=markup)
                add_message_to_history(chat_id, user_id, msg.message_id)
                user_states[user_id] = "editing_bot_description"
            elif state == "editing_bot_description":
                user_inputs[user_id]["description"] = text
                markup = InlineKeyboardMarkup()
                markup.row(
                    InlineKeyboardButton("✅ تأكيد", callback_data="confirm_bot_name"),
                    InlineKeyboardButton("✏️ تعديل", callback_data="edit_bot_description"),
                    InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_bot")
                )
                msg = bot.send_message(chat_id, f"📝 وصف البوت المعدل:\n{text}", reply_markup=markup)
                add_message_to_history(chat_id, user_id, msg.message_id)
                user_states[user_id] = "editing_bot_name"
            elif state == "editing_bot_name":
                user_inputs[user_id]["name"] = text
                markup = InlineKeyboardMarkup()
                markup.row(
                    InlineKeyboardButton("✅ تأكيد", callback_data="confirm_add_bot"),
                    InlineKeyboardButton("✏️ تعديل", callback_data="edit_bot_name"),
                    InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_bot")
                )
                msg = bot.send_message(chat_id, f"📝 اسم البوت المعدل:\n{text}", reply_markup=markup)
                add_message_to_history(chat_id, user_id, msg.message_id)
            elif state == "sending_complaint":
                user_inputs[user_id] = {"complaint": text}
                markup = InlineKeyboardMarkup()
                markup.row(
                    InlineKeyboardButton("✅ تأكيد", callback_data="confirm_complaint"),
                    InlineKeyboardButton("✏️ تعديل", callback_data="edit_complaint"),
                    InlineKeyboardButton("❌ إلغاء", callback_data="cancel_action")
                )
                msg = bot.send_message(chat_id, f"📩 شكواك:\n{text}", reply_markup=markup)
                add_message_to_history(chat_id, user_id, msg.message_id)
    except Exception as e:
        logging.error(f"خطأ في معالجة الإدخال لـ {user_id}: {e}")

@bot.callback_query_handler(func=lambda call: call.data in ["confirm_complaint", "edit_complaint"])
def handle_complaint_confirmation(call):
    try:
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        delete_previous_messages(chat_id, user_id)
        
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("🏠 رجوع للقايمة الرئيسية", callback_data="main_menu"),
            InlineKeyboardButton("⬅️ رجوع للسابقة", callback_data="go_back")
        )
        
        if call.data == "confirm_complaint":
            user_data = global_data["users"].get(str(user_id), {"points": 0, "referrals": 0})
            user_data["points"] += 10
            global_data["users"][str(user_id)] = user_data
            save_data()
            user_states.pop(user_id, None)
            user_inputs.pop(user_id, None)
            msg = bot.send_message(chat_id, "✅ تم تسجيل شكواك وحصلت على 10 نقاط!", reply_markup=markup)
            add_message_to_history(chat_id, user_id, msg.message_id)
        elif call.data == "edit_complaint":
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("❌ إلغاء", callback_data="cancel_action"))
            msg = bot.send_message(chat_id, "📩 أرسل شكواك مرة أخرى:", reply_markup=markup)
            user_states[user_id] = "sending_complaint"
            add_message_to_history(chat_id, user_id, msg.message_id)
    except Exception as e:
        logging.error(f"خطأ في معالجة الشكوى لـ {user_id}: {e}")

# تشغيل البوت
def run_bot():
    while True:
        try:
            print("البوت شغال...")
            logging.info("بدء تشغيل البوت...")
            bot.polling(non_stop=True, interval=1, timeout=20)
        except (ConnectionError, ReadTimeout) as e:
            logging.error(f"خطأ في الاتصال: {e}")
            time.sleep(5)
        except Exception as e:
            logging.error(f"خطأ غير متوقع: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_bot()