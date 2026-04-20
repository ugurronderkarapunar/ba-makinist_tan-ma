import streamlit as st
import fitz  # PyMuPDF
import re

# 1. Senin verdiğin listeye göre unvan hiyerarşisi (Puanı yüksek olan en kıdemlidir)
# Bu liste, cüzdanda yazabilecek anahtar kelimeleri kapsar.
UNVAN_HIYERARSI = {
    "Çarkçıbaşı": 100,
    "Başmakinist": 100,
    "Chief Engineer": 100,
    "2. Çarkçı": 80,
    "2. Makinist": 80,
    "Second Engineer": 80,
    "3. Çarkçı": 60,
    "3. Makinist": 60,
    "Third Engineer": 60,
    "4. Çarkçı": 40,
    "4. Makinist": 40,
    "Fourth Engineer": 40,
    "Elektrik Zabiti": 50, # Genelde 3. veya 4. çarkçı seviyesinde değerlendirilir
    "Elektrik Çarkçısı": 50,
    "Makine Lostromosu": 30,
    "Motorman": 30,
    "Yağcı": 20,
    "Oiler": 20,
    "Silici": 10,
    "Wiper": 10
}

def analiz_et(metin):
    tespit_edilenler = []
    
    # Metni temizle ve unvanları ara
    for unvan, puan in UNVAN_HIYERARSI.items():
        # Regex ile tam kelime araması yapalım (Case insensitive)
        if re.search(r'\b' + re.escape(unvan) + r'\b', metin, re.IGNORECASE):
            tespit_edilenler.append((unvan, puan))
    
    if not tespit_edilenler:
        return None
    
    # Puanı en yüksek olanı seç (Kıdemli olan)
    en_yuksek = max(tespit_edilenler, key=lambda x: x[1])
    return en_yuksek

# --- Streamlit Arayüzü ---
st.set_page_config(page_title="Makine Personeli Analiz", page_icon="⚙️")

st.title("🚢 Çarkçı Yeterlilik Analiz Sistemi")
st.markdown("""
Bu uygulama, yüklenen PDF cüzdanlarındaki unvanları tarar ve personel arasındaki **en yüksek yeterliliği** belirler.
""")

dosya = st.file_uploader("Personel Cüzdanı (PDF)", type="pdf")

if dosya:
    try:
        with st.spinner('Cüzdan taranıyor...'):
            # PDF Okuma
            doc = fitz.open(stream=dosya.read(), filetype="pdf")
            tam_metin = ""
            for sayfa in doc:
                tam_metin += sayfa.get_text()
            
            # Analiz
            sonuc = analiz_et(tam_metin)
            
            if sonuc:
                unvan_adi, puan = sonuc
                st.balloons()
                st.success(f"### Tespit Edilen En Üst Unvan: **{unvan_adi}**")
                
                # Görsel bir hiyerarşi barı
                st.progress(puan / 100)
                st.caption(f"Hiyerarşi Seviyesi: {puan}/100")
            else:
                st.error("Üzgünüm, PDF içerisinde tanımlı bir unvan (Çarkçı, Yağcı vb.) bulunamadı.")
                
            with st.expander("PDF'den Çıkarılan Ham Metni Gör"):
                st.text(tam_metin)
                
    except Exception as e:
        st.error(f"Bir hata oluştu: {e}")

# --- Footer ---
st.divider()
st.info("Not: Bu sistem anahtar kelime eşleşmesi ile çalışır. El yazısı olan belgelerde OCR (Tesseract) gerekebilir.")
