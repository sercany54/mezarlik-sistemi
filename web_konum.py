import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
from datetime import datetime
from PIL import Image
import time
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Nokta Atışı GPS Mezarlık Sistemi", layout="wide", page_icon="🪦")

DOSYA_ADI = "mezarlik_konum_veritabani.xlsx"
FOTO_KLASORU = "mezar_fotograflari"

if not os.path.exists(FOTO_KLASORU):
    os.makedirs(FOTO_KLASORU)

def verileri_yukle():
    if os.path.exists(DOSYA_ADI):
        return pd.read_excel(DOSYA_ADI)
    return pd.DataFrame(columns=["İndeks", "Vefat Eden", "Mezar_Adasi", "Sira_No", "Mezar_No", "Olum_Tarihi", "Yakin_Iletisim", "Notlar", "Enlem", "Boylam", "Foto_Yolu"])

def verileri_kaydet(df):
    df.to_excel(DOSYA_ADI, index=False)

if "df" not in st.session_state:
    st.session_state.df = verileri_yukle()
if "harita_merkez" not in st.session_state:
    st.session_state.harita_merkez = [40.7628, 30.3894] # Sakarya Emirdağ Mezarlığı
if "zoom_seviyesi" not in st.session_state:
    st.session_state.zoom_seviyesi = 16
if "rota_hedef" not in st.session_state:
    st.session_state.rota_hedef = None
if "harita_key" not in st.session_state:
    st.session_state.harita_key = str(time.time())
if "user_location" not in st.session_state:
    st.session_state.user_location = None

# İnternet sunucusunda çalışırken cihazın GPS koordinatını çeken güvenli sistem
device_loc = streamlit_js_eval(data_of='navigator.geolocation.getCurrentPosition', wrapper='(p) => {return {lat: p.coords.latitude, lng: p.coords.longitude};}', key='gps_device')

st.title("🪦 Nokta Atışı GPS Navigasyonlu Mezarlık Sistemi")

sekme1, sekme2, sekme3 = st.tabs(["🗺️ Canlı Harita & Rota", "✍️ Tekli Mezar Kaydı", "🤖 Otomatik Konum Motoru (Grid)"])

# SEKME 3: OTOMATİK KONUM MOTORU
with sekme3:
    st.subheader("🤖 Ada/Sıra Numarasına Göre Otomatik Konumlandır")
    secilen_ada = st.text_input("📍 Konumlandırılacak Ada İsmi:", placeholder="Örn: Ada 4")
    ref_enlem = st.number_input("Ada Başlangıç Enlemi:", format="%.6f", value=float(st.session_state.harita_merkez[0]), key="ref_lat")
    ref_boylam = st.number_input("Ada Başlangıç Boylamı:", format="%.6f", value=float(st.session_state.harita_merkez[1]), key="ref_lng")
    
    if st.button("⚡ Bu Adadaki Tüm Mezarları Otomatik Konumlandır", type="primary", use_container_width=True):
        if not secilen_ada.strip():
            st.error("Lütfen bir ada ismi girin!")
        elif st.session_state.df.empty:
            st.error("Veritabanında kayıt yok!")
        else:
            METRE_TO_DEG_LAT = 1 / 111111.0
            METRE_TO_DEG_LNG = 1 / (111111.0 * 0.75) 
            MEZAR_GENISLIK = 1.2  
            MEZAR_UZUNLUK = 2.2   
            SIRA_ARASI_BOSLUK = 1.0 
            
            sayac = 0
            for idx, row in st.session_state.df.iterrows():
                if str(row["Mezar_Adasi"]).strip().lower() == secilen_ada.strip().lower():
                    try: sira, no = int(row["Sira_No"]), int(row["Mezar_No"])
                    except: continue 
                    
                    y_ekseni_kayma = (sira - 1) * (MEZAR_UZUNLUK + SIRA_ARASI_BOSLUK) * METRE_TO_DEG_LAT
                    x_ekseni_kayma = (no - 1) * MEZAR_GENISLIK * METRE_TO_DEG_LNG
                    
                    st.session_state.df.at[idx, "Enlem"] = ref_enlem - y_ekseni_kayma
                    st.session_state.df.at[idx, "Boylam"] = ref_boylam + x_ekseni_kayma
                    sayac += 1
            
            verileri_kaydet(st.session_state.df)
            st.session_state.harita_key = str(time.time())
            st.success(f"🚀 Mezarlar başarıyla yerleştirildi!")
            st.rerun()

# SEKME 2: TEKLİ MEZAR KAYDI
with sekme2:
    st.subheader("📝 Tekli Mezar Kaydı Oluştur")
    vefat_eden = st.text_input("👤 Vefat Edenin Adı Soyadı:")
    m_adasi = st.text_input("🔢 Mezar Adası (Örn: Ada 4):")
    sira_no = st.number_input("🔢 Sıra No:", min_value=1, value=1)
    mezar_no = st.number_input("🔢 Mezar No:", min_value=1, value=1)
    olum_tarihi = st.date_input("📅 Ölüm Tarihi:", value=datetime.now())
    yakin_iletisim = st.text_input("📞 Yakın İletişim:")
    notlar = st.text_area("ℹ️ Notlar:")
    yuklenen_foto = st.file_uploader("📸 Fotoğraf Yükle:", type=["png", "jpg", "jpeg"])
    
    if st.button("💾 Kaydet", type="primary", use_container_width=True):
        if not vefat_eden.strip(): st.error("Ad soyad giriniz!")
        else:
            foto_yolu = ""
            if yuklenen_foto is not None:
                foto_adi = f"{vefat_eden}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                foto_yolu = os.path.join(FOTO_KLASORU, foto_adi)
                Image.open(yuklenen_foto).convert("RGB").save(foto_yolu, "JPEG")
            
            yeni_satir = pd.DataFrame([{
                "İndeks": len(st.session_state.df)+1, "Vefat Eden": vefat_eden, "Mezar_Adasi": m_adasi,
                "Sira_No": sira_no, "Mezar_No": mezar_no, "Olum_Tarihi": olum_tarihi.strftime('%Y-%m-%d'),
                "Yakin_Iletisim": yakin_iletisim, "Notlar": notlar, "Enlem": st.session_state.harita_merkez[0],
                "Boylam": st.session_state.harita_merkez[1], "Foto_Yolu": foto_yolu
            }])
            st.session_state.df = pd.concat([st.session_state.df, yeni_satir], ignore_index=True)
            verileri_kaydet(st.session_state.df)
            st.session_state.harita_key = str(time.time())
            st.success("Kaydedildi!")
            st.rerun()

# SEKME 1: HARİTA VE ARAMA
with sekme1:
    arama_kelimesi = st.text_input("🔎 Vefat Eden İsmi veya Ada Ara:")
    filtreli_df = st.session_state.df
    if arama_kelimesi:
        filtreli_df = st.session_state.df[
            st.session_state.df["Vefat Eden"].str.contains(arama_kelimesi, case=False, na=False) |
            st.session_state.df["Mezar_Adasi"].str.contains(arama_kelimesi, case=False, na=False)
        ]

    if not filtreli_df.empty and arama_kelimesi:
        for idx, row in filtreli_df.iterrows():
            with st.expander(f"🪦 {row['Vefat Eden']} ({row['Mezar_Adasi']} - Sıra: {row['Sira_No']} No: {row['Mezar_No']})"):
                f_yolu = row['Foto_Yolu']
                if isinstance(f_yolu, str) and f_yolu.strip() and os.path.exists(f_yolu): 
                    st.image(f_yolu, use_container_width=True)
                
                c1, c2 = st.columns(2)
                if c1.button("📍 Git (Mezara Odaklan)", key=f"git_{idx}", use_container_width=True):
                    st.session_state.harita_merkez = [float(row['Enlem']), float(row['Boylam'])]
                    st.session_state.zoom_seviyesi = 20
                    st.session_state.harita_key = str(time.time())
                    st.rerun()
                    
                if c2.button("🚗 Mevcut Konumdan Doğrudan Rota Çiz", key=f"rota_{idx}", use_container_width=True):
                    if device_loc and 'lat' in device_loc:
                        st.session_state.user_location = [device_loc['lat'], device_loc['lng']]
                        st.session_state.rota_hedef = [float(row['Enlem']), float(row['Boylam'])]
                        st.session_state.harita_merkez = [(device_loc['lat'] + float(row['Enlem'])) / 2, (device_loc['lng'] + float(row['Boylam'])) / 2]
                        st.session_state.zoom_seviyesi = 18
                        st.session_state.harita_key = str(time.time())
                        st.rerun()
                    else:
                        st.error("Cihazınızın GPS konumuna ulaşılamadı. Lütfen konum izinlerinizi kontrol edin!")

    if st.session_state.rota_hedef:
        st.success("🎯 Navigasyon Aktif: Bulunduğunuz konumdan mezara giden rota başarıyla haritaya eklendi.")
        if st.button("❌ Rotayı Kapat ve Temizle", use_container_width=True): 
            st.session_state.rota_hedef = None
            st.session_state.user_location = None
            st.session_state.harita_key = str(time.time())
            st.rerun()

    m = folium.Map(location=st.session_state.harita_merkez, zoom_start=st.session_state.zoom_seviyesi)
    folium.TileLayer(tiles='https://google.com{x}&y={y}&z={z}', attr='Google', name='Google Uydu').add_to(m)

    if st.session_state.user_location and st.session_state.rota_hedef:
        folium.Marker(location=st.session_state.user_location, popup="Siz", icon=folium.Icon(color="blue", icon="user")).add_to(m)
        folium.PolyLine(locations=[st.session_state.user_location, st.session_state.rota_hedef], color="red", weight=6).add_to(m)

    for _, row in st.session_state.df.dropna(subset=['Enlem', 'Boylam']).iterrows():
        popup_txt = f"<b>{row['Vefat Eden']}</b><br>{row['Mezar_Adasi']}<br>Sıra: {row['Sira_No']} No: {row['Mezar_No']}"
        folium.Marker(location=[float(row["Enlem"]), float(row["Boylam"])], popup=folium.Popup(popup_txt, max_width=200), icon=folium.Icon(color="green")).add_to(m)

    m.add_child(folium.LatLngPopup())
    harita_verisi = st_folium(m, width="100%", height=550, key=st.session_state.harita_key)
    
    if harita_verisi and harita_verisi.get("last_clicked") and not st.session_state.rota_hedef:
        st.session_state.harita_merkez = [harita_verisi["last_clicked"]["lat"], harita_verisi["last_clicked"]["lng"]]
        st.session_state.zoom_seviyesi = harita_verisi.get("zoom", 19)
        st.rerun()
