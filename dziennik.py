import sqlite3
import streamlit as st
import pandas as pd
from datetime import date

# ================= TRYB PRZERWY TECHNICZNEJ =================
PRZERWA_TECHNICZNA = False

if PRZERWA_TECHNICZNA:
    st.warning("⚠️ **Przerwa techniczna!** System Synergia jest obecnie niedostępny z powodu prac konserwacyjnych.")
    st.stop()
# =============================================================

st.set_page_config(page_title="Synergia - Dziennik Elektroniczny", layout="wide")

# Zaawansowany styl 1:1 imitujący interfejs Librus Synergia
st.markdown("""
    <style>
    .stApp {
        background-color: #ffffff;
        font-family: Arial, Helvetica, sans-serif;
    }
    
    .librus-top-nav {
        background-color: #f1f1f3;
        border-bottom: 2px solid #dcdce0;
        padding: 5px 10px;
        font-size: 11px;
        color: #333333;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 5px;
    }
    
    .librus-header-bar {
        background: linear-gradient(to bottom, #fcfcfc 0%, #e6e6ec 100%);
        border: 1px solid #cccccc;
        padding: 8px 15px;
        border-radius: 2px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 15px;
    }
    
    .librus-logo {
        font-size: 26px;
        font-weight: bold;
        color: #6b2d5c;
        font-family: Arial, sans-serif;
        letter-spacing: -1px;
    }

    .librus-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
        font-family: Arial, sans-serif;
    }
    .librus-table th {
        background-color: #e2e2e8;
        color: #333333;
        border: 1px solid #b5b5c0;
        padding: 6px;
        text-align: center;
        font-weight: bold;
    }
    .librus-table td {
        border: 1px solid #cccccc;
        padding: 5px 8px;
        background-color: #ffffff;
    }
    .librus-table tr:nth-child(even) td {
        background-color: #f9f9fb;
    }

    .grade-badge {
        display: inline-block;
        padding: 1px 6px;
        margin: 1px;
        border-radius: 2px;
        font-weight: bold;
        font-size: 11px;
        color: white;
        text-align: center;
    }
    .g-6 { background-color: #2e7d32; }
    .g-5 { background-color: #388e3c; }
    .g-4 { background-color: #0288d1; }
    .g-3 { background-color: #f57c00; }
    .g-2 { background-color: #d32f2f; }
    .g-1 { background-color: #b71c1c; }
    .g-0 { background-color: #757575; }
    .g-np { background-color: #607d8b; }

    .stButton>button {
        background-color: #f0f0f4;
        border: 1px solid #adadb8;
        border-radius: 2px;
        font-size: 11px;
        color: #222222;
        padding: 4px 8px;
    }
    .stButton>button:hover {
        background-color: #e4e4ec;
        border-color: #6b2d5c;
    }
    </style>
""", unsafe_allow_html=True)

conn = sqlite3.connect("dziennik_szkolny.db", check_same_thread=False)
c = conn.cursor()

# Inicjalizacja tabel w bazie danych
c.execute("CREATE TABLE IF NOT EXISTS uzytkownicy (id INTEGER PRIMARY KEY AUTOINCREMENT, imie_nazwisko TEXT, login TEXT, haslo TEXT, rola TEXT, klasa TEXT, powiazany_uczen TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS klasy (id INTEGER PRIMARY KEY AUTOINCREMENT, nazwa_klasy TEXT UNIQUE, wychowawca TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS przypisania (id INTEGER PRIMARY KEY AUTOINCREMENT, nauczyciel TEXT, przedmiot TEXT, klasa TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS oceny (id INTEGER PRIMARY KEY AUTOINCREMENT, uczen TEXT, przedmiot TEXT, ocena TEXT, waga INTEGER, kategoria TEXT, data TEXT, komentarz TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS frekwencja (id INTEGER PRIMARY KEY AUTOINCREMENT, uczen TEXT, data TEXT, lekcja TEXT, status TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS wiadomosci (id INTEGER PRIMARY KEY AUTOINCREMENT, nadawca TEXT, odbiorca TEXT, temat TEXT, tresc TEXT, data TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS uwagi (id INTEGER PRIMARY KEY AUTOINCREMENT, uczen TEXT, nauczyciel TEXT, typ TEXT, tresc TEXT, data TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS plan_lekcji (id INTEGER PRIMARY KEY AUTOINCREMENT, klasa TEXT, dzien TEXT, nr_lekcji TEXT, przedmiot TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS zastepstwa (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, klasa TEXT, nr_lekcji TEXT, stary_przedmiot TEXT, nowy_przedmiot TEXT, nauczyciel TEXT, informacja TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS dyzury (id INTEGER PRIMARY KEY AUTOINCREMENT, osoba TEXT, miejsce TEXT, dzien TEXT, godzina TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS oceny_zachowania (id INTEGER PRIMARY KEY AUTOINCREMENT, uczen TEXT, okres TEXT, ocena TEXT, opis TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS ogloszenia (id INTEGER PRIMARY KEY AUTOINCREMENT, tytul TEXT, tresc TEXT, data TEXT)")
conn.commit()

# Bezpieczna migracja kolumn
migracje = [
    ("oceny", "kategoria", "TEXT"),
    ("oceny", "komentarz", "TEXT"),
    ("uzytkownicy", "klasa", "TEXT"),
    ("uzytkownicy", "powiazany_uczen", "TEXT"),
    ("ogloszenia", "tytul", "TEXT")
]
for tabela, kolumna, typ in migracje:
    try:
        c.execute(f"ALTER TABLE {tabela} ADD COLUMN {kolumna} {typ}")
        conn.commit()
    except sqlite3.OperationalError:
        pass

# Dane startowe dla nowej bazy
c.execute("SELECT COUNT(*) FROM uzytkownicy")
if c.fetchone()[0] == 0:
    c.execute("INSERT INTO uzytkownicy (imie_nazwisko, login, haslo, rola, klasa, powiazany_uczen) VALUES (?, ?, ?, ?, ?, ?)", ("Administrator", "admin", "admin123", "Admin", "-", "-"))
    c.execute("INSERT INTO uzytkownicy (imie_nazwisko, login, haslo, rola, klasa, powiazany_uczen) VALUES (?, ?, ?, ?, ?, ?)", ("Olivier", "olivier", "admin123", "Nauczyciel", "1c", "-"))
    
    uczniowie_1c_start = [
        ("Emilia Widomska", "emilia", "emilia123"),
        ("Adam Nowak", "brak", "brak"),
        ("Barbara Kozakowska", "brak", "brak"),
        ("Katarzyna Nowakówna", "brak", "brak"),
        ("Łucja Widomska", "brak", "brak"),
        ("Adam Kazimierz", "brak", "brak"),
        ("Kacper Opolski", "brak", "brak")
    ]
    for u_imie, u_log, u_has in uczniowie_1c_start:
        c.execute("INSERT INTO uzytkownicy (imie_nazwisko, login, haslo, rola, klasa, powiazany_uczen) VALUES (?, ?, ?, ?, ?, ?)", 
                  (u_imie, u_log, u_has, "Uczeń", "1c", "-"))
                  
    c.execute("INSERT INTO uzytkownicy (imie_nazwisko, login, haslo, rola, klasa, powiazany_uczen) VALUES (?, ?, ?, ?, ?, ?)", ("Jan Widomski", "rodzic_emilia", "rodzic123", "Rodzic", "1c", "Emilia Widomska"))
    c.execute("INSERT INTO klasy (nazwa_klasy, wychowawca) VALUES (?, ?)", ("1c", "Olivier"))
    conn.commit()

c.execute("SELECT COUNT(*) FROM ogloszenia")
if c.fetchone()[0] == 0:
    c.execute("INSERT INTO ogloszenia (tytul, tresc, data) VALUES (?, ?, ?)", ("Witamy w nowym semestrze!", "Zapraszamy do korzystania z dziennika elektronicznego Synergia.", str(date.today())))
    conn.commit()

c.execute("SELECT COUNT(*) FROM plan_lekcji")
if c.fetchone()[0] == 0:
    domyslny_plan = [
        ("1c", "Poniedziałek", "1 [07:10 - 07:55]", "Plastyka"),
        ("1c", "Poniedziałek", "2 [08:00 - 08:45]", "Matematyka"),
    ]
    c.executemany("INSERT INTO plan_lekcji (klasa, dzien, nr_lekcji, przedmiot) VALUES (?, ?, ?, ?)", domyslny_plan)
    conn.commit()

c.execute("SELECT COUNT(*) FROM dyzury")
if c.fetchone()[0] == 0:
    c.execute("INSERT INTO dyzury (osoba, miejsce, dzien, godzina) VALUES (?, ?, ?, ?)", ("Olivier", "Parter - Wejście główne", "Poniedziałek", "Przerwa 09:40 - 09:50"))
    conn.commit()

if "dziennik_user" not in st.session_state:
    st.session_state["dziennik_user"] = None
if "dziennik_rola" not in st.session_state:
    st.session_state["dziennik_rola"] = None
if "librus_aktywna_zakladka" not in st.session_state:
    st.session_state["librus_aktywna_zakladka"] = "Oceny"

if "lekcja_temat" not in st.session_state:
    st.session_state["lekcja_temat"] = "Wprowadzenie do nowego działu"

WSZYSTKIE_PRZEDMIOTY = [
    "Biologia", "Chemia", "Fizyka", "Geografia", "Historia", "Informatyka", 
    "Język angielski", "Język polski", "Matematyka", "Plastyka", "Wychowanie fizyczne"
]

KATEGORIE_OCEN = [
    "aktywność", "inna", "kartkówka", "odpowiedź ustna", 
    "praca na lekcji", "przewidywana roczna", "przewidywana śródroczna", 
    "roczna", "sprawdzian", "śródroczna", "zadanie", "zeszyt"
]

PELNE_GODZINY_LEKCYJNE = [
    "1 [07:10 - 07:55]", "2 [08:00 - 08:45]", "3 [08:55 - 09:40]",
    "4 [09:50 - 10:35]", "5 [10:45 - 11:30]", "6 [11:50 - 12:35]",
    "7 [12:45 - 13:30]", "8 [13:40 - 14:25]", "9 [14:30 - 15:10]"
]

DNI_TYGODNIA = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek"]

def renderuj_tabelue_planu_dla_klasy(docelowa_klasa, allow_change=False):
    c.execute("SELECT nazwa_klasy FROM klasy")
    klasy_baza = [k[0] for k in c.fetchall()]
    if not klasy_baza:
        klasy_baza = ["1c"]
        
    if docelowa_klasa not in klasy_baza:
        docelowa_klasa = klasy_baza[0]
        
    if allow_change:
        wybrana_klasa = st.selectbox("Wybierz klasę:", klasy_baza, index=klasy_baza.index(docelowa_klasa), key=f"sel_plan_{docelowa_klasa}")
    else:
        wybrana_klasa = docelowa_klasa
        st.markdown(f"**Klasa:** {wybrana_klasa}")

    st.markdown(f"### Plan lekcji i Zastępstwa — Klasa: {wybrana_klasa}")
    
    df_p = pd.read_sql("SELECT dzien, nr_lekcji, przedmiot FROM plan_lekcji WHERE klasa = ?", conn, params=(wybrana_klasa,))
    df_z = pd.read_sql("SELECT nr_lekcji, nowy_przedmiot, informacja FROM zastepstwa WHERE klasa = ?", conn, params=(wybrana_klasa,))
    
    if not df_p.empty and not df_z.empty:
        zast_dict = {row.nr_lekcji: (row.nowy_przedmiot, row.informacja) for row in df_z.itertuples()}
        df_p['przedmiot'] = df_p.apply(lambda r: f"🚫 {zast_dict[r['nr_lekcji']][0]} ({zast_dict[r['nr_lekcji']][1]})" if r['nr_lekcji'] in zast_dict else r['przedmiot'], axis=1)

    if not df_p.empty:
        pivot_plan = df_p.pivot_table(index="nr_lekcji", columns="dzien", values="przedmiot", aggfunc=lambda x: ', '.join(str(v) for v in x))
        dostepne_dni = [d for d in DNI_TYGODNIA if d in pivot_plan.columns]
        inne_dni = [d for d in pivot_plan.columns if d not in DNI_TYGODNIA]
        pivot_plan = pivot_plan[dostepne_dni + inne_dni]
        st.dataframe(pivot_plan, use_container_width=True)
    else:
        st.info(f"Brak zdefiniowanego planu lekcji dla klasy {wybrana_klasa}.")

def renderuj_tabelue_ocen_dla_ucznia(imie_ucznia):
    c.execute("SELECT klasa FROM uzytkownicy WHERE imie_nazwisko = ?", (imie_ucznia,))
    res_k = c.fetchone()
    klasa_ucznia = res_k[0] if res_k and res_k[0] != "-" else "1c"
    
    st.markdown("### Oceny bieżące")
    
    html_tabeli = """
    <table class="librus-table">
        <thead>
            <tr>
                <th rowspan="2" style="width: 25%;">Przedmiot</th>
                <th colspan="3">Okres 1</th>
                <th colspan="3">Okres 2</th>
            </tr>
            <tr>
                <th>Oceny bieżące</th>
                <th style="width: 8%;">Śr. 1</th>
                <th style="width: 6%;">R</th>
                <th>Oceny bieżące</th>
                <th style="width: 8%;">Śr. 2</th>
                <th style="width: 6%;">R</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for przedm in WSZYSTKIE_PRZEDMIOTY:
        df_oceny_p = pd.read_sql("SELECT ocena, waga FROM oceny WHERE uczen = ? AND przedmiot = ?", conn, params=(imie_ucznia, przedm))
        okres_1_html = ""
        srednia_p = "-"
        if not df_oceny_p.empty:
            badge_list = []
            suma_wazona = 0
            suma_wag = 0
            for row in df_oceny_p.itertuples():
                val_str = str(row.ocena)
                waga = int(row.waga)
                css_klasa = f"g-{val_str}" if val_str in ["0", "1", "2", "3", "4", "5", "6"] else "g-np"
                badge_list.append(f'<span class="grade-badge {css_klasa}">{val_str}</span>')
                if val_str.isdigit():
                    val = int(val_str)
                    if val > 0:
                        suma_wazona += val * waga
                        suma_wag += waga
            okres_1_html = " ".join(badge_list)
            if suma_wag > 0:
                srednia_p = round(suma_wazona / suma_wag, 2)
        else:
            okres_1_html = '<span style="color: #999; font-style: italic;">Brak ocen</span>'
            
        html_tabeli += f"""
            <tr>
                <td><b>{przedm}</b></td>
                <td>{okres_1_html}</td>
                <td style="text-align: center;"><b>{srednia_p}</b></td>
                <td style="text-align: center;">-</td>
                <td style="color: #999; font-style: italic;">Brak ocen</td>
                <td style="text-align: center;">-</td>
                <td style="text-align: center;">-</td>
            </tr>
        """
        
    html_tabeli += "</tbody></table>"
    st.markdown(html_tabeli, unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("Szczegóły i historia ocen")
    df_szczegoly = pd.read_sql("SELECT data as [Data], przedmiot as [Przedmiot], ocena as [Ocena], kategoria as [Kategoria], waga as [Waga], komentarz as [Komentarz] FROM oceny WHERE uczen = ?", conn, params=(imie_ucznia,))
    if not df_szczegoly.empty:
        st.dataframe(df_szczegoly, use_container_width=True, hide_index=True)
    else:
        st.info("Brak szczegółów ocen.")

def renderuj_zakladke_wiadomosci(aktualny_uzytkownik):
    st.subheader("Wiadomości")
    c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE imie_nazwisko != ?", (aktualny_uzytkownik,))
    osoby = [o[0] for o in c.fetchall()]
    
    with st.form("form_wyslij_wiadomosc"):
        st.write("### Nowa wiadomość")
        odb = st.selectbox("Adresat:", osoby if osoby else ["Brak"])
        temat = st.text_input("Temat:")
        tresc = st.text_area("Treść:")
        if st.form_submit_button("Wyślij", type="primary"):
            if odb and odb != "Brak":
                c.execute("INSERT INTO wiadomosci (nadawca, odbiorca, temat, tresc, data) VALUES (?, ?, ?, ?, ?)",
                          (aktualny_uzytkownik, odb, temat, tresc, str(date.today())))
                conn.commit()
                st.success("Wiadomość została wysłana.")
                st.rerun()

    st.markdown("---")
    st.subheader("Odebrane")
    df_msg = pd.read_sql("SELECT id, nadawca as [Od], temat as [Temat], tresc as [Treść], data as [Data] FROM wiadomosci WHERE odbiorca = ? ORDER BY id DESC", conn, params=(aktualny_uzytkownik,))
    
    if not df_msg.empty:
        for idx, row in df_msg.iterrows():
            st.markdown(f"""
                <div style="background-color: #f9f9fb; padding: 10px; border: 1px solid #dcdce0; border-radius: 2px; margin-bottom: 8px; font-size: 12px;">
                    <b>Od: {row['Od']}</b> | <i>Data: {row['Data']}</i><br>
                    <b>Temat: {row['Temat']}</b><br>
                    <p style="margin-top: 4px;">{row['Treść']}</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Usuń wiadomość", key=f"del_msg_{row['id']}"):
                c.execute("DELETE FROM wiadomosci WHERE id = ?", (row['id'],))
                conn.commit()
                st.rerun()
    else:
        st.info("Skrzynka odbiorcza jest pusta.")

# ================= EKRAN LOGOWANIA LIBRUS (STABILNY) =================
if st.session_state["dziennik_user"] is None:
    st.markdown("""
        <div style="text-align: center; margin-top: 40px; margin-bottom: 20px;">
            <div style="font-size: 42px; font-weight: bold; color: #6b2d5c; font-family: Arial;">Synergia</div>
            <div style="font-size: 14px; color: #555555;">System Obsługi Szkoły i Placówki Oświatowej</div>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown('<div style="background: #f4f4f7; padding: 25px; border: 1px solid #cccccc; border-radius: 3px;">', unsafe_allow_html=True)
        
        # Stabilny formularz logowania
        with st.form("form_logowania_stabilne", clear_on_submit=False):
            st.subheader("Logowanie do systemu")
            login_in = st.text_input("Login:")
            haslo_in = st.text_input("Hasło:", type="password", help="Wpisz swoje hasło dostępowe")
            btn_log = st.form_submit_button("Zaloguj się", use_container_width=True)
            
            if btn_log:
                c.execute("SELECT imie_nazwisko, rola, login FROM uzytkownicy WHERE login = ? AND haslo = ?", (login_in.strip(), haslo_in))
                res = c.fetchone()
                if res:
                    if res[2] == "brak":
                        st.error("Konto nie jest aktywowane.")
                    else:
                        st.session_state["dziennik_user"] = res[0]
                        st.session_state["dziennik_rola"] = res[1]
                        st.success("Zalogowano pomyślnie!")
                        st.rerun()
                else:
                    st.error("Błędny login lub hasło.")
                    
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("Ogłoszenia")
        df_ogloszenia_pub = pd.read_sql("SELECT data as [Data], tytul as [Tytuł], tresc as [Treść] FROM ogloszenia ORDER BY id DESC", conn)
        if not df_ogloszenia_pub.empty:
            for idx, row in df_ogloszenia_pub.iterrows():
                st.markdown(f"""
                    <div style="background-color: #f9f9fb; padding: 8px; border: 1px solid #dcdce0; border-radius: 2px; margin-bottom: 6px; font-size: 12px;">
                        <b>{row['Data']} — {row['Tytuł']}</b><br>{row['Treść']}
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Brak ogłoszeń.")

    st.stop()

# ================= GÓRNY PASEK NAWIGACYJNY LIBRUS =================
st.markdown(f"""
    <div class="librus-top-nav">
        <div><b>Synergia</b> | Zalogowany jako: <b>{st.session_state['dziennik_user']}</b> ({st.session_state['dziennik_rola']})</div>
        <div>Portal Librus Synergia</div>
    </div>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="librus-header-bar">
        <div class="librus-logo">Synergia</div>
        <div style="font-size: 11px; color: #444;">Rok szkolny 2025/2026</div>
    </div>
""", unsafe_allow_html=True)

# 100% responsywne menu mobilne
opcje_menu = ["📊 Oceny", "📋 Frekwencja", "✉️ Wiadomości", "📢 Ogłoszenia", "📖 Lekcja", "⚠️ Uwagi", "📅 Plan", "⚙️ Ustawienia", "🚪 Wyloguj"]
wybrana_opcja_menu = st.selectbox("Wybierz moduł (Menu Synergia):", opcje_menu)

if "Oceny" in wybrana_opcja_menu:
    st.session_state["librus_aktywna_zakladka"] = "Oceny"
elif "Frekwencja" in wybrana_opcja_menu:
    st.session_state["librus_aktywna_zakladka"] = "Frekwencja"
elif "Wiadomości" in wybrana_opcja_menu:
    st.session_state["librus_aktywna_zakladka"] = "Wiadomości"
elif "Ogłoszenia" in wybrana_opcja_menu:
    st.session_state["librus_aktywna_zakladka"] = "Ogłoszenia"
elif "Lekcja" in wybrana_opcja_menu:
    st.session_state["librus_aktywna_zakladka"] = "Realizacja"
elif "Uwagi" in wybrana_opcja_menu:
    st.session_state["librus_aktywna_zakladka"] = "Uwagi"
elif "Plan" in wybrana_opcja_menu:
    st.session_state["librus_aktywna_zakladka"] = "Plan"
elif "Ustawienia" in wybrana_opcja_menu:
    st.session_state["librus_aktywna_zakladka"] = "Ustawienia"
elif "Wyloguj" in wybrana_opcja_menu:
    st.session_state["dziennik_user"] = None
    st.session_state["dziennik_rola"] = None
    st.rerun()

st.divider()

akt_zakl = st.session_state["librus_aktywna_zakladka"]
rola = st.session_state["dziennik_rola"]
user = st.session_state["dziennik_user"]

# ================= ZAKŁADKA USTAWIENIA =================
if akt_zakl == "Ustawienia":
    st.subheader("Ustawienia konta")
    with st.form("form_zmien_haslo"):
        st_haslo_stare = st.text_input("Aktualne hasło:", type="password")
        st_haslo_nowe = st.text_input("Nowe hasło:", type="password")
        st_haslo_nowe_powt = st.text_input("Powtórz nowe hasło:", type="password")
        if st.form_submit_button("Zmień hasło", type="primary"):
            c.execute("SELECT haslo FROM uzytkownicy WHERE imie_nazwisko = ?", (user,))
            db_haslo = c.fetchone()[0]
            if st_haslo_stare != db_haslo:
                st.error("Błędne aktualne hasło.")
            elif st_haslo_nowe != st_haslo_nowe_powt:
                st.error("Nowe hasła nie zgadzają się.")
            else:
                c.execute("UPDATE uzytkownicy SET haslo = ? WHERE imie_nazwisko = ?", (st_haslo_nowe, user))
                conn.commit()
                st.success("Hasło zmienione pomyślnie!")

elif akt_zakl == "Ogłoszenia":
    st.subheader("Ogłoszenia szkolne")
    df_ogl = pd.read_sql("SELECT data as [Data], tytul as [Tytuł], tresc as [Treść] FROM ogloszenia ORDER BY id DESC", conn)
    if not df_ogl.empty:
        for idx, row in df_ogl.iterrows():
            st.markdown(f"""
                <div style="background-color: #f9f9fb; padding: 10px; border: 1px solid #dcdce0; border-radius: 2px; margin-bottom: 8px;">
                    <b>📅 {row['Data']} — {row['Tytuł']}</b><br>
                    <p style="margin-top: 4px;">{row['Treść']}</p>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Brak ogłoszeń.")

# ================= PANEL ADMINISTRATORA =================
elif rola == "Admin":
    st.subheader("Panel Administratora")
    adm_tab1, adm_tab2, adm_tab3, adm_tab4, adm_tab5, adm_tab6, adm_tab7, adm_tab8 = st.tabs(["Zastępstwa", "📢 Ogłoszenia", "Zachowanie", "Użytkownicy", "Przypisania", "📅 Plan", "🛡️ Dyżury", "Wiadomości"])
    
    with adm_tab1:
        st.subheader("Zarządzanie Zastępstwami")
        tryb_zast = st.radio("Akcja:", ["Dodaj zastępstwo", "Usuń zastępstwo"], horizontal=True)
        if tryb_zast == "Dodaj zastępstwo":
            with st.form("form_zastepstwo_adm"):
                z_data = st.date_input("Data:", value=date.today())
                z_klasa = st.text_input("Klasa:", value="1c")
                z_nr = st.selectbox("Nr lekcji:", PELNE_GODZINY_LEKCYJNE)
                z_stary = st.text_input("Stary przedmiot:")
                typ_zmiany = st.selectbox("Rodzaj:", ["Zastępstwo / Zmiana przedmiotu", "🚫 Odwołanie lekcji"])
                if typ_zmiany == "🚫 Odwołanie lekcji":
                    z_nowy = "Lekcja odwołana"
                    z_nauczyciel = "-"
                    z_info = st.text_input("Informacja:", value="Lekcja odwołana")
                else:
                    z_nowy = st.text_input("Nowy przedmiot:")
                    z_nauczyciel = st.text_input("Nauczyciel:")
                    z_info = st.text_input("Komentarz:")
                if st.form_submit_button("Zapisz", type="primary"):
                    c.execute("INSERT INTO zastepstwa (data, klasa, nr_lekcji, stary_przedmiot, nowy_przedmiot, nauczyciel, informacja) VALUES (?, ?, ?, ?, ?, ?, ?)",
                              (str(z_data), z_klasa, z_nr, z_stary, z_nowy, z_nauczyciel, z_info))
                    conn.commit()
                    st.success("Zapisano!")
                    st.rerun()
        else:
            df_zast_all = pd.read_sql("SELECT id, data as [Data], klasa as [Klasa], nr_lekcji as [Lekcja], nowy_przedmiot as [Zmiana] FROM zastepstwa", conn)
            if not df_zast_all.empty:
                st.dataframe(df_zast_all, use_container_width=True, hide_index=True)
                with st.form("form_usun_zastepstwo"):
                    id_zast_del = st.selectbox("ID wpisu:", df_zast_all["id"].tolist())
                    if st.form_submit_button("Usuń", type="primary"):
                        c.execute("DELETE FROM zastepstwa WHERE id = ?", (id_zast_del,))
                        conn.commit()
                        st.success("Usunięto!")
                        st.rerun()
            else:
                st.info("Brak zastępstw.")

    with adm_tab2:
        st.subheader("Zarządzanie Ogłoszeniami")
        with st.form("form_dodaj_ogloszenie"):
            og_tytul = st.text_input("Tytuł:")
            og_tresc = st.text_area("Treść:")
            og_data = st.date_input("Data:", value=date.today())
            if st.form_submit_button("Opublikuj", type="primary"):
                if og_tytul.strip() and og_tresc.strip():
                    c.execute("INSERT INTO ogloszenia (tytul, tresc, data) VALUES (?, ?, ?)", (og_tytul, og_tresc, str(og_data)))
                    conn.commit()
                    st.success("Opublikowano!")
                    st.rerun()
        st.markdown("---")
        df_ogl_all = pd.read_sql("SELECT id, data as [Data], tytul as [Tytuł] FROM ogloszenia", conn)
        if not df_ogl_all.empty:
            st.dataframe(df_ogl_all, use_container_width=True, hide_index=True)
            with st.form("form_usun_ogloszenie"):
                id_ogl_del = st.selectbox("ID ogłoszenia:", df_ogl_all["id"].tolist())
                if st.form_submit_button("Usuń", type="primary"):
                    c.execute("DELETE FROM ogloszenia WHERE id = ?", (id_ogl_del,))
                    conn.commit()
                    st.success("Usunięto!")
                    st.rerun()

    with adm_tab3:
        st.subheader("Oceny Zachowania")
        with st.form("form_dodaj_zachowanie"):
            c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE rola = 'Uczeń'")
            uczniowie_l = [u[0] for u in c.fetchall()]
            z_uczen = st.selectbox("Uczeń:", uczniowie_l if uczniowie_l else ["Brak"])
            z_okres = st.selectbox("Okres:", ["I okres", "II okres", "Roczna"])
            z_ocena_z = st.selectbox("Ocena:", ["Wzorowe", "Bardzo dobre", "Dobre", "Poprawne", "Nieodpowiednie", "Naganne"])
            z_opis = st.text_area("Opis:")
            if st.form_submit_button("Dodaj", type="primary"):
                if z_uczen != "Brak":
                    c.execute("INSERT INTO oceny_zachowania (uczen, okres, ocena, opis) VALUES (?, ?, ?, ?)", (z_uczen, z_okres, z_ocena_z, z_opis))
                    conn.commit()
                    st.success("Dodano!")
                    st.rerun()

    with adm_tab4:
        st.subheader("Użytkownicy")
        sub_adm_t1, sub_adm_t2, sub_adm_t3 = st.tabs(["➕ Dodaj", "✏️ Edytuj", "🗑️ Usuń"])
        c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE rola = 'Uczeń'")
        uczniowie_baza = [u[0] for u in c.fetchall()]
        
        with sub_adm_t1:
            with st.form("form_dodaj_uzytkownika"):
                d_imie = st.text_input("Imię i nazwisko:")
                d_login = st.text_input("Login:", value="brak")
                d_haslo = st.text_input("Hasło:", value="brak", type="password")
                d_rola = st.selectbox("Rola:", ["Admin", "Nauczyciel", "Uczeń", "Rodzic"])
                d_klasa = st.text_input("Klasa:", value="1c")
                d_powiazany = st.selectbox("Powiązany uczeń:", ["-"] + uczniowie_baza)
                if st.form_submit_button("Dodaj", type="primary"):
                    c.execute("INSERT INTO uzytkownicy (imie_nazwisko, login, haslo, rola, klasa, powiazany_uczen) VALUES (?, ?, ?, ?, ?, ?)",
                              (d_imie, d_login, d_haslo, d_rola, d_klasa, d_powiazany))
                    conn.commit()
                    st.success("Dodano!")
                    st.rerun()

        with sub_adm_t2:
            c.execute("SELECT id, imie_nazwisko FROM uzytkownicy")
            wszyscy_u = c.fetchall()
            u_slownik = {f"{u[1]} (ID: {u[0]})": u[0] for u in wszyscy_u}
            if u_slownik:
                wybrany_edycja = st.selectbox("Użytkownik:", list(u_slownik.keys()))
                ed_id = u_slownik[wybrany_edycja]
                c.execute("SELECT imie_nazwisko, login, haslo, rola, klasa, powiazany_uczen FROM uzytkownicy WHERE id = ?", (ed_id,))
                dane_u = c.fetchone()
                with st.form("form_edytuj_uzytkownika"):
                    ed_imie = st.text_input("Imię i nazwisko:", value=dane_u[0])
                    ed_login = st.text_input("Login:", value=dane_u[1])
                    ed_haslo = st.text_input("Hasło:", value=dane_u[2])
                    role_lista = ["Admin", "Nauczyciel", "Uczeń", "Rodzic"]
                    ed_rola = st.selectbox("Rola:", role_lista, index=role_lista.index(dane_u[3]) if dane_u[3] in role_lista else 0)
                    ed_klasa = st.text_input("Klasa:", value=dane_u[4])
                    if st.form_submit_button("Zapisz", type="primary"):
                        c.execute("UPDATE uzytkownicy SET imie_nazwisko = ?, login = ?, haslo = ?, rola = ?, klasa = ? WHERE id = ?",
                                  (ed_imie, ed_login, ed_haslo, ed_rola, ed_klasa, ed_id))
                        conn.commit()
                        st.success("Zaktualizowano!")
                        st.rerun()

        with sub_adm_t3:
            df_u_del = pd.read_sql("SELECT id, imie_nazwisko as [Imię], rola as [Rola] FROM uzytkownicy", conn)
            st.dataframe(df_u_del, use_container_width=True, hide_index=True)
            with st.form("form_usun_uzytkownika"):
                id_u_del = st.selectbox("ID:", df_u_del["id"].tolist() if not df_u_del.empty else [0])
                if st.form_submit_button("Usuń", type="primary"):
                    if id_u_del > 1:
                        c.execute("DELETE FROM uzytkownicy WHERE id = ?", (id_u_del,))
                        conn.commit()
                        st.success("Usunięto!")
                        st.rerun()

    with adm_tab5:
        st.subheader("Przypisania")
        with st.form("form_przypisz"):
            c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE rola = 'Nauczyciel'")
            nauczyciele_l = [n[0] for n in c.fetchall()]
            c.execute("SELECT nazwa_klasy FROM klasy")
            klasy_l = [k[0] for k in c.fetchall()]
            p_nauczyciel = st.selectbox("Nauczyciel:", nauczyciele_l if nauczyciele_l else ["Brak"])
            p_przedmiot = st.selectbox("Przedmiot:", WSZYSTKIE_PRZEDMIOTY)
            p_klasa = st.selectbox("Klasa:", klasy_l if klasy_l else ["1c"])
            if st.form_submit_button("Przypisz", type="primary"):
                c.execute("INSERT INTO przypisania (nauczyciel, przedmiot, klasa) VALUES (?, ?, ?)", (p_nauczyciel, p_przedmiot, p_klasa))
                conn.commit()
                st.success("Przypisano!")
                st.rerun()

    with adm_tab6:
        st.subheader("Plan lekcji")
        with st.form("form_plan"):
            c.execute("SELECT nazwa_klasy FROM klasy")
            klasy_p_l = [k[0] for k in c.fetchall()]
            pl_klasa = st.selectbox("Klasa:", klasy_p_l if klasy_p_l else ["1c"])
            pl_dzien = st.selectbox("Dzień:", DNI_TYGODNIA)
            pl_nr = st.selectbox("Godzina:", PELNE_GODZINY_LEKCYJNE)
            pl_przedmiot = st.selectbox("Przedmiot:", WSZYSTKIE_PRZEDMIOTY)
            if st.form_submit_button("Dodaj", type="primary"):
                c.execute("INSERT INTO plan_lekcji (klasa, dzien, nr_lekcji, przedmiot) VALUES (?, ?, ?, ?)", (pl_klasa, pl_dzien, pl_nr, pl_przedmiot))
                conn.commit()
                st.success("Dodano!")
                st.rerun()

    with adm_tab7:
        st.subheader("Dyżury")
        with st.form("form_dyzur"):
            c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE rola = 'Nauczyciel'")
            nauczyciele_l = [n[0] for n in c.fetchall()]
            dyz_osoba = st.selectbox("Nauczyciel:", nauczyciele_l if nauczyciele_l else ["Olivier"])
            dyz_miejsce = st.text_input("Miejsce:")
            dyz_dzien = st.selectbox("Dzień:", DNI_TYGODNIA)
            dyz_godzina = st.text_input("Godzina:")
            if st.form_submit_button("Dodaj", type="primary"):
                c.execute("INSERT INTO dyzury (osoba, miejsce, dzien, godzina) VALUES (?, ?, ?, ?)", (dyz_osoba, dyz_miejsce, dyz_dzien, dyz_godzina))
                conn.commit()
                st.success("Dodano!")
                st.rerun()

    with adm_tab8:
        renderuj_zakladke_wiadomosci("Administrator")

# ================= PANEL NAUCZYCIELA =================
elif rola == "Nauczyciel":
    if akt_zakl == "Realizacja" or akt_zakl == "Oceny" or akt_zakl == "Uwagi" or akt_zakl == "Wiadomości" or akt_zakl == "Plan" or akt_zakl == "Frekwencja":
        
        nauczyciel_glowne_menu = st.radio("Widok nauczyciela:", ["Dziennik lekcyjny (Tematy i Frekwencja)", "Oceny bieżące", "Uwagi", "Wiadomości", "Plan i Dyżury", "Frekwencja zestawienie"], horizontal=True)
        
        st.divider()

        if "Dziennik lekcyjny" in nauczyciel_glowne_menu:
            st.markdown("### Realizacja programu i Frekwencja")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                data_lekcji = st.date_input("Data lekcji:", value=date.today(), key="in_data_lekcji")
            with col_d2:
                klasa_wyb = st.selectbox("Klasa:", ["1c"], key="in_klasa_lekcji")
                
            col_l1, col_l2 = st.columns(2)
            with col_l1:
                nr_jednostki = st.selectbox("Nr lekcji:", PELNE_GODZINY_LEKCYJNE, key="in_nr_lekcji")
            with col_l2:
                przedmiot_wyb = st.selectbox("Przedmiot:", WSZYSTKIE_PRZEDMIOTY, key="in_przedmiot_lekcji")
                
            def update_temat():
                st.session_state["lekcja_temat"] = st.session_state["widget_temat_input"]

            temat_lekcji = st.text_input("Temat lekcji:", value=st.session_state["lekcja_temat"], key="widget_temat_input", on_change=update_temat)
            st.session_state["lekcja_temat"] = temat_lekcji
            
            st.markdown("---")
            st.markdown("### Frekwencja uczniów")
            c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE klasa = ? AND rola = 'Uczeń'", (klasa_wyb,))
            uczniowie_klas = c.fetchall()
            frekwencja_wyniki = {}
            if uczniowie_klas:
                for idx, uczen in enumerate(uczniowie_klas, 1):
                    col_u_name, col_u_radio = st.columns([2, 5])
                    with col_u_name:
                        st.write(f"{idx}. {uczen[0]}")
                    with col_u_radio:
                        status = st.radio(f"st_{uczen[0]}", ["ob", "nb", "u", "sp", "zw"], horizontal=True, label_visibility="collapsed", key=f"radio_freq_{uczen[0]}")
                        frekwencja_wyniki[uczen[0]] = status
            
            if st.button("Zapisz lekcję i frekwencję", type="primary"):
                for uczen, status in frekwencja_wyniki.items():
                    c.execute("INSERT INTO frekwencja (uczen, data, lekcja, status) VALUES (?, ?, ?, ?)", (uczen, str(data_lekcji), nr_jednostki, status))
                conn.commit()
                st.success("Zapisano pomyślnie!")

        elif "Oceny bieżące" in nauczyciel_glowne_menu:
            st.markdown("### Dziennik Ocen")
            col_op1, col_op2 = st.columns(2)
            with col_op1:
                wybrany_przedmiot = st.selectbox("Przedmiot:", WSZYSTKIE_PRZEDMIOTY)
            with col_op2:
                c.execute("SELECT nazwa_klasy FROM klasy")
                klasy_baza = [k[0] for k in c.fetchall()]
                wybrana_klasa = st.selectbox("Klasa:", klasy_baza if klasy_baza else ["1c"])

            nauczyciel_tabs = st.tabs(["Tabela ocen", "Wystaw ocenę", "Edytuj / Usuń"])

            with nauczyciel_tabs[0]:
                c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE klasa = ? AND rola = 'Uczeń'", (wybrana_klasa,))
                uczniowie_klasy = c.fetchall()
                if uczniowie_klasy:
                    tabela_wiersze = []
                    for idx, uczen_row in enumerate(uczniowie_klasy, 1):
                        u_nazwisko = uczen_row[0]
                        df_oceny_u = pd.read_sql("SELECT ocena FROM oceny WHERE uczen = ? AND przedmiot = ?", conn, params=(u_nazwisko, wybrany_przedmiot))
                        badge_list = [f'<span class="grade-badge g-{r.ocena}">{r.ocena}</span>' for r in df_oceny_u.itertuples()] if not df_oceny_u.empty else ['<span style="color:gray;">Brak</span>']
                        tabela_wiersze.append({"Nr": idx, "Uczeń": u_nazwisko, "Oceny": " ".join(badge_list)})
                    st.write(pd.DataFrame(tabela_wiersze).to_html(escape=False, index=False), unsafe_allow_html=True)

            with nauczyciel_tabs[1]:
                with st.form("form_wystaw_ocene"):
                    c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE klasa = ? AND rola = 'Uczeń'", (wybrana_klasa,))
                    uczniowie_l = [u[0] for u in c.fetchall()]
                    uczen_docelowy = st.selectbox("Uczeń:", uczniowie_l if uczniowie_l else ["Brak"])
                    ocena_val = st.selectbox("Ocena:", ["0", "1", "2", "3", "4", "5", "6", "np"], index=5)
                    kategoria_val = st.selectbox("Kategoria:", KATEGORIE_OCEN, index=7)
                    waga_val = st.number_input("Waga:", min_value=1, max_value=10, value=5)
                    komentarz_val = st.text_area("Komentarz:")
                    if st.form_submit_button("Zapisz", type="primary"):
                        c.execute("INSERT INTO oceny (uczen, przedmiot, ocena, waga, kategoria, data, komentarz) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                  (uczen_docelowy, wybrany_przedmiot, ocena_val, waga_val, kategoria_val, str(date.today()), komentarz_val))
                        conn.commit()
                        st.success("Wystawiono ocenę!")
                        st.rerun()

            with nauczyciel_tabs[2]:
                df_w_o = pd.read_sql("SELECT id, uczen, ocena, kategoria FROM oceny WHERE przedmiot = ?", conn, params=(wybrany_przedmiot,))
                if not df_w_o.empty:
                    st.dataframe(df_w_o, use_container_width=True, hide_index=True)
                    with st.form("form_del_ocena"):
                        id_o_del = st.selectbox("ID oceny do usunięcia:", df_w_o["id"].tolist())
                        if st.form_submit_button("Usuń", type="primary"):
                            c.execute("DELETE FROM oceny WHERE id = ?", (id_o_del,))
                            conn.commit()
                            st.success("Usunięto!")
                            st.rerun()

        elif "Uwagi" in nauczyciel_glowne_menu:
            with st.form("form_uwaga"):
                c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE rola = 'Uczeń'")
                uczniowie_l = [u[0] for u in c.fetchall()]
                uw_uczen = st.selectbox("Uczeń:", uczniowie_l if uczniowie_l else ["Emilia Widomska"])
                uw_typ = st.selectbox("Typ:", ["Pozytywna", "Neutralna", "Negatywna"])
                uw_tresc = st.text_area("Treść:")
                if st.form_submit_button("Dodaj uwagę", type="primary"):
                    c.execute("INSERT INTO uwagi (uczen, nauczyciel, typ, tresc, data) VALUES (?, ?, ?, ?, ?)", (uw_uczen, user, uw_typ, uw_tresc, str(date.today())))
                    conn.commit()
                    st.success("Dodano!")
                    st.rerun()

        elif "Wiadomości" in nauczyciel_glowne_menu:
            renderuj_zakladke_wiadomosci(user)

        elif "Plan i Dyżury" in nauczyciel_glowne_menu:
            renderuj_tabelue_planu_dla_klasy("1c", allow_change=True)

        elif "Frekwencja zestawienie" in nauczyciel_glowne_menu:
            df_fr = pd.read_sql("SELECT uczen as [Uczeń], data as [Data], status as [Status] FROM frekwencja", conn)
            st.dataframe(df_fr, use_container_width=True, hide_index=True)

# ================= PANEL UCZNIA =================
elif rola == "Uczeń":
    c.execute("SELECT klasa FROM uzytkownicy WHERE imie_nazwisko = ?", (user,))
    res_ku = c.fetchone()
    klasa_ucz = res_ku[0] if res_ku and res_ku[0] != "-" else "1c"

    if akt_zakl == "Oceny":
        renderuj_tabelue_ocen_dla_ucznia(user)
    elif akt_zakl == "Plan":
        renderuj_tabelue_planu_dla_klasy(klasa_ucz)
    elif akt_zakl == "Wiadomości":
        renderuj_zakladke_wiadomosci(user)
    elif akt_zakl == "Uwagi":
        st.subheader("Moje uwagi")
        df_uw = pd.read_sql("SELECT data as [Data], typ as [Typ], tresc as [Treść] FROM uwagi WHERE uczen = ?", conn, params=(user,))
        if not df_uw.empty:
            st.dataframe(df_uw, use_container_width=True, hide_index=True)
        else:
            st.info("Brak uwag.")
    elif akt_zakl == "Frekwencja":
        st.subheader("Moja frekwencja")
        df_f_ucz = pd.read_sql("SELECT data as [Data], status as [Status] FROM frekwencja WHERE uczen = ?", conn, params=(user,))
        if not df_f_ucz.empty:
            st.dataframe(df_f_ucz, use_container_width=True, hide_index=True)
        else:
            st.info("Brak frekwencji.")

# ================= PANEL RODZICA =================
elif rola == "Rodzic":
    c.execute("SELECT powiazany_uczen FROM uzytkownicy WHERE imie_nazwisko = ?", (user,))
    res_p = c.fetchone()
    dziecko = res_p[0] if res_p and res_p[0] != "-" else "Emilia Widomska"
    
    st.subheader(f"Panel Rodzica — Podgląd dziecka: {dziecko}")
    
    if akt_zakl == "Oceny":
        renderuj_tabelue_ocen_dla_ucznia(dziecko)
    elif akt_zakl == "Wiadomości":
        renderuj_zakladke_wiadomosci(user)
    elif akt_zakl == "Frekwencja":
        df_f_d = pd.read_sql("SELECT data as [Data], status as [Status] FROM frekwencja WHERE uczen = ?", conn, params=(dziecko,))
        st.dataframe(df_f_d, use_container_width=True, hide_index=True)
