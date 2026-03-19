import streamlit as st
import requests
import pandas as pd
import time
import random

# Sayfa ayarları
st.set_page_config(page_title="Film Dedektifi v2", page_icon="🍿", layout="wide")

# Estetik bir CSS dokunuşu (Kartların daha şık görünmesi için)
st.markdown("""
    <style>
    .stSuccess { background-color: #1e2a3a; border-left: 5px solid #ffcc00; }
    .stHeader { color: #ffcc00; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎬 Sinema Salonunuza Hoş Geldiniz")
st.caption("Listeniz taranıyor, mısırları hazırlayın...")

api_key = "f57e54dbfb985cb1733c8299b78b2a5e"

def platform_bul(film_adi, yil):
    search_url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={film_adi}&primary_release_year={yil}"
    try:
        res = requests.get(search_url).json()
        if res['results']:
            movie_id = res['results'][0]['id']
            p_url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers?api_key={api_key}"
            p_res = requests.get(p_url).json()
            if 'TR' in p_res['results'] and 'flatrate' in p_res['results']['TR']:
                return [p['provider_name'] for p in p_res['results']['TR']['flatrate']]
    except:
        return []
    return []

# Sol Panel
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2503/2503508.png", width=100)
st.sidebar.header("Film Arşivi Yükle")
yuklenen_dosya = st.sidebar.file_uploader("Letterboxd CSV", type=["csv"])

if yuklenen_dosya is not None:
    liste_verisi = pd.read_csv(yuklenen_dosya)
    
    if st.button("🎞️ Makarayı Başlat ve Platformları Bul"):
        sepetler = {} 
        yok_listesi = []
        
        # İlerleme çubuğu (Progress Bar) ekleyelim
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        sinema_simgeleri = ["🎬", "🎥", "🍿", "🎞️", "🎟️", "🎭"]

        for index, satir in liste_verisi.iterrows():
            f_adi = satir.get('Name') or satir.get('Title')
            f_yil = satir.get('Year')
            
            # İlerleme yüzdesi
            yuzde = (index + 1) / len(liste_verisi)
            progress_bar.progress(yuzde)
            status_text.text(f"{random.choice(sinema_simgeleri)} Sorgulanıyor: {f_adi}")
            
            platformlar = platform_bul(f_adi, f_yil)
            
            if platformlar:
                for p in platformlar:
                    if p not in sepetler: sepetler[p] = []
                    sepetler[p].append(f"{f_adi} ({f_yil})")
            else:
                yok_listesi.append(f"{f_adi} ({f_yil})")
            
            time.sleep(0.05)

        status_text.success("✨ Tüm makaralar tarandı!")
        
        # --- SONUÇLAR ---
        col1, col2 = st.columns(2)
        with col1:
            st.header("📺 Hemen İzle")
            for platform, filmler in sepetler.items():
                with st.expander(f"📌 {platform} ({len(filmler)} Film)"):
                    for f in filmler:
                        st.write(f"🍿 {f}")

        with col2:
            st.header("⏳ Yakında Gelebilir")
            with st.expander(f"Platformda Olmayanlar ({len(yok_listesi)})"):
                for f in yok_listesi:
                    st.write(f"🎞️ {f}")