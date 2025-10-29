# =============================================================================
#           *** بوت نشر الألعاب - الإصدار 3.0 ***
#
#  (يتصل بـ RAWG.io وينشر لعبة عشوائية)
#  (يستخدم "تصميم الرسالتين" الناجح الذي اكتشفته)
#  (لا يوجد Gemini)
# =============================================================================

import requests
import os
import sys
import random
import datetime

# --- [1] الإعدادات والمفاتيح السرية ---
try:
    GAMES_API_KEY = os.environ['GAMES_API_KEY']
    BOT_TOKEN = os.environ['BOT_TOKEN']
    CHANNEL_USERNAME = os.environ['CHANNEL_USERNAME'] # يجب أن يبدأ بـ @
except KeyError as e:
    print(f"!!! خطأ: متغير البيئة الأساسي غير موجود: {e}")
    sys.exit(1)

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
RAWG_BASE_URL = 'https://api.rawg.io/api'

# --- [2] الدوال المساعدة (التي أصلحناها معاً) ---

def post_text_to_telegram(text_content):
    """(آمنة) إرسال رسالة نصية (للشرح الطويل)"""
    print(f"... جاري إرسال (النص الكامل) إلى {CHANNEL_USERNAME} ...")
    url = f"{TELEGRAM_API_URL}/sendMessage"
    
    if len(text_content) > 4096:
        text_content = text_content[:4093] + "..."
        
    payload = { 'chat_id': CHANNEL_USERNAME, 'text': text_content, 'parse_mode': 'Markdown' }
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        print(">>> تم إرسال (النص الكامل) بنجاح!")
    except requests.exceptions.RequestException as e:
        print(f"!!! فشل إرسال (النص الكامل): {e}")

def post_photo_to_telegram(image_url, caption):
    """(آمنة) تحميل وإرسال صورة (للصور)"""
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
        print(f"!!! فشل إرسال (الصورة): {e}")
        return False

# --- [3] المهمة الرئيسية (جلب لعبة) ---
def run_games_job():
    print("--- بدء مهمة [جلب لعبة اليوم] ---")
    try:
        # 1. إيجاد لعبة جيدة (من آخر سنتين، تقييم عالٍ)
        print("... البحث عن لعبة جيدة ...")
        today = datetime.datetime.now()
        last_year = today.year - 2
        dates = f"{last_year}-01-01,{today.year}-{today.month:02d}-{today.day:02d}"
        random_page = random.randint(1, 5) # لاختيار عشوائي

        list_url = f"{RAWG_BASE_URL}/games?key={GAMES_API_KEY}&dates={dates}&ordering=-metacritic&page_size=40&page={random_page}"
        
        response = requests.get(list_url)
        response.raise_for_status()
        list_data = response.json()
        
        if not list_data.get('results'):
            print("... لم يتم العثور على ألعاب في القائمة.")
            return

        random_game_summary = random.choice(list_data['results'])
        game_id = random_game_summary['id']
        
        # 2. جلب التفاصيل الكاملة للعبة
        print(f"... تم اختيار اللعبة (ID: {game_id}). جاري جلب التفاصيل الكاملة ...")
        details_url = f"{RAWG_BASE_URL}/games/{game_id}?key={GAMES_API_KEY}"
        response = requests.get(details_url)
        response.raise_for_status()
        data = response.json()

        title = data.get('name', 'N/A')
        description = data.get('description_raw', 'No description available.')
        image_url = data.get('background_image')
        rating = data.get('rating', 'N/A')
        metacritic = data.get('metacritic', 'N/A')
        released = data.get('released', 'N/A')
        platforms = ", ".join([p['platform']['name'] for p in data.get('platforms', [])])

        if not image_url:
            print("... اللعبة لا تحتوي على صورة. سيتم التخطي.")
            return

        # 3. إرسال الرسالتين (فكرتك الناجحة)
        short_caption = (
            f"🎮 **{title}**\n\n"
            f"⭐ **التقييم:** {rating} / 5\n"
            f"🔥 **Metacritic:** {metacritic}\n"
            f"📅 **تاريخ الإصدار:** {released}"
        )
        
        full_text = (
            f"**{title}**\n\n"
            f"**الأجهزة:** {platforms}\n\n"
            f"**الوصف:**\n{description[:1500]}...\n\n" # اقتطاع الوصف الطويل
            f"---\n*تابعنا للمزيد من {CHANNEL_USERNAME}*"
        )

        success = post_photo_to_telegram(image_url, short_caption)
        if success:
            post_text_to_telegram(full_text)
        
    except Exception as e:
        print(f"!!! فشلت مهمة الألعاب: {e}")

# --- [4] التشغيل ---
def main():
    print("==========================================")
    print(f"بدء تشغيل مهمة (v3.0 - بوت الألعاب)...")
    print("==========================================")
    run_games_job()
    print("==========================================")
    print("... انتهت مهمة الألعاب.")

if __name__ == "__main__":
    main()
