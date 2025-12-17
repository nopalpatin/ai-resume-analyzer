import os
import time
from pypdf import PdfReader
from google import genai

# --- TEMPEL API KEY (JANGAN SAMPAI SALAH) ---
MY_API_KEY = "AIzaSyB3WlSK3mvLUU4g7r3QvE3kZK8ECbaeHZM" 

def clean_text(text):
    # Fungsi sederhana untuk membersihkan spasi berlebih
    # Mengubah double space menjadi single space
    return " ".join(text.split())

def main():
    print("🚀 MENYIAPKAN CAREER COACH AI...")
    
    # 1. BACA PDF
    nama_file = "cv_saya.pdf"
    if not os.path.exists(nama_file):
        print(f"❌ File '{nama_file}' mana? Copas dulu ke folder ini!")
        return

    try:
        reader = PdfReader(nama_file)
        raw_text = ""
        for page in reader.pages:
            raw_text += page.extract_text() + "\n"
        
        # Preprocessing Data (Penting!)
        clean_cv = clean_text(raw_text)
        print(f"✅ CV Terbaca ({len(clean_cv)} karakter). Memulai Sesi Chat...")
        
    except Exception as e:
        print(f"❌ Gagal baca PDF: {e}")
        return

    # 2. INISIALISASI AI
    try:
        # Gunakan model yang terbukti jalan di akunmu
        MODEL_NAME = "gemini-flash-latest" 
        
        client = genai.Client(api_key=MY_API_KEY)

        # SYSTEM INSTRUCTION: Kita jejalkan CV di sini supaya dia ingat terus
        system_prompt = f"""
        Kamu adalah Career Coach AI yang profesional tapi tegas.
        Kamu memegang data CV user ini:
        
        --- DATA CV MULAI ---
        {clean_cv}
        --- DATA CV SELESAI ---
        
        Tugasmu: Menjawab pertanyaan user seputar karir berdasarkan data CV di atas.
        Jika CV-nya jelek, jujur saja. Jangan sugar coating.
        """

        chat = client.chats.create(
            model=MODEL_NAME,
            config={
                "system_instruction": system_prompt
            }
        )

        print("-" * 40)
        print("🤖 COACH SIAP! (Tanya apapun soal CV-mu. Ketik 'exit' untuk udahan)")
        print("-" * 40)

        # 3. CHAT LOOP
        while True:
            user_input = input("\nKamu: ")
            if user_input.lower() in ["keluar", "exit", "quit"]:
                print("👋 Sukses terus bro. Perbaiki CV-nya!")
                break
            
            # Retry Logic (Anti-Crash)
            for attempt in range(3):
                try:
                    response = chat.send_message(user_input)
                    print(f"Coach: {response.text}")
                    break
                except Exception as e:
                    if "429" in str(e) or "503" in str(e):
                        print("⚠️ Server sibuk, bentar...")
                        time.sleep(5)
                    else:
                        print(f"❌ Error: {e}")
                        return

    except Exception as e:
        print(f"❌ Gagal Connect Google: {e}")

if __name__ == "__main__":
    main()