import streamlit as st
import os
from pypdf import PdfReader
from google import genai

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="CV Analyze AI",page_icon="🔥" )

# Coba ambil dari Environment Variable (Server)
# Kalau gak ada (di localhost), baru error atau minta input manual
if "GOOGLE_API_KEY" in st.secrets:
    MY_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    # Fallback aman: Minta user input sendiri di sidebar kalau key server gak ketemu
    MY_API_KEY = st.sidebar.text_input("Masukkan Google API Key:", type="password")
    if not MY_API_KEY:
        st.warning("Masukkan API Key dulu di sidebar!")
        st.stop()

# Fungsi Inisialisasi Client (Bukan cuma model)
def get_client():
    return genai.Client(api_key=MY_API_KEY)

# --- UI VISUAL ---
st.title("🔥 CV Analyze")
st.markdown("Upload CV kamu")

# 1. SIDEBAR: UPLOAD PDF
with st.sidebar:
    st.header("1. Upload Dokumen")
    uploaded_file = st.file_uploader("Pilih file PDF", type=["pdf"])
    
    # Tombol Reset
    if st.button("Hapus Chat"):
        st.session_state.messages = []
        st.rerun()

# 2. PROSES FILE (Hanya jika ada file diupload)
if uploaded_file:
    # Baca PDF langsung dari memori (tanpa save ke disk)
    try:
        reader = PdfReader(uploaded_file)
        text_content = ""
        for page in reader.pages:
            text_content += page.extract_text() + "\n"
        
        # Simpan teks CV ke session state biar gak hilang saat reload
        st.session_state.cv_text = text_content
        st.success(f"✅ CV Terbaca! ({len(text_content)} karakter)")
    except Exception as e:
        st.error(f"Gagal baca file: {e}")

# 3. CHAT INTERFACE
# Inisialisasi history chat jika belum ada
if "messages" not in st.session_state:
    st.session_state.messages = []

# Tampilkan chat yang sudah ada di layar
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. INPUT USER & LOGIKA AI
if prompt := st.chat_input("Tanya sesuatu tentang CV ini..."):
    
    # Cek apakah CV sudah diupload
    if "cv_text" not in st.session_state:
        st.error("Upload CV dulu woy!")
    else:
        # A. Tampilkan pesan user
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # B. Pikirkan Jawaban AI
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("🤖 *Sedang menilaimu...*")
            
            try:
                # Siapkan Prompt Raksasa
                full_prompt = f"""
                Kamu adalah HR Manager Galak.
                Data CV User: {st.session_state.cv_text}
                
                Pertanyaan User: {prompt}
                
                Jawab dengan pedas, singkat, dan berdasarkan data CV di atas.
                """
                
               # Panggil Google
                client = get_client() # Ambil client utuh
                response = client.models.generate_content( # Panggil dari client
                    model="gemini-flash-latest",
                    contents=full_prompt
                )
                
                # Tampilkan hasil
                reply = response.text
                message_placeholder.markdown(reply)
                
                # Simpan ke history
                st.session_state.messages.append({"role": "assistant", "content": reply})
                
            except Exception as e:
                message_placeholder.error(f"Error: {e}")
