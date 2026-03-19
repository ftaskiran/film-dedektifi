import streamlit as st
import requests
import pandas as pd
import time
import random

# Sayfa Ayarları
st.set_page_config(page_title="MovieSherlock", page_icon="🕵️‍♂️", layout="wide")

# Gereksiz sistem uyarılarını gizle
import warnings
warnings.filterwarnings("ignore")

api_key = "f57e54dbfb985cb1733c8299b78b2a5e"

def film_detay_getir(film_adi, yil):
    search_url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={film_adi}&primary_release_year={yil}"
    try:
        res = requests.get(search_url).json()
        if res.get('results'):
            film = res['results'][0]
            m_id = film['id']
            poster = f"https://image.tmdb.org/t/p/w500{film.get('poster_path')}" if film.get('poster_path') else None
            
            # Platform Sorgusu
            p_url = f"https://api.themoviedb.org/3/movie/{m_id}/watch/providers?api_key={api_key}"
            p_res = requests.get(p_url).json()
            
            platformlar = []
            if 'TR' in p_res.get('results', {}) and 'flatrate' in p_res['results']['TR']:
                platformlar = [p['provider_name'] for p in p_res['results']['TR']['flatrate']]
            
            return platformlar, poster
    except Exception as e:
        return [], None
    return [], None

# --- ARAYÜZ ---
st.title("🕵️‍♂️ MovieSherlock")
st.caption("Kayıp filmlerin izini sürer.")

st.sidebar.header("Arşivi Yükle")
yuklenen_dosya = st.sidebar.file_uploader("Letterboxd CSV", type=["csv"])

if yuklenen_dosya is not None:
    liste_verisi = pd.read_csv(yuklenen_dosya)
    
    if st.button("🔎 İzini Sür "):
        sepetler = {}
        yok_listesi = []
        
        # --- İLERLEME KISMI (İstediğin Bölüm) ---
        progress_bar = st.progress(0)
        durum_yazisi = st.empty()
        ikonlar = ["🔍", "🕵️‍♂️", "🎞️", "🍿", "📽️"]

        for index, satir in liste_verisi.iterrows():
            f_adi = satir.get('Name') or satir.get('Title')
            f_yil = satir.get('Year')
            
            # İlerleme güncelleme
            yuzde = (index + 1) / len(liste_verisi)
            progress_bar.progress(yuzde)
            durum_yazisi.text(f"{random.choice(ikonlar)} Araştırılıyor: {f_adi} ({f_yil})")
            
            platformlar, poster = film_detay_getir(f_adi, f_yil)
            
            if platformlar:
                for p in platformlar:
                    if p not in sepetler: sepetler[p] = []
                    sepetler[p].append({"ad": f_adi, "yil": f_yil, "poster": poster})
            else:
                yok_listesi.append({"ad": f_adi, "yil": f_yil})
            
            time.sleep(0.2) # API'yi yormamak için kısa mola

        durum_yazisi.success("✨ Sherlock başardı!")

        # --- SONUÇLAR (POSTERLİ VE GRUPLU) ---
        if sepetler:
            for platform, filmler in sepetler.items():
                st.divider()
                st.header(f"📺 {platform} Üzerinden İzlenebilir")
                
                # Yan yana 4 poster dizimi
                cols = st.columns(4)
                for i, film in enumerate(filmler):
                    with cols[i % 4]:
                        if film['poster']:
                            st.image(film['poster'], use_container_width=True)
                        st.markdown(f"**{film['ad']}**")
                        st.caption(f"Yıl: {film['yil']}")
        
        # Platformda olmayanlar (Kısa Liste)
        if yok_listesi:
            with st.expander("🎞️ Şu An Platformlarda Bulunmayanlar"):
                for f in yok_listesi:
                    st.write(f"⚪ {f['ad']} ({f['yil']})")
