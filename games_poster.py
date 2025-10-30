# =============================================================================
#           *** بوت COSMOS للألعاب - الإصدار 1.1 ***
#
#  (نسخة الاختبار - تم إلغاء الترجمة بالكامل)
# =============================================================================

import requests
import os
import sys
import random
import datetime
import re

# --- [1] الإعدادات والمفاتيح السرية ---
try:
    GAMES_API_KEY = os.environ['GAMES_API_KEY']
    BOT_TOKEN = os.environ['BOT_TOKEN']
    CHANNEL_USERNAME = os.environ['CHANNEL_USERNAME'] 
except KeyError as e:
    print(f"!!! خطأ: متغير البيئة الأساسي غير موجود: {e}")
    sys.exit(1)

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
RAWG_BASE_URL = "https://api.rawg.io/api"

# --- [2] الدوال المساعدة (النشر) ---

def clean_text(text):
    if not text: return ""
    clean_text = re.sub(r'<[^>]+>', '', text)
    clean_text = re.sub(r'https?://[^\s\n\r]+', '', clean_text)
    clean_text = re.sub(r'www\.[^\s\n\r]+', '', clean_text)
    return clean_text.strip()

# --- (تم إلغاء دالة الترجمة بناءً على طلبك) ---

def post_text_to_telegram(text_content):
    print(f"... جاري إرسال (النص الكامل) إلى {CHANNEL_USERNAME} ...")
    url = f"{TELEGRAM_API_URL}/sendMessage"
    if len(text_content) > 4096: text_content = text_content[:4093] + "..."
    payload = { 'chat_id': CHANNEL_USERNAME, 'text': text_content, 'parse_mode': 'Markdown' }
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        print(">>> تم إرسال (النص الكامل) بنجاح!")
    except requests.exceptions.RequestException as e:
        print(f"!!! فشل إرسال (النص الكامل): {e} - {getattr(response, 'text', 'لا يوجد رد')}")
        # (سنقوم بطباعة الخطأ ولكننا لن نوقف الكود)

def post_photo_to_telegram(image_url, caption):
    print(f"... جاري تحميل الصورة من الرابط: {image_url} ...")
    try:
        image_response = requests.get(image_url, timeout=60)
        image_response.raise_for_status()
        image_data = image_response.content
        print(f"...تم تحميل الصورة بنجاح (الحجم: {len(image_data) / 1024:.2f} كيلوبايت)")
    except requests.exceptions.RequestException as e:
        print(f"!!! فشل تحميل الصورة من المصدر: {e}")
        return False

    print(f"... جاري رفع (الصورة + النص القصير) إلى {CHANNEL_USERNAME} ...")
    url = f"{TELEGRAM_API_URL}/sendPhoto"
    payload = { 'chat_id': CHANNEL_USERNAME, 'caption': caption, 'parse_mode': 'Markdown' }
    files = { 'photo': ('game_image.jpg', image_data) }
    try:
        response = requests.post(url, data=payload, files=files, timeout=120)
        response.raise_for_status()
        print(">>> 🎉🎉🎉 تم إرسال (الصورة) بنجاح! 🎉🎉🎉")
        return True
    except requests.exceptions.RequestException as e:
        print(f"!!! فشل إرسال (الصورة): {e} - {getattr(response, 'text', 'لا يوجد رد')}")
        return False

# --- [3] دوال جلب الألعاب (الجديدة) ---

def get_game_details(game_id):
    print(f"... جاري جلب التفاصيل الكاملة للعبة ID: {game_id} ...")
    try:
        url = f"{RAWG_BASE_URL}/games/{game_id}?key={GAMES_API_KEY}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"!!! فشل جلب التفاصيل الكاملة: {e}")
        return None

def get_game_list(endpoint, params={}):
    try:
        default_params = { 'key': GAMES_API_KEY, 'page_size': 10, 'metacritic__gt': 60 }
        all_params = {**default_params, **params}
        url = f"{RAWG_BASE_URL}/{endpoint}"
        response = requests.get(url, params=all_params, timeout=60)
        response.raise_for_status()
        data = response.json()
        if data.get('results'):
            game = random.choice(data['results'])
            return game.get('id')
        else:
            print(f"... لم يتم العثور على نتائج لـ {endpoint} بالمعايير {params}")
            return None
    except Exception as e:
        print(f"!!! فشل جلب قائمة الألعاب: {e}")
        return None

def format_platforms(platforms_list):
    if not platforms_list: return "Unknown"
    main_platforms = [p['platform']['name'] for p in platforms_list]
    return ", ".join(main_platforms)
    
def format_developers(developers_list):
    if not developers_list: return "Unknown"
    return ", ".join([d['name'] for d in developers_list])

# --- [4] دوال "المهام" (الخطة المتنوعة) ---

def run_job(job_name, endpoint, params={}):
    print(f"--- بدء مهمة [{job_name}] ---")
    game_id = get_game_list(endpoint, params)
    if not game_id:
        print(f"!!! فشلت مهمة [{job_name}] - لم يتم العثور على لعبة.")
        return

    details = get_game_details(game_id)
    if not details:
        print(f"!!! فشلت مهمة [{job_name}] - لم يتم العثور على تفاصيل اللعبة.")
        return

    # 3. استخراج البيانات (باللغة الإنجليزية فقط)
    title_en = details.get('name', 'N/A')
    description_en_dirty = details.get('description_raw', 'No description available.')
    description_en_clean = clean_text(description_en_dirty)
    image_url = details.get('background_image')
    metacritic = details.get('metacritic')
    released = details.get('released', 'N/A')
    platforms_en = format_platforms(details.get('parent_platforms', []))
    developers_en = format_developers(details.get('developers', []))

    if not image_url:
        print("!!! فشلت المهمة - اللعبة لا تحتوي على صورة خلفية.")
        return

    # 5. إرسال "الرسالتين" (باللغة الإنجليزية)
    
    # الرسالة 1: الصورة + العنوان
    metacritic_tag = f"⭐️ {metacritic}" if metacritic else ""
    short_caption = f"🎮 **{title_en}**\n\n*({released})* {metacritic_tag}"
    
    # الرسالة 2: التفاصيل الكاملة
    full_text = (
        f"**{title_en}**\n\n"
        f"{description_en_clean}\n\n"
        f"---\n"
        f"**Platforms:** {platforms_en}\n"
        f"**Developers:** {developers_en}\n\n"
        f"*Follow us for more at {CHANNEL_USERNAME}*"
    )
    
    if post_photo_to_telegram(image_url, short_caption):
        post_text_to_telegram(full_text)

# --- [5] التشغيل الرئيسي (الذكي) ---
def main():
    print("==========================================")
    print(f"بدء تشغيل (v1.1 - بوت الألعاب - بدون ترجمة)...")
    
    current_hour_utc = datetime.datetime.now(datetime.timezone.utc).hour
    print(f"Current UTC Hour: {current_hour_utc}")
    
    today = datetime.date.today()
    last_30_days = today - datetime.timedelta(days=30)
    today_str = today.strftime('%Y-%m-%d')
    last_30_days_str = last_30_days.strftime('%Y-%m-%d')

    if current_hour_utc == 0: 
        run_job("New Release 🚀", "games", {'dates': f"{last_30_days_str},{today_str}", 'ordering': '-added'})
    elif current_hour_utc == 4: 
        run_job("Top Rated ⭐️", "games", {'ordering': '-metacritic'})
    elif current_hour_utc == 8: 
        run_job("Action 💥", "games", {'genres': 'action'})
    elif current_hour_utc == 12: 
        run_job("RPG 📜", "games", {'genres': 'role-playing-games-rpg'})
    elif current_hour_utc == 16: 
        run_job("Indie 💡", "games", {'genres': 'indie'})
    elif current_hour_utc == 20: 
        run_job("Popular 🔥", "games", {'ordering': '-rating'})
    else:
        print(">>> Non-scheduled time (Manual Run). Running 'Popular' job for testing.")
        run_job("Popular (Test) 🔥", "games", {'ordering': '-rating'})

    print("==========================================")
    print("... Games job finished.")

if __name__ == "__main__":
    main()

