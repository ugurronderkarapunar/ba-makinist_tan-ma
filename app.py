import streamlit as st
from supabase import create_client
from datetime import datetime, date
import pandas as pd
import io
import base64

# ------------------------------
# Sayfa yapılandırması
st.set_page_config(
    page_title="Lojistik Takip",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------
# Supabase bağlantısı (secrets.toml kullan)
@st.cache_resource
def init_supabase():
    url = st.secrets["supabase_url"]
    key = st.secrets["supabase_key"]
    return create_client(url, key)

supabase = init_supabase()

# ------------------------------
# Oturum yönetimi
if "user" not in st.session_state:
    st.session_state.user = None

# ------------------------------
# Yardımcı fonksiyonlar
def get_profile(user_id):
    res = supabase.table("profiles").select("*").eq("id", user_id).execute()
    return res.data[0] if res.data else None

def get_shipment_count(user_id):
    res = supabase.table("shipments").select("id", count="exact").eq("user_id", user_id).execute()
    return res.count

def can_create_shipment(user_id):
    profile = get_profile(user_id)
    if profile["subscription_status"] == "pro":
        return True
    count = get_shipment_count(user_id)
    return count < 5  # free plan max 5

# ------------------------------
# Giriş/Kayıt sayfaları
def login_tab():
    st.subheader("🔐 Giriş Yap")
    email = st.text_input("E-posta", key="login_email")
    password = st.text_input("Şifre", type="password", key="login_password")
    if st.button("Giriş", type="primary", use_container_width=True):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.user = res.user
            st.success("Hoş geldiniz!")
            st.rerun()
        except Exception as e:
            st.error(f"Giriş hatası: {e}")

def register_tab():
    st.subheader("📝 Kayıt Ol")
    email = st.text_input("E-posta", key="reg_email")
    password = st.text_input("Şifre (min 6 karakter)", type="password", key="reg_password")
    if st.button("Kayıt Ol", type="primary", use_container_width=True):
        try:
            res = supabase.auth.sign_up({"email": email, "password": password})
            if res.user:
                # Profil oluştur
                supabase.table("profiles").insert({
                    "id": res.user.id,
                    "email": email,
                    "subscription_status": "free"
                }).execute()
                st.success("Kayıt başarılı! Şimdi giriş yapabilirsiniz.")
            else:
                st.warning("Kayıt başarısız, e-posta doğrulama gerekebilir.")
        except Exception as e:
            st.error(f"Kayıt hatası: {e}")

# ------------------------------
# Dashboard
def show_dashboard():
    user = st.session_state.user
    profile = get_profile(user.id)
    is_pro = profile["subscription_status"] == "pro"
    shipment_count = get_shipment_count(user.id)
    remaining = "Sınırsız" if is_pro else f"{5 - shipment_count}"

    # Sidebar bilgileri
    with st.sidebar:
        st.image("https://placehold.co/400x100?text=LojistikTakip", use_container_width=True)
        st.markdown(f"### 👤 {user.email}")
        st.markdown(f"**Plan:** {'🚀 Pro' if is_pro else '✨ Ücretsiz'}")
        st.markdown(f"**Kalan gönderi hakkı:** {remaining}")
        if not is_pro:
            if st.button("⭐ Pro'ya Geç", use_container_width=True):
                st.switch_page("pages/subscribe.py")  # opsiyonel sayfa
        st.divider()
        if st.button("🚪 Çıkış Yap", use_container_width=True):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    # Ana içerik
    st.title("📦 Gönderi Paneli")
    
    # Yeni gönderi butonu
    col1, col2 = st.columns([4,1])
    with col2:
        if st.button("➕ Yeni Gönderi", use_container_width=True, type="primary"):
            st.session_state.show_new_form = True
    
    # Yeni gönderi formu
    if st.session_state.get("show_new_form", False):
        with st.form("new_shipment_form", clear_on_submit=True):
            st.subheader("Yeni Gönderi Bilgileri")
            tracking = st.text_input("Takip No *")
            col_a, col_b = st.columns(2)
            with col_a:
                origin = st.text_input("Çıkış Yeri *")
            with col_b:
                destination = st.text_input("Varış Yeri *")
            deadline = st.date_input("Teslim Tarihi *", min_value=date.today())
            status = st.selectbox("Durum", ["beklemede", "yolda", "teslim edildi"])
            notes = st.text_area("Notlar")
            
            submitted = st.form_submit_button("💾 Kaydet")
            if submitted:
                if not tracking or not origin or not destination:
                    st.error("Lütfen tüm zorunlu alanları doldurun.")
                else:
                    try:
                        supabase.table("shipments").insert({
                            "user_id": user.id,
                            "tracking_number": tracking,
                            "origin": origin,
                            "destination": destination,
                            "deadline": deadline.isoformat(),
                            "status": status,
                            "notes": notes
                        }).execute()
                        st.success("Gönderi eklendi!")
                        st.session_state.show_new_form = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Hata: {e}")
    
    # Gönderi listesi
    shipments = supabase.table("shipments")\
        .select("*")\
        .eq("user_id", user.id)\
        .order("deadline", desc=False)\
        .execute()
    
    if not shipments.data:
        st.info("Henüz hiç gönderi eklenmemiş. Yukarıdaki butonla başlayın.")
        return
    
    # Tablo görünümü
    df = pd.DataFrame(shipments.data)
    df["deadline"] = pd.to_datetime(df["deadline"]).dt.date
    df["days_left"] = (df["deadline"] - date.today()).dt.days
    
    # Renklendirme için fonksiyon
    def highlight_deadline(val):
        if val < 0:
            return "color: red; font-weight: bold"
        elif val <= 2:
            return "color: orange"
        return ""
    
    st.dataframe(
        df[["tracking_number", "origin", "destination", "deadline", "status", "days_left"]],
        column_config={
            "tracking_number": "Takip No",
            "origin": "Nereden",
            "destination": "Nereye",
            "deadline": "Teslim Tarihi",
            "status": "Durum",
            "days_left": st.column_config.NumberColumn("Kalan Gün", format="%d")
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Detaylı kartlar
    st.subheader("📄 Gönderi Detayları")
    for ship in shipments.data:
        with st.expander(f"🚚 {ship['tracking_number']} - {ship['origin']} → {ship['destination']}"):
            col1, col2 = st.columns([2,1])
            with col1:
                st.markdown(f"**Teslim:** {ship['deadline']}")
                st.markdown(f"**Durum:** {ship['status']}")
                st.markdown(f"**Notlar:** {ship.get('notes', '-')}")
            with col2:
                # PDF yükleme
                st.markdown("#### Evraklar")
                # Mevcut evrakları listele
                docs = supabase.table("documents").select("*").eq("shipment_id", ship["id"]).execute()
                for doc in docs.data:
                    st.markdown(f"📎 [{doc['file_name']}]({doc['file_url']})")
                # Yeni PDF yükle
                uploaded = st.file_uploader("PDF Ekle", type=["pdf"], key=f"upload_{ship['id']}")
                if uploaded:
                    file_bytes = uploaded.getvalue()
                    file_name = uploaded.name
                    # Supabase Storage'a yükle
                    bucket = "documents"
                    file_path = f"{ship['id']}/{datetime.now().timestamp()}_{file_name}"
                    supabase.storage.from_(bucket).upload(file_path, file_bytes)
                    public_url = supabase.storage.from_(bucket).get_public_url(file_path)
                    supabase.table("documents").insert({
                        "shipment_id": ship["id"],
                        "file_url": public_url,
                        "file_name": file_name
                    }).execute()
                    st.success("PDF yüklendi!")
                    st.rerun()
                
                # Silme butonu
                if st.button("🗑️ Gönderiyi Sil", key=f"del_{ship['id']}"):
                    supabase.table("shipments").delete().eq("id", ship["id"]).execute()
                    st.success("Silindi.")
                    st.rerun()

# ------------------------------
# Abonelik sayfası (isteğe bağlı, ayrı dosya)
def show_subscribe():
    st.title("⭐ Pro Plana Geç")
    st.markdown("**Aylık ₺199** ile sınırsız gönderi ve e-posta hatırlatmalar.")
    if st.button("Abone Ol (Stripe)"):
        # Stripe checkout entegrasyonu için yönlendirme
        # Detaylı entegrasyon için st_paywall veya manuel checkout linki
        st.info("Ödeme sayfasına yönlendiriliyorsunuz...")
        # Buraya stripe checkout linki gelecek

# ------------------------------
# Ana yönlendirme
def main():
    if st.session_state.user is None:
        st.title("📦 Lojistik Takip Sistemi")
        st.caption("Gönderilerinizi, evraklarınızı ve teslim tarihlerini tek yerden yönetin.")
        tab1, tab2 = st.tabs(["Giriş", "Kayıt Ol"])
        with tab1:
            login_tab()
        with tab2:
            register_tab()
    else:
        show_dashboard()

if __name__ == "__main__":
    main()
