import time
from google import genai

# --- TEMPEL API KEY ---
MY_API_KEY = "AIzaSyB3WlSK3mvLUU4g7r3QvE3kZK8ECbaeHZM" 

def start_chat():
    try:
        # Kita pakai alias 'gemini-1.5-flash'
        MODEL_NAME = "gemini-1.5-flash"
        
        print(f"🤖 Menghubungkan ke {MODEL_NAME} dengan mode ANTI-CRASH...")
        client = genai.Client(api_key=MY_API_KEY)

        # PERBAIKAN DI SINI: Pakai Dictionary, bukan types.GenerateContentConfig
        # Ini lebih aman dan tidak butuh import aneh-aneh.
        chat = client.chats.create(
            model=MODEL_NAME,
            config={
                "system_instruction": "Kamu asisten karir yang sarkas. Jawab singkat."
            }
        )

        print("✅ TERHUBUNG! (Ketik 'keluar' untuk stop)")
        print("-" * 30)

        while True:
            user_input = input("\nKamu: ")
            if user_input.lower() in ["keluar", "exit"]:
                print("👋 Bye.")
                break
            
            # --- RETRY LOGIC (JURUS SABAR) ---
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = chat.send_message(user_input)
                    print(f"AI: {response.text}")
                    break # Berhasil? Keluar loop
                
                except Exception as e:
                    error_msg = str(e)
                    # Deteksi error kuota (429) atau server (503)
                    if "429" in error_msg or "503" in error_msg:
                        wait_time = (attempt + 1) * 5
                        print(f"⚠️ Google ngambek (Limit). Menunggu {wait_time} detik...")
                        time.sleep(wait_time)
                    else:
                        print(f"❌ Error Fatal: {e}")
                        # Jika error fatal, biasanya karena model 404. Kita break biar gak looping.
                        return

    except Exception as e:
        print(f"❌ Gagal Inisialisasi: {e}")

if __name__ == "__main__":
    start_chat()