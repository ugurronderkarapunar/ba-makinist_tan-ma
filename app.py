import streamlit as st
import fitz  # PyMuPDF
import re

# 1. Genişletilmiş ve Güncellenmiş Unvan Hiyerarşisi
# Belgedeki tam karşılıkları ve puanları (Yüksek puan = Üst kıdem)
UNVAN_HIYERARSI = {
    "Uzakyol Başmakinist": 110,
    "Başmakinist": 100,
    "Çarkçıbaşı": 100,
    "Chief Engineer": 100,
    "Uzakyol İkinci Makinist": 90,
    "İkinci Makinist": 85,
    "2. Makinist": 80,
    "3. Makinist": 60,
    "4. Makinist": 40,
    "Sınırlı Başmakinist": 35,  # Belgedeki unvan 
    "Restricted Chief Engineer": 35,
    "Sınırlı Makinist": 30,
    "Makine Lostromosu": 25,
    "Yağcı": 15,
    "Oiler": 15,
    "Silici": 5
}

def unvan_tespit_et(text):
    # Metni temizle ve satırları birleştir
    temiz_metin = " ".join(text.split()).upper()
    bulunan_unvanlar = []

    for unvan, puan in UNVAN_HIYERARSI.items():
        # Unvanı büyük harfe çevirip metin içinde arıyoruz
        if unvan.upper() in temiz_metin:
            bulunan_unvanlar.append((unvan, puan))
    
    if not bulunan_unvanlar:
        return None

    # Puanı en yüksek olanı döndür
    return max(bulunan_unvanlar, key=lambda x: x[1])

# --- Streamlit Arayüzü ---
st.set_page_config(page_title="Gemi Adamı Belge Analizi", page_icon="⚓")

st.title("⚓ Gemi Adamı Cüzdan Okuyucu")
st.write("PDF belgesini yükleyin, en yüksek yeterlilik derecesini belirleyelim.")

yuklenen_dosya = st.file_uploader("Cüzdan PDF", type="pdf")

if yuklenen_dosya:
    with st.spinner('Belge analiz ediliyor...'):
        doc = fitz.open(stream=yuklenen_dosya.read(), filetype="pdf")
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        
        # Eğer PyMuPDF metni hiç göremezse alternatif bir uyarı verelim
        if not full_text.strip():
            st.error("⚠️ PDF metni okunamadı. Bu dosya bir fotoğraf/tarama olabilir. OCR desteği gerekebilir.")
        else:
            sonuc = unvan_tespit_et(full_text)
            
            if sonuc:
                unvan, puan = sonuc
                st.success(f"### Tespit Edilen En Yüksek Yeterlilik: **{unvan}**")
                st.progress(puan / 110)
            else:
                st.warning("Tanımlı bir unvan bulunamadı. Lütfen unvan listesini kontrol edin.")

            with st.expander("Okunan Metin Detayı"):
                st.write(full_text)
