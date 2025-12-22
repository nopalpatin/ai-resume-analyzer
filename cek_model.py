from google import genai
import streamlit as st
import os

# Masukkan API KEY langsung di sini sebentar cuma buat ngecek (JANGAN DI-COMMIT)
api_key = "AIzaSyDWR5BpZIXK7lD2_MFVTrlLytnmnOVxbAQ" # Copy dari secrets.toml kamu

client = genai.Client(api_key=api_key)
print("=== DAFTAR MODEL YANG TERSEDIA ===")
for m in client.models.list(config={"page_size": 100}):
    print(m.name)