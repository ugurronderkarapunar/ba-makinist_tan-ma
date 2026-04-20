import streamlit as st
import fitz  # PyMuPDF
import re

# 1. Gemi Adamı Yeterlilik Hiyerarşisi (Makine Sınıfı)
# Puan ne kadar yüksekse yeterlilik o kadar üst seviyededir.
HIYERARSI = {
    "Başmakinist": 10,
    "Uzakyol Başmakinist": 11,
    "İkinci Makinist": 8,
    "Uzakyol İkinci Makinist": 9,
    "Makinist": 6,
    "Uzakyol Vardiya Makinisti": 7,
    "Sınırlı Başmakinist": 5,
    "Sınırlı Makinist": 4,
    "Yağcı": 2,
    "Silici": 1
}

def yeterlilik_analizi(text):
    bulunanlar = []
    for unvan in HIYERARSI.keys():
        # Metin içinde büyük/küçük harf duyarsız arama yapar
        if re.search(unvan, text, re.IGNORECASE):
            bulunanlar.append(unvan)
    
    if not bulunanlar:
        return None, None

    # Bulunanlar içinden puanı en yüksek olanı seç
    en_yuksek = max(bulunanlar, key=lambda x: HIYERARSI[x])
    return en_yuksek, HIYERARSI[en_yuksek]

# --- Streamlit Arayüzü ---
st.set_page_config(page_title="Gemi Adamı Cüzdan Analizi", layout="centered")

st.title("🚢 Gemi Adamı Cüzdan Analiz Sistemi")
st.write("PDF cüzdanı yükleyin, sistem en yüksek yeterliliği otomatik tespit etsin.")

uploaded_file = st.file_uploader("Cüzdan PDF'ini Yükleyin", type="pdf")

if uploaded_file is not None:
    with st.spinner('Dosya işleniyor...'):
        # PDF'i oku
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        
        # Analiz et
        sonuc, puan = yeterlilik_analizi(full_text)
        
        if sonuc:
            st.success(f"### Tespit Edilen En Yüksek Yeterlilik: **{sonuc}**")
            st.info(f"Sistem Hiyerarşi Puanı: {puan}")
            
            # Detaylı metin görmek istersen (Debug için)
            with st.expander("PDF İçeriğini Görüntüle"):
                st.text(full_text)
        else:
            st.warning("PDF içerisinde geçerli bir yeterlilik unvanı bulunamadı.")
