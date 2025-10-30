# =============================================================================
#           *** بوت COSMOS للألعاب - الإصدار 1.2 ***
#
#  (هذا كود اختبار بسيط جداً للتأكد من أن تيليجرام يعمل)
# =============================================================================

import requests
import os
import sys

# --- [1] الإعدادات والمفاتيح السرية ---
try:
    BOT_TOKEN = os.environ['BOT_TOKEN']
    CHANNEL_USERNAME = os.environ['CHANNEL_USERNAME'] 
except KeyError as e:
    print(f"!!! خطأ: متغير البيئة الأساسي غير موجود: {e}")
    print("!!! يرجى التأكد من إضافة BOT_TOKEN و CHANNEL_USERNAME إلى GitHub Secrets في 'هذا المستودع الجديد'")
    sys.exit(1) # (إيقاف التشغيل بفشل)

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# --- [2] دالة إرسال النص ---
def post_text_to_telegram(text_content):
    print(f"... جاري إرسال (رسالة الاختبار) إلى {CHANNEL_USERNAME} ...")
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = { 'chat_id': CHANNEL_USERNAME, 'text': text_content, 'parse_mode': 'Markdown' }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status() # (سيطبع خطأ إذا فشل)
        print(">>> 🎉🎉🎉 تم إرسال (رسالة الاختبار) بنجاح! 🎉🎉🎉")
    except requests.exceptions.RequestException as e:
        print(f"!!! فشل إرسال (رسالة الاختبار): {e}")
        # (طباعة رد تيليجرام لنرى الخطأ 400 أو 404)
        print(f"!!! تفاصيل الخطأ من تيليجرام: {getattr(response, 'text', 'لا يوجد رد')}")
        sys.exit(1) # (إيقاف التشغيل بفشل)

# --- [3] التشغيل الرئيسي ---
def main():
    print("==========================================")
    print(f"بدء تشغيل (v1.2 - اختبار تيليجرام)...")
    
    test_message = (
        f"**اختبار (بوت الألعاب v1.2)** 🎮\n\n"
        f"إذا رأيت هذه الرسالة، فهذا يعني أن `BOT_TOKEN` و `CHANNEL_USERNAME` في هذا المستودع **صحيحة 100%**."
    )
    
    post_text_to_telegram(test_message)
    
    print("... انتهت مهمة الاختبار.")
    print("==========================================")

if __name__ == "__main__":
    main()
