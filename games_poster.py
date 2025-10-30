# =============================================================================
#           *** بوت COSMOS للألعاب - الإصدار 1.0 ***
#
#  (يتصل بـ RAWG.io API)
#  (يستخدم MyMemory للترجمة)
#  (يستخدم "تصميم الرسالتين" الآمن)
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
    CHANNEL_USERNAME = os.environ['CHANNEL_USERNAME'] # يجب أن يبدأ بـ @
except KeyError as e:
    print(f"!!! خطأ: متغير البيئة الأساسي غير موجود: {e}")
    sys.exit(1)

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
RAWG_BASE_URL = "https://api.rawg.io/api"

# --- [2] الدوال المساعدة (الترجمة + النشر) ---
# (هذه الدوال هي نفسها التي نجحت 100% في "مشروع ناسا")

def clean_text(text):
    if not text: return ""
    clean_text = re.sub(r'<[^>]+>', '', text)
    clean_text = re.sub(r'https?://[^\s\n\r]+', '', clean_text)
    clean_text = re.sub(r'www\.[^\s\n\r]+', '', clean_text)
    return clean_text.strip()

def translate_text(text_to_translate):
    if not text_to_translate: return ""
    print(f"... بدء الترجمة (MyMemory) لـ '{text_to_translate[:50]}...'")
    try:
        url = "https://api.mymemory.translated.net/get"
        params = {"q": text_to_translate, "langpair": "en|ar"}
        response = requests.get(url, params=params, timeout=120)
        response.raise_for_status(); data = response.json()
        if data['responseStatus'] == 200:
            translation = data['responseData']['translatedText']
            translation = translation.replace("MYMEMORY WARNING: YOU USED ALL AVAILABLE FREE TRANSLATIONS FOR TODAY. NEXT AVAILABLE IN", "")
            print("...الترجمة تمت بنجاح.")
            return translation.strip()
        else:
            print(f"!!! فشلت ترجمة MyMemory (السبب: {data['responseDetails']}).")
            return text_to_translate
    except Exception as e:
        print(f"!!! فشلت الترجمة (السبب: {e}). سيتم استخدام النص الإنجليزي.")
        return text_to_translate

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
    """
    يجلب التفاصيل الكاملة (مثل الوصف) للعبة معينة
    """
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
    """
    الدالة الرئيسية لجلب قائمة الألعاب بناءً على "المهمة"
    """
    try:
        default_params = {
            'key': GAMES_API_KEY,
            'page_size': 10, # نجلب 10 ونختار 1 عشوائياً
            'metacritic__gt': 60 # فلتر للجودة (أعلى من 60)
        }
        all_params = {**default_params, **params}
        
        url = f"{RAWG_BASE_URL}/{endpoint}"
        response = requests.get(url, params=all_params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        if data.get('results'):
            # اختر لعبة عشوائية من النتائج العشر
            game = random.choice(data['results'])
            return game.get('id')
        else:
            print(f"... لم يتم العثور على نتائج لـ {endpoint} بالمعايير {params}")
            return None
    
    except Exception as e:
        print(f"!!! فشل جلب قائمة الألعاب: {e}")
        return None

def format_platforms(platforms_list):
    """
    تنسيق قائمة المنصات (مثل تطبيقك HTML)
    """
    if not platforms_list: return "غير معروف"
    # (PC, PlayStation, Xbox, Nintendo, iOS, Android, macOS, Linux)
    # (نأخذ الأسماء الرئيسية فقط)
    main_platforms = [p['platform']['name'] for p in platforms_list]
    return ", ".join(main_platforms)
    
def format_developers(developers_list):
    """
    تنسيق قائمة المطورين
    """
    if not developers_list: return "غير معروف"
    return ", ".join([d['name'] for d in developers_list])

# --- [4] دوال "المهام" (الخطة المتنوعة) ---

def run_job(job_name, endpoint, params={}):
    """
    الدالة الموحدة لتشغيل أي مهمة
    """
    print(f"--- بدء مهمة [{job_name}] ---")
    
    # 1. جلب لعبة عشوائية من القائمة
    game_id = get_game_list(endpoint, params)
    if not game_id:
        print(f"!!! فشلت مهمة [{job_name}] - لم يتم العثور على لعبة.")
        return

    # 2. جلب التفاصيل الكاملة لهذه اللعبة
    details = get_game_details(game_id)
    if not details:
        print(f"!!! فشلت مهمة [{job_name}] - لم يتم العثور على تفاصيل اللعبة.")
        return

    # 3. استخراج البيانات (مثل تطبيقك HTML)
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

    # 4. الترجمة (باستخدام MyMemory)
    title_ar = translate_text(title_en)
    description_ar = translate_text(description_en_clean)
    platforms_ar_label = translate_text("Platforms:")
    developers_ar_label = translate_text("Developers:")
    platforms_ar = translate_text(platforms_en)
    developers_ar = translate_text(developers_en)

    # 5. إرسال "الرسالتين" (فكرتك الناجحة)
    
    # الرسالة 1: الصورة + العنوان
    metacritic_tag = f"⭐️ {metacritic}" if metacritic else ""
    short_caption = f"🎮 **{title_ar}**\n\n*({released})* {metacritic_tag}"
    
    # الرسالة 2: التفاصيل الكاملة
    full_text = (
        f"**{title_ar}**\n\n"
        f"{description_ar}\n\n"
        f"---\n"
        f"**{platforms_ar_label}** {platforms_ar}\n"
        f"**{developers_ar_label}** {developers_ar}\n\n"
        f"*تابعنا للمزيد من {CHANNEL_USERNAME}*"
    )
    
    if post_photo_to_telegram(image_url, short_caption):
        post_text_to_telegram(full_text)

# --- [5] التشغيل الرئيسي (الذكي) ---
def main():
    print("==========================================")
    print(f"بدء تشغيل (v1.0 - بوت الألعاب)...")
    
    # (توقيت بغداد: 3ص, 7ص, 11ص, 3ظ, 7م, 11م)
    current_hour_utc = datetime.datetime.now(datetime.timezone.utc).hour
    print(f"الساعة الحالية (UTC): {current_hour_utc}")
    
    today = datetime.date.today()
    last_30_days = today - datetime.timedelta(days=30)
    
    # تنسيق التواريخ
    today_str = today.strftime('%Y-%m-%d')
    last_30_days_str = last_30_days.strftime('%Y-%m-%d')

    # هذا هو "الراوتر" الذي يختار المهمة بناءً على الوقت (خطة النشر)
    if current_hour_utc == 0: # 3:00 صباحاً (بغداد)
        run_job("إصدار جديد 🚀", "games", {'dates': f"{last_30_days_str},{today_str}", 'ordering': '-added'})
        
    elif current_hour_utc == 4: # 7:00 صباحاً (بغداد)
        run_job("الأعلى تقييماً ⭐️", "games", {'ordering': '-metacritic'})
        
    elif current_hour_utc == 8: # 11:00 صباحاً (بغداد)
        run_job("ألعاب أكشن 💥", "games", {'genres': 'action'})
        
    elif current_hour_utc == 12: # 3:00 ظهراً (بغداد)
        run_job("ألعاب RPG 📜", "games", {'genres': 'role-playing-games-rpg'})
        
    elif current_hour_utc == 16: # 7:00 مساءً (بغداد)
        run_job("ألعاب مستقلة 💡", "games", {'genres': 'indie'})
        
    elif current_hour_utc == 20: # 11:00 مساءً (بغداد)
        run_job("الأكثر شعبية 🔥", "games", {'ordering': '-rating'})
        
    else:
        # هذا للتشغيل اليدوي (workflow_dispatch)
        print(">>> وقت غير مجدول (تشغيل يدوي). سيتم اختيار مهمة 'الأكثر شعبية' للاختبار.")
        run_job("الأكثر شعبية (اختبار) 🔥", "games", {'ordering': '-rating'})

    print("==========================================")
    print("... انتهت مهمة الألعاب.")

if __name__ == "__main__":
    main()

