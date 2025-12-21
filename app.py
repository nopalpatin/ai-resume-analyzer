import streamlit as st
import os
from pypdf import PdfReader
from google import genai
import json
import plotly.express as px
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

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
            message_placeholder.markdown("🤖 *Sedang memindai kompetensi...*")
            
            try:
                # 1. PROMPT ENGINEERING KHUSUS JSON
                full_prompt = f"""
                Kamu adalah HR Analytics System yang sadis tapi akurat.
                
                Tugasmu:
                1. Analisis CV berikut: {st.session_state.cv_text}
                2. Jawab pertanyaan user: "{prompt}"
                3. BERIKAN SKOR (0-100) untuk 5 kategori ini:
                   - Relevansi Skill (Apakah skill cocok dengan job market?)
                   - Pengalaman (Kualitas pengalaman kerja/magang)
                   - Pendidikan (Relevansi background studi)
                   - Kerapian (Format CV dan tata bahasa)
                   - "Selling Point" (Seberapa menarik kandidat ini?)
                
                FORMAT OUTPUT WAJIB JSON (Tanpa markdown ```json, murni text):
                {{
                    "jawaban_text": "Jawaban verbal pedasmu di sini...",
                    "skor": {{
                        "Skill": 80,
                        "Experience": 40,
                        "Education": 90,
                        "Formatting": 20,
                        "Selling_Point": 50
                    }}
                }}
                """
                
                # 2. PANGGIL GEMINI
                client = get_client() 
                response = client.models.generate_content(
                    model="gemini-flash-latest",
                    contents=full_prompt
                )
                
                # 3. PARSING HASIL (STRING -> JSON)
                raw_text = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(raw_text)
                
                # 4. TAMPILKAN TEKS JAWABAN
                reply_text = data["jawaban_text"]
                message_placeholder.markdown(reply_text)
                
                # 5. TAMPILKAN GRAFIK (RADAR CHART)
                scores = data["skor"]
                df = pd.DataFrame(dict(
                    r=list(scores.values()),
                    theta=list(scores.keys())
                ))
                
                fig = px.line_polar(df, r='r', theta='theta', line_close=True)
                fig.update_traces(fill='toself')
                fig.update_layout(title="Peta Kelemahan Karirmu")
                
                # ... (Kode grafik plotly selesai di sini) ...
                st.plotly_chart(fig, use_container_width=True)

                # --- FITUR DATABASE: SIMPAN HASIL KE GOOGLE SHEETS ---
                try:
                    # 1. Hitung Total Skor (Rata-rata)
                    total_score = sum(scores.values()) / len(scores)
                    
                    # 2. Siapkan Data Baris Baru
                    new_data = pd.DataFrame([{
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Total_Score": total_score,
                        "Skill_Score": scores.get("Skill", 0),
                        "Experience_Score": scores.get("Experience", 0),
                        "Education_Score": scores.get("Education", 0),
                        "Recommendation": data["jawaban_text"][:100] + "..." # Ambil 100 huruf awal aja biar gak penuh
                    }])

                    # 3. Koneksi ke Google Sheets
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    
                    # 4. Baca Data Lama
                    existing_data = conn.read(worksheet="Sheet1", usecols=list(range(6)), ttl=5)
                    
                    # 5. Gabung Data (Lama + Baru)
                    updated_df = pd.concat([existing_data, new_data], ignore_index=True)
                    
                    # 6. Update Google Sheets
                    conn.update(worksheet="Sheet1", data=updated_df)
                    
                    st.toast("✅ Data Analysis tersimpan ke Database!", icon="💾")
                    
                except Exception as e:
                    st.warning(f"Gagal simpan database: {e}")
                
                # Simpan ke history (Note: Grafik tidak tersimpan di history chat standar, hanya teks)
                st.session_state.messages.append({"role": "assistant", "content": reply_text})
                
            except json.JSONDecodeError:
                st.error("AI gagal generate grafik. Mencoba mode teks biasa...")
                st.markdown(response.text)
                
            except Exception as e:
                message_placeholder.error(f"Error: {e}")