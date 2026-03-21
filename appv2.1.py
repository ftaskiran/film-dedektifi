import streamlit as st
import requests
import pandas as pd
import time
import random
import warnings

# Gereksiz sistem uyarılarını gizle
warnings.filterwarnings("ignore")

# Sayfa Ayarları
st.set_page_config(page_title="MovieSherlock", page_icon="🕵️‍♂️", layout="wide")

api_key = "f57e54dbfb985cb1733c8299b78b2a5e"

def film_detay_getir(sorgu, yil=None):
    try:
        # --- ADIM 1: TMDB ID'SİNİ BUL ---
        m_id = None
        poster_path = None
        film_adi_gercek = sorgu # Arayüzde göstermek için

        # Eğer sorgu bir IMDb ID ise (tt ile başlıyorsa)
        if str(sorgu).strip().lower().startswith("tt"):
            find_url = f"https://api.themoviedb.org/3/find/{sorgu}?api_key={api_key}&external_source=imdb_id"
            res = requests.get(find_url).json()
            if res.get('movie_results'):
                film = res['movie_results'][0]
                m_id = film['id']
                poster_path = film.get('poster_path')
                film_adi_gercek = film.get('title')
        
        # Eğer normal metin araması ise
        else:
            search_url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={sorgu}&primary_release_year={yil}"
            res = requests.get(search_url).json()
            if res.get('results'):
                film = res['results'][0]
                m_id = film['id']
                poster_path = film.get('poster_path')
                film_adi_gercek = film.get('title')

        # --- ADIM 2: PLATFORM VE POSTER BİLGİSİNİ AL ---
        if m_id:
            poster = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
            p_url = f"https://api.themoviedb.org/3/movie/{m_id}/watch/providers?api_key={api_key}"
            p_res = requests.get(p_url).json()
            
            platformlar = []
            if 'TR' in p_res.get('results', {}) and 'flatrate' in p_res['results']['TR']:
                platformlar = [p['provider_name'] for p in p_res['results']['TR']['flatrate']]
            
            return platformlar, poster, film_adi_gercek
            
    except Exception as e:
        return [], None, sorgu
        
    return [], None, sorgu

# --- ARAYÜZ ---
st.title("🕵️‍♂️ MovieSherlock")
st.caption("Kayıp filmlerin izini sürer, IMDb ID'lerini bile tanır.")

# --- MANUEL ARAMA ALANI ---
st.subheader("🔍 Tekli Film Sorgula")
col1, col2 = st.columns([3, 1])

with col1:
    manuel_film = st.text_input("Film Adı veya IMDb ID Giriniz", placeholder="Örn: Inception veya tt15239678")
with col2:
    manuel_yil = st.text_input("Yıl (Opsiyonel)", placeholder="2010")

if st.button("🕵️‍♂️ Sherlock'a Sor"):
    if manuel_film:
        with st.spinner('Sherlock büyütecini hazırlıyor...'):
            platformlar, poster, gercek_ad = film_detay_getir(manuel_film, manuel_yil)
            
            if platformlar:
                st.success(f"Buldum! **{gercek_ad}** şu platformlarda var:")
                c1, c2 = st.columns([1, 3])
                with c1:
                    if poster: st.image(poster, use_container_width=True)
                with c2:
                    for p in platformlar:
                        st.write(f"✅ {p}")
            else:
                st.warning(f"Maalesef **{gercek_ad}** şu an Türkiye'deki ana platformlarda görünmüyor.")
    else:
        st.error("Lütfen bir film adı veya ID yazın.")

st.divider()

# --- LİSTE YÜKLEME KISMI ---
# --- SOL MENÜ (SIDEBAR) ---
st.sidebar.header("📽️ Arşivi Yükle")

# 1. Rehber Notu (Kullanıcıya yardımcı olması için)
with st.sidebar.expander("❓ Liste Nasıl İndirilir?"):
    st.info("""
    **Letterboxd:**
    Settings > Import & Export > Export Data yolunu izleyin.
    
    **IMDb:**
    Watchlist sayfanıza gidin, listenin en altındaki 'Export' butonuna basın.
    """)

# 2. Kaynak Seçimi ve Dosya Yükleyici
kaynak_secimi = st.sidebar.selectbox("Liste Kaynağı Seçin", ["Letterboxd", "IMDb Watchlist"])
yuklenen_dosya = st.sidebar.file_uploader(f"{kaynak_secimi} CSV Dosyası", type=["csv"])

if yuklenen_dosya is not None:
    # IMDb ve Letterboxd dosyaları bazen farklı karakter formatlarında olabilir
    try:
        liste_verisi = pd.read_csv(yuklenen_dosya)
    except:
        liste_verisi = pd.read_csv(yuklenen_dosya, encoding='latin-1')
    
    if st.sidebar.button("🔎 İzini Sür "):
        sepetler = {}
        yok_listesi = []
        
        # İlerleme Çubuğu Hazırlığı
        progress_bar = st.progress(0)
        durum_yazisi = st.empty()
        ikonlar = ["🔍", "🕵️‍♂️", "🎞️", "🍿", "📽️"]

        for index, satir in liste_verisi.iterrows():
            # Kaynağa göre veri ayıklama
            if kaynak_secimi == "Letterboxd":
                f_sorgu = satir.get('Name') or satir.get('Title')
                f_yil = satir.get('Year')
                ekran_adi = f_sorgu
            else: # IMDb Watchlist
                # IMDb'de ID 'Const' sütunundadır, isim ise 'Title'
                f_sorgu = satir.get('Const') # tt... kodunu yakalar
                f_yil = satir.get('Year')
                ekran_adi = satir.get('Title')

            # İlerleme güncelleme
            yuzde = (index + 1) / len(liste_verisi)
            progress_bar.progress(yuzde)
            durum_yazisi.text(f"{random.choice(ikonlar)} Araştırılıyor: {ekran_adi}")
            
            # Fonksiyon artık 3 değer döndürüyor (Platformlar, Poster, Gerçek Ad)
            platformlar, poster, gercek_ad = film_detay_getir(f_sorgu, f_yil)
            
            if platformlar:
                for p in platformlar:
                    if p not in sepetler: sepetler[p] = []
                    sepetler[p].append({"ad": gercek_ad, "yil": f_yil, "poster": poster})
            else:
                yok_listesi.append({"ad": gercek_ad, "yil": f_yil})
            
            time.sleep(0.1) # ID araması daha hızlı olduğu için süreyi biraz kıstık

        durum_yazisi.success(f"✨ Sherlock {kaynak_secimi} listesini tamamladı!")

        # --- SONUÇLAR (ANA EKRANDA GÖRÜNECEK) ---
        if sepetler:
            for platform, filmler in sepetler.items():
                st.divider()
                st.header(f"📺 {platform}")
                cols = st.columns(5) 
                for i, film in enumerate(filmler):
                    with cols[i % 5]:
                        if film['poster']:
                            st.image(film['poster'], use_container_width=True)
                        st.markdown(f"**{film['ad']}**")
                        st.caption(f"{film['yil']}")
        
        if yok_listesi:
            with st.expander("🎞️ Şu An Platformlarda Bulunmayanlar"):
                for f in yok_listesi:
                    st.write(f"⚪ {f['ad']} ({f['yil']})")

# --- FOOTER ---
st.divider()
st.caption("🎬 *This product uses the TMDB API but is not endorsed or certified by TMDB.*")
