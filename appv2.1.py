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

# Senin API Key'in
api_key = "f57e54dbfb985cb1733c8299b78b2a5e"

# --- YARDIMCI FONKSİYONLAR ---

def get_poster_only(tmdb_id):
    """Kürasyon köşesi için TMDB'den sadece poster çeker"""
    try:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={api_key}&language=tr-TR"
        res = requests.get(url).json()
        if res.get('poster_path'):
            return f"https://image.tmdb.org/t/p/w500{res['poster_path']}"
    except:
        return None
    return None

def film_detay_getir(sorgu, yil=None):
    try:
        m_id = None
        poster_path = None
        film_adi_gercek = sorgu 

        if str(sorgu).strip().lower().startswith("tt"):
            find_url = f"https://api.themoviedb.org/3/find/{sorgu}?api_key={api_key}&external_source=imdb_id"
            res = requests.get(find_url).json()
            if res.get('movie_results'):
                film = res['movie_results'][0]
                m_id = film['id']
                poster_path = film.get('poster_path')
                film_adi_gercek = film.get('title')
        else:
            search_url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={sorgu}&primary_release_year={yil}"
            res = requests.get(search_url).json()
            if res.get('results'):
                film = res['results'][0]
                m_id = film['id']
                poster_path = film.get('poster_path')
                film_adi_gercek = film.get('title')

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

# --- ARAYÜZ BAŞLIĞI ---
st.title("🕵️‍♂️ MovieSherlock")
st.caption("Kayıp filmlerin izini sürer, IMDb ID'lerini de tanır.")

# --- MANUEL ARAMA ALANI (EN ÜSTTE) ---
st.subheader("🔍 Hızlı Sorgu")
col1, col2 = st.columns([3, 1])

with col1:
    manuel_film = st.text_input("Film Adı veya IMDb ID Giriniz", placeholder="Örn: Inception veya tt15239678")
with col2:
    manuel_yil = st.text_input("Yıl (Opsiyonel)", placeholder="2010")

if st.button("🕵️‍♂️ Sherlock'a Sor"):
    if manuel_film:
        with st.spinner('Sherlock araştırıyor...'):
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

# --- LİSTE YÜKLEME SONUÇLARI BURAYA GELECEK ---
# (Sidebar'dan yüklenen listelerin sonuçları bu alanda görünür)

# --- SOL MENÜ (SIDEBAR) ---
st.sidebar.header("📽️ Arşivi Yükle")

with st.sidebar.expander("❓ Liste Nasıl İndirilir?"):
    st.info("""
    **Letterboxd:**
    Settings > Import & Export > Export Data yolunu izleyin.
    
    **IMDb:**
    Watchlist sayfanıza gidin, listenin en altındaki 'Export' butonuna basın.
    """)

kaynak_secimi = st.sidebar.selectbox("Liste Kaynağı Seçin", ["Letterboxd", "IMDb"])
yuklenen_dosya = st.sidebar.file_uploader(f"{kaynak_secimi} CSV Dosyası", type=["csv"])

if yuklenen_dosya is not None:
    try:
        liste_verisi = pd.read_csv(yuklenen_dosya)
    except:
        liste_verisi = pd.read_csv(yuklenen_dosya, encoding='latin-1')
    
    if st.sidebar.button("🔎 İzini Sür "):
        sepetler = {}
        yok_listesi = []
        progress_bar = st.progress(0)
        durum_yazisi = st.empty()

        for index, satir in liste_verisi.iterrows():
            if kaynak_secimi == "Letterboxd":
                f_sorgu = satir.get('Name') or satir.get('Title')
                f_yil = satir.get('Year')
                ekran_adi = f_sorgu
            else:
                f_sorgu = satir.get('Const')
                f_yil = satir.get('Year')
                ekran_adi = satir.get('Title')

            yuzde = (index + 1) / len(liste_verisi)
            progress_bar.progress(yuzde)
            durum_yazisi.text(f"🔍 Araştırılıyor: {ekran_adi}")
            
            platformlar, poster, gercek_ad = film_detay_getir(f_sorgu, f_yil)
            
            if platformlar:
                for p in platformlar:
                    if p not in sepetler: sepetler[p] = []
                    sepetler[p].append({"ad": gercek_ad, "yil": f_yil, "poster": poster})
            else:
                yok_listesi.append({"ad": gercek_ad, "yil": f_yil})
            
            time.sleep(0.1)

        durum_yazisi.success(f"✨ Liste tamamlandı!")

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

# --- MANUEL ARAMA BİTİŞİNDEN HEMEN SONRA ---
st.divider()

# Sidebar'ın en altına şık bir X butonu
with st.sidebar:
    st.divider() # Üstteki menü elemanlarından ince bir çizgiyle ayırır
    st.markdown(
        """
        <div style="display: flex; flex-direction: column; align-items: center; margin-top: 10px;">
            <p style="font-size: 0.85rem; color: #808080; margin-bottom: 8px; font-family: sans-serif;">
                Sherlock'u X'te Takip Et
            </p>
            <a href="https://x.com/MovieSherlockHQ" target="_blank" style="text-decoration: none;">
                <div style="
                    background-color: #000000; 
                    color: #ffffff; 
                    padding: 8px 20px; 
                    border-radius: 25px; 
                    font-weight: bold; 
                    font-family: sans-serif;
                    display: flex; 
                    align-items: center; 
                    gap: 10px;
                    border: 1px solid #444;
                ">
                    <span style="font-size: 1.2rem;">𝕏</span> 
                    <span>@MovieSherlock</span>
                </div>
            </a>
        </div>
        """, 
        unsafe_allow_html=True
    )

# --- BANA FİLM ÖNER (RANDOMIZER) ---
# Senin 'Altın Liste'ndeki 12 film ve TMDB ID'leri
film_havuzu = [
    {"ad": "Nocturnal Animals", "id": "340666"},
    {"ad": "Atomic Blonde", "id": "341013"},
    {"ad": "Manchester By The Sea", "id": "334541"},
    {"ad": "Loving Vincent", "id": "339877"},
    {"ad": "Burning", "id": "491584"},
    {"ad": "Decision to Leave", "id": "705996"},
    {"ad": "Constantine", "id": "561"},
    {"ad": "Lovers of the Arctic Circle", "id": "1414"},
    {"ad": "The Devil All The Time", "id": "499932"},
    {"ad": "Uncut Gems", "id": "473033"},
    {"ad": "I'm Thinking of Ending Things", "id": "500840"},
    {"ad": "La La Land", "id": "313369"}
]

# Arayüzdeki kutu tasarımı
with st.expander(" Karar Veremedin mi? Sherlock'a Sor", expanded=True):
    st.write("Sherlock favorilerinden rastgele seçsin.")
    
    if st.button("Bana Film Öner"):
        secilen_film = random.choice(film_havuzu)
        
        # Sherlock araştırıyor animasyonu
        with st.spinner('Sherlock arşivde iz sürüyor...'):
            oneri_poster = get_poster_only(secilen_film['id'])
            
            st.markdown(f"### 🔍 Önerim: **{secilen_film['ad']}**")
            
            if oneri_poster:
                # Posteri biraz daha kibar (küçük) gösterelim ki çok yer kaplamasın
                st.image(oneri_poster, width=250)
            
            st.success("Bu film tam sana göre görünüyor!")

st.divider()
# --- KÜRASYON KÖŞESİ (SİSLİ TEPELER) BURADAN DEVAM EDER ---

# --- ŞİMDİ EN ALTA KÜRASYON KÖŞESİNİ EKLEYELİM ---
# st.write("") # Boşluk
# st.write("") # Boşluk
# st.divider()

# # Kürasyon Listesi
# curation_list = [
#     {"ad": "Jane Eyre", "yil": "2011", "id": "38684"},
#     {"ad": "Atonement", "yil": "2007", "id": "4347"},
#     {"ad": "Rebecca", "yil": "1940", "id": "223"},
#     {"ad": "Portrait of a Lady on Fire", "yil": "2019", "id": "531428"},
#     {"ad": "Far from the Madding Crowd", "yil": "2015", "id": "250734"}
# ]

# if 'current_curation' not in st.session_state:
#     st.session_state.current_curation = random.choice(curation_list)

# selected = st.session_state.current_curation

# # KUTU TASARIMI (Ana sayfanın altında şık bir bölüm)
# st.markdown("### Wuthering Heights'ı beklerken")

# col_poster, col_info = st.columns([1, 4])

# with col_poster:
#     poster_url = get_poster_only(selected['id'])
#     if poster_url:
#         st.image(poster_url, use_container_width=True)

# with col_info:
#     st.subheader(f"{selected['ad']} ({selected['yil']})")
#     if st.button("Başka Bir Öneri"):
#         st.session_state.current_curation = random.choice(curation_list)
#         st.rerun()

# FOOTER
st.divider()
st.caption("🎬 *This product uses the TMDB API but is not endorsed or certified by TMDB.*")
