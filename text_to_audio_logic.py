from TTS.api import TTS
import os
import sqlite3
from tkinter import messagebox

# إعدادات النموذج الصوتي
COQUI_MODEL = "tts_models/en/ljspeech/tacotron2-DDC_ph"
DEFAULT_SPEAKER = "LJ Speech"

def convert_text_to_blob(text):
    """تحويل النص إلى كائن صوتي باستخدام Coqui TTS"""
    try:
        # تنظيف النص من الرموز غير المرغوبة
        text_clean = text.replace('**', ' ').replace('*', ' ').replace('_', ' ').replace('-', ' ')
        
        # تهيئة محرك Coqui TTS
        tts = TTS(model_name=COQUI_MODEL, progress_bar=False)
        
        # إنشاء ملف صوتي مؤقت
        temp_file = "temp_coqui_audio.wav"
        tts.tts_to_file(text=text_clean, file_path=temp_file, speaker=DEFAULT_SPEAKER)
        
        # قراءة الملف كـ binary blob
        with open(temp_file, "rb") as audio_file:
            audio_blob = audio_file.read()
        
        return audio_blob
    
    except Exception as e:
        raise Exception(f"فشل في توليد الصوت: {str(e)}")
    
    finally:
        # حذف الملف المؤقت
        if os.path.exists(temp_file):
            os.remove(temp_file)

def process_data(db_path, source_table, source_column, destination_table, destination_column, progress_bar, master_window):
    """معالجة البيانات وحفظها في قاعدة البيانات"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT id, {source_column} FROM {source_table}")
        rows = cursor.fetchall()

        progress_bar["maximum"] = len(rows)
        progress_bar["value"] = 0

        for row in rows:
            item_id, text_to_convert = row
            try:
                cursor.execute(f"SELECT {destination_column} FROM {destination_table} WHERE id = ?", (item_id,))
                result = cursor.fetchone()

                if result and result[0] is not None:
                    print(f"تم تخطي الصف (ID: {item_id}) لأن العمود الصوتي يحتوي على بيانات.")
                    progress_bar["value"] += 1
                    master_window.update_idletasks()
                    continue

                audio_blob = convert_text_to_blob(text_to_convert)
                cursor.execute(f"UPDATE {destination_table} SET {destination_column} = ? WHERE id = ?", 
                             (audio_blob, item_id))
                conn.commit()
                progress_bar["value"] += 1
                master_window.update_idletasks()
                print(f"تم تحويل النص (ID: {item_id}) وحفظه في {destination_table}.{destination_column}.")
                
            except Exception as e:
                print(f"فشل تحويل النص (ID: {item_id}): {e}")

        messagebox.showinfo("اكتمل", "تمت معالجة جميع البيانات بنجاح.")
        conn.close()

    except sqlite3.Error as e:
        messagebox.showerror("خطأ في قاعدة البيانات", f"خطأ SQLite: {e}")
    except Exception as e:
        messagebox.showerror("خطأ عام", f"خطأ غير متوقع: {e}")