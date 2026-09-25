import sqlite3
import streamlit as st
import pandas as pd
from datetime import date

# ================= TRYB PRZERWY TECHNICZNEJ =================
PRZERWA_TECHNICZNA = False

if PRZERWA_TECHNICZNA:
    st.warning("⚠️ **Przerwa techniczna!** System Librus jest obecnie niedostępny z powodu prac konserwacyjnych. Zapraszamy w godzinach od 12:00 do 14:00.")
    st.stop()
# =============================================================

st.set_page_config(page_title="Synergia - Dziennik Elektroniczny", layout="wide")

# Zaawansowany styl 1:1 przypominający Librus Synergia
st.markdown("""
    <style>
    .librus-header-main {
        background: linear-gradient(135deg, #e4efe9 0%, #c4d7cd 100%);
        padding: 10px 20px;
        border: 1px solid #b2c9bd;
        border-radius: 3px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .librus-logo-text {
        font-size: 24px;
        font-weight: bold;
        color: #6b2d5c;
        font-family: Arial, sans-serif;
    }
    .librus-subbar {
        background-color: #f0f4f1;
        padding: 5px 12px;
        border-left: 4px solid #6b2d5c;
        font-size: 12px;
        margin-bottom: 15px;
        color: #333;
    }
    .grade-badge {
        display: inline-block;
        padding: 2px 8px;
        margin: 2px;
        border-radius: 3px;
        font-weight: bold;
        font-size: 12px;
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
        border-radius: 3px;
        font-size: 11px;
        padding: 4px 6px;
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

conn = sqlite3.connect("dziennik_szkolny.db", check_same_thread=False)
c = conn.cursor()

# Inicjalizacja tabel (tworzy tylko wtedy, gdy jeszcze ich nie ma — NIE nadpisuje istniejących danych)
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
conn.commit()

# Bezpieczna migracja kolumn dla istniejących baz
migracje = [
    ("oceny", "kategoria", "TEXT"),
    ("oceny", "komentarz", "TEXT"),
    ("uzytkownicy", "klasa", "TEXT"),
    ("uzytkownicy", "powiazany_uczen", "TEXT")
]
for tabela, kolumna, typ in migracje:
    try:
        c.execute(f"ALTER TABLE {tabela} ADD COLUMN {kolumna} {typ}")
        conn.commit()
    except sqlite3.OperationalError:
        pass

# Dane startowe uruchamiane TYLKO w przypadku pustej bazy
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
    st.session_state["librus_aktywna_zakladka"] = "Interfejs"

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
        wybrana_klasa = st.selectbox("Wybierz klasę do wyświetlenia planu:", klasy_baza, index=klasy_baza.index(docelowa_klasa), key=f"sel_plan_{docelowa_klasa}")
    else:
        wybrana_klasa = docelowa_klasa
        st.markdown(f"#### Klasa ucznia: **{wybrana_klasa}**")

    st.markdown(f"### Plan lekcji — Klasa: **{wybrana_klasa}**")
    df_p = pd.read_sql("SELECT dzien, nr_lekcji, przedmiot FROM plan_lekcji WHERE klasa = ?", conn, params=(wybrana_klasa,))
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
    
    c.execute("SELECT DISTINCT przedmiot FROM plan_lekcji WHERE klasa = ?", (klasa_ucznia,))
    przedmioty_klasy = [row[0] for row in c.fetchall()]
    if not przedmioty_klasy:
        przedmioty_klasy = ["Plastyka", "Matematyka"]

    st.markdown(f"### Oceny bieżące i szczegóły (Klasa: {klasa_ucznia})")
    tabela_dane = []
    for przedm in przedmioty_klasy:
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
            okres_1_html = '<span style="color: gray; font-size: 12px;">Brak ocen</span>'
            
        tabela_dane.append({
            "Przedmiot": przedm,
            "Oceny bieżące": okres_1_html,
            "Średnia": srednia_p
        })
    df_librus = pd.DataFrame(tabela_dane)
    st.write(df_librus.to_html(escape=False, index=False), unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("Szczegóły ocen")
    df_szczegoly = pd.read_sql("SELECT data as [Data], przedmiot as [Przedmiot], ocena as [Ocena], kategoria as [Kategoria], waga as [Waga], komentarz as [Komentarz] FROM oceny WHERE uczen = ?", conn, params=(imie_ucznia,))
    if not df_szczegoly.empty:
        st.dataframe(df_szczegoly, use_container_width=True, hide_index=True)
    else:
        st.info("Brak szczegółów ocen.")

def renderuj_zakladke_wiadomosci(aktualny_uzytkownik):
    st.subheader("Skrzynka wiadomości")
    c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE imie_nazwisko != ?", (aktualny_uzytkownik,))
    osoby = [o[0] for o in c.fetchall()]
    
    with st.form("form_wyslij_wiadomosc"):
        st.write("### Nowa wiadomość")
        odb = st.selectbox("Do:", osoby if osoby else ["Brak"])
        temat = st.text_input("Temat:")
        tresc = st.text_area("Treść:")
        if st.form_submit_button("Wyślij wiadomość", type="primary"):
            if odb and odb != "Brak":
                c.execute("INSERT INTO wiadomosci (nadawca, odbiorca, temat, tresc, data) VALUES (?, ?, ?, ?, ?)",
                          (aktualny_uzytkownik, odb, temat, tresc, str(date.today())))
                conn.commit()
                st.success("Wiadomość została wysłana!")
                st.rerun()

    st.markdown("---")
    st.subheader("Otrzymane wiadomości")
    df_msg = pd.read_sql("SELECT id, nadawca as [Od], temat as [Temat], tresc as [Treść], data as [Data] FROM wiadomosci WHERE odbiorca = ? ORDER BY id DESC", conn, params=(aktualny_uzytkownik,))
    
    if not df_msg.empty:
        for idx, row in df_msg.iterrows():
            with st.container():
                st.markdown(f"""
                    <div style="background-color: #f8f9fa; padding: 10px; border-left: 4px solid #6b2d5c; border-radius: 3px; margin-bottom: 10px;">
                        <b>Od: {row['Od']}</b> | <i>Data: {row['Data']}</i><br>
                        <b>Temat: {row['Temat']}</b><br>
                        <p style="margin-top: 5px;">{row['Treść']}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                col_btn_del, _ = st.columns([1, 4])
                with col_btn_del:
                    if st.button("🗑️ Usuń", key=f"del_msg_{row['id']}"):
                        c.execute("DELETE FROM wiadomosci WHERE id = ?", (row['id'],))
                        conn.commit()
                        st.success("Wiadomość została usunięta!")
                        st.rerun()
    else:
        st.info("Brak wiadomości w skrzynce odbiorczej.")

# ================= EKRAN LOGOWANIA =================
if st.session_state["dziennik_user"] is None:
    st.markdown("""
        <div style="text-align: center; padding: 40px 10px;">
            <h1 style="color: #6b2d5c; font-size: 38px;">Synergia <b>Librus</b></h1>
            <p style="color: gray; font-size: 14px;">Zdalny Dziennik Szkolny</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.3, 1])
    with col2:
        with st.form("form_logowania"):
            st.subheader("Logowanie do systemu")
            login_in = st.text_input("Login:")
            haslo_in = st.text_input("Hasło:", type="password")
            btn_log = st.form_submit_button("Zaloguj się", type="primary", use_container_width=True)
            
            if btn_log:
                c.execute("SELECT imie_nazwisko, rola, login FROM uzytkownicy WHERE login = ? AND haslo = ?", (login_in, haslo_in))
                res = c.fetchone()
                if res:
                    if res[2] == "brak":
                        st.error("To konto ucznia nie ma jeszcze aktywnego loginu (brak dostępu). Skontaktuj się z administratorem.")
                    else:
                        st.session_state["dziennik_user"] = res[0]
                        st.session_state["dziennik_rola"] = res[1]
                        st.success("Zalogowano pomyślnie!")
                        st.rerun()
                else:
                    st.error("Błędny login lub hasło!")
    st.stop()

# ================= NAGŁÓWEK SYSTEMOWY LIBRUS =================
st.markdown("""
    <div class="librus-header-main">
        <div class="librus-logo-text">Synergia <sub>Librus</sub></div>
        <div style="font-size: 12px; color: #555;">ostatnie logowanie: 2026-09-25 12:40</div>
    </div>
""", unsafe_allow_html=True)

cols_ikony = st.columns(9)
with cols_ikony[0]:
    if st.button("🏠 Interfejs", use_container_width=True):
        st.session_state["librus_aktywna_zakladka"] = "Interfejs"
        st.rerun()
with cols_ikony[1]:
    if st.button("📖 Lekcja", use_container_width=True):
        st.session_state["librus_aktywna_zakladka"] = "Realizacja"
        st.rerun()
with cols_ikony[2]:
    if st.button("📊 Oceny", use_container_width=True):
        st.session_state["librus_aktywna_zakladka"] = "Oceny"
        st.rerun()
with cols_ikony[3]:
    if st.button("⚠️ Uwagi", use_container_width=True):
        st.session_state["librus_aktywna_zakladka"] = "Uwagi"
        st.rerun()
with cols_ikony[4]:
    if st.button("📋 Frekwencja", use_container_width=True):
        st.session_state["librus_aktywna_zakladka"] = "Frekwencja"
        st.rerun()
with cols_ikony[5]:
    if st.button("✉️ Wiadomości", use_container_width=True):
        st.session_state["librus_aktywna_zakladka"] = "Wiadomości"
        st.rerun()
with cols_ikony[6]:
    if st.button("📅 Plan/Zast.", use_container_width=True):
        st.session_state["librus_aktywna_zakladka"] = "Plan"
        st.rerun()
with cols_ikony[7]:
    if st.button("⚙️ Ustawienia", use_container_width=True):
        st.session_state["librus_aktywna_zakladka"] = "Ustawienia"
        st.rerun()
with cols_ikony[8]:
    if st.button("🚪 Wyloguj", use_container_width=True):
        st.session_state["dziennik_user"] = None
        st.session_state["dziennik_rola"] = None
        st.rerun()

st.markdown(f"""
    <div class="librus-subbar" style="margin-top: 10px;">
        Aktywny moduł Librus: <b>{st.session_state['librus_aktywna_zakladka']}</b> | Zalogowany użytkownik: <b>{st.session_state['dziennik_user']}</b> ({st.session_state['dziennik_rola']})
    </div>
""", unsafe_allow_html=True)

st.divider()

akt_zakl = st.session_state["librus_aktywna_zakladka"]
rola = st.session_state["dziennik_rola"]
user = st.session_state["dziennik_user"]

# ================= OBSŁUGA ZAKŁADKI USTAWIENIA =================
if akt_zakl == "Ustawienia":
    st.subheader("Ustawienia konta — Zmiana hasła")
    with st.form("form_zmien_haslo"):
        st_haslo_stare = st.text_input("Aktualne hasło:", type="password")
        st_haslo_nowe = st.text_input("Nowe hasło:", type="password")
        st_haslo_nowe_powt = st.text_input("Powtórz nowe hasło:", type="password")
        if st.form_submit_button("Zmień hasło", type="primary"):
            c.execute("SELECT haslo FROM uzytkownicy WHERE imie_nazwisko = ?", (user,))
            db_haslo = c.fetchone()[0]
            if st_haslo_stare != db_haslo:
                st.error("Podane aktualne hasło jest niepoprawne!")
            elif st_haslo_nowe != st_haslo_nowe_powt:
                st.error("Nowe hasła nie zgadzają się!")
            else:
                c.execute("UPDATE uzytkownicy SET haslo = ? WHERE imie_nazwisko = ?", (st_haslo_nowe, user))
                conn.commit()
                st.success("Hasło zostało pomyślnie zmienione!")

# ================= PANEL ADMINISTRATORA =================
elif rola == "Admin":
    st.subheader("Panel Administratora")
    adm_tab1, adm_tab2, adm_tab3, adm_tab4, adm_tab5, adm_tab6, adm_tab7 = st.tabs(["Zastępstwa / Odwołania", "Oceny Zachowania", "Użytkownicy", "Przypisania", "📅 Plan lekcji", "🛡️ Dyżury", "Wiadomości"])
    
    with adm_tab1:
        st.subheader("Zarządzanie Zastępstwami i Odwołaniami Lekcji")
        
        tryb_zast = st.radio("Wybierz akcję:", ["Dodaj zastępstwo / odwołanie", "Usuń zastępstwo / odwołanie"], horizontal=True)
        
        if tryb_zast == "Dodaj zastępstwo / odwołanie":
            with st.form("form_zastepstwo_adm"):
                z_data = st.date_input("Data:", value=date.today())
                z_klasa = st.text_input("Klasa (np. 1c):", value="1c")
                z_nr = st.selectbox("Nr lekcji:", PELNE_GODZINY_LEKCYJNE)
                z_stary = st.text_input("Stary przedmiot (z planu):")
                
                typ_zmiany = st.selectbox("Rodzaj zmiany:", ["Zastępstwo / Zmiana przedmiotu", "🚫 Odwołanie lekcji"])
                
                if typ_zmiany == "🚫 Odwołanie lekcji":
                    z_nowy = "Lekcja odwołana"
                    z_nauczyciel = "-"
                    z_info = st.text_input("Informacja o odwołaniu (np. Nieobecność nauczyciela):", value="Lekcja odwołana")
                else:
                    z_nowy = st.text_input("Nowy przedmiot:")
                    z_nauczyciel = st.text_input("Zastępujący nauczyciel:")
                    z_info = st.text_input("Informacja / Komentarz:")
                    
                if st.form_submit_button("Zapisz w systemiue", type="primary"):
                    c.execute("INSERT INTO zastepstwa (data, klasa, nr_lekcji, stary_przedmiot, nowy_przedmiot, nauczyciel, informacja) VALUES (?, ?, ?, ?, ?, ?, ?)",
                              (str(z_data), z_klasa, z_nr, z_stary, z_nowy, z_nauczyciel, z_info))
                    conn.commit()
                    st.success("Zapisano wpis w systemie!")
                    st.rerun()
        else:
            df_zast_all = pd.read_sql("SELECT id, data as [Data], klasa as [Klasa], nr_lekcji as [Lekcja], nowy_przedmiot as [Zmiana], informacja as [Info] FROM zastepstwa", conn)
            if not df_zast_all.empty:
                st.dataframe(df_zast_all, use_container_width=True, hide_index=True)
                with st.form("form_usun_zastepstwo"):
                    id_zast_del = st.selectbox("Wybierz ID wpisu do usunięcia (cofnięcie odwołania/zastępstwa):", df_zast_all["id"].tolist())
                    if st.form_submit_button("Usuń wpis / Przywróć plan", type="primary"):
                        c.execute("DELETE FROM zastepstwa WHERE id = ?", (id_zast_del,))
                        conn.commit()
                        st.success("Usunięto wpis! Przywrócono pierwotny stan lekcji.")
                        st.rerun()
            else:
                st.info("Brak aktywnych zastępstw lub odwołań w bazie.")

    with adm_tab2:
        st.subheader("Zarządzanie Ocenami z Zachowania")
        with st.form("form_dodaj_zachowanie"):
            c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE rola = 'Uczeń'")
            uczniowie_l = [u[0] for u in c.fetchall()]
            z_uczen = st.selectbox("Uczeń:", uczniowie_l if uczniowie_l else ["Brak"])
            z_okres = st.selectbox("Okres:", ["I okres", "II okres", "Roczna"])
            z_ocena_z = st.selectbox("Ocena z zachowania:", ["Wzorowe", "Bardzo dobre", "Dobre", "Poprawne", "Nieodpowiednie", "Naganne"])
            z_opis = st.text_area("Uzasadnienie / Opis:")
            if st.form_submit_button("Dodaj ocenę z zachowania", type="primary"):
                if z_uczen != "Brak":
                    c.execute("INSERT INTO oceny_zachowania (uczen, okres, ocena, opis) VALUES (?, ?, ?, ?)", (z_uczen, z_okres, z_ocena_z, z_opis))
                    conn.commit()
                    st.success("Dodano ocenę z zachowania!")
                    st.rerun()

        st.markdown("---")
        st.write("### Usuwanie ocen z zachowania")
        df_zach_all = pd.read_sql("SELECT id, uczen as [Uczeń], okres as [Okres], ocena as [Ocena] FROM oceny_zachowania", conn)
        if not df_zach_all.empty:
            st.dataframe(df_zach_all, use_container_width=True, hide_index=True)
            with st.form("form_usun_zachowanie"):
                id_zach_del = st.selectbox("Wybierz ID wpisu do usunięcia:", df_zach_all["id"].tolist())
                if st.form_submit_button("Usuń ocenę z zachowania", type="primary"):
                    c.execute("DELETE FROM oceny_zachowania WHERE id = ?", (id_zach_del,))
                    conn.commit()
                    st.success("Usunięto wpis!")
                    st.rerun()
        else:
            st.info("Brak ocen z zachowania w bazie.")

    with adm_tab3:
        st.subheader("Zarządzanie Użytkownikami")
        sub_adm_t1, sub_adm_t2, sub_adm_t3 = st.tabs(["➕ Dodaj użytkownika", "✏️ Edytuj użytkownika", "🗑️ Usuń użytkownika"])
        
        c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE rola = 'Uczeń'")
        uczniowie_baza = [u[0] for u in c.fetchall()]
        if not uczniowie_baza:
            uczniowie_baza = ["Brak uczniów"]

        with sub_adm_t1:
            with st.form("form_dodaj_uzytkownika"):
                d_imie = st.text_input("Imię i nazwisko:")
                d_login = st.text_input("Login (wpisz 'brak' jeśli uczeń nie ma mieć loginu):", value="brak")
                d_haslo = st.text_input("Hasło:", value="brak", type="password")
                d_rola = st.selectbox("Rola:", ["Admin", "Nauczyciel", "Uczeń", "Rodzic"])
                d_klasa = st.text_input("Klasa (np. 1c lub '-' dla Admina):", value="1c")
                d_powiazany = st.selectbox("Powiązany uczeń (dla Rodzica):", ["-"] + uczniowie_baza)
                
                if st.form_submit_button("Dodaj użytkownika", type="primary"):
                    try:
                        c.execute("INSERT INTO uzytkownicy (imie_nazwisko, login, haslo, rola, klasa, powiazany_uczen) VALUES (?, ?, ?, ?, ?, ?)",
                                  (d_imie, d_login, d_haslo, d_rola, d_klasa, d_powiazany))
                        conn.commit()
                        st.success(f"Dodano użytkownika {d_imie}!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Użytkownik o takim loginie już istnieje!")

        with sub_adm_t2:
            c.execute("SELECT id, imie_nazwisko FROM uzytkownicy")
            wszyscy_u = c.fetchall()
            u_slownik = {f"{u[1]} (ID: {u[0]})": u[0] for u in wszyscy_u}
            
            if u_slownik:
                wybrany_do_edycji_str = st.selectbox("Wybierz użytkownika do edycji:", list(u_slownik.keys()))
                ed_id = u_slownik[wybrany_do_edycji_str]
                
                c.execute("SELECT imie_nazwisko, login, haslo, rola, klasa, powiazany_uczen FROM uzytkownicy WHERE id = ?", (ed_id,))
                dane_u = c.fetchone()
                
                with st.form("form_edytuj_uzytkownika"):
                    ed_imie = st.text_input("Imię i nazwisko:", value=dane_u[0])
                    ed_login = st.text_input("Login (wpisz 'brak', aby zablokować logowanie):", value=dane_u[1])
                    ed_haslo = st.text_input("Hasło:", value=dane_u[2])
                    role_lista = ["Admin", "Nauczyciel", "Uczeń", "Rodzic"]
                    ed_rola = st.selectbox("Rola:", role_lista, index=role_lista.index(dane_u[3]) if dane_u[3] in role_lista else 0)
                    ed_klasa = st.text_input("Klasa:", value=dane_u[4])
                    
                    akt_pow = dane_u[5]
                    opcje_pow = ["-"] + uczniowie_baza
                    idx_pow = opcje_pow.index(akt_pow) if akt_pow in opcje_pow else 0
                    ed_powiazany = st.selectbox("Powiązany uczeń (dla Rodzica):", opcje_pow, index=idx_pow)
                    
                    if st.form_submit_button("Zapisz zmiany", type="primary"):
                        c.execute("UPDATE uzytkownicy SET imie_nazwisko = ?, login = ?, haslo = ?, rola = ?, klasa = ?, powiazany_uczen = ? WHERE id = ?",
                                  (ed_imie, ed_login, ed_haslo, ed_rola, ed_klasa, ed_powiazany, ed_id))
                        conn.commit()
                        st.success("Zaktualizowano dane użytkownika!")
                        st.rerun()
            else:
                st.info("Brak użytkowników.")

        with sub_adm_t3:
            df_u_del = pd.read_sql("SELECT id, imie_nazwisko as [Imię i Nazwisko], login as [Login], rola as [Rola] FROM uzytkownicy", conn)
            st.dataframe(df_u_del, use_container_width=True, hide_index=True)
            with st.form("form_usun_uzytkownika"):
                id_u_del = st.selectbox("Wybierz ID użytkownika do usunięcia:", df_u_del["id"].tolist() if not df_u_del.empty else [0])
                if st.form_submit_button("Usuń użytkownika", type="primary"):
                    if id_u_del > 1:
                        c.execute("DELETE FROM uzytkownicy WHERE id = ?", (id_u_del,))
                        conn.commit()
                        st.success("Usunięto użytkownika!")
                        st.rerun()
                    else:
                        st.error("Nie można usunąć głównego administratora systemowego (ID 1)!")

    with adm_tab4:
        st.subheader("Przypisanie nauczyciela do przedmiotu i klasy")
        with st.form("form_przypisz_nauczyciela"):
            c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE rola = 'Nauczyciel'")
            nauczyciele_l = [n[0] for n in c.fetchall()]
            
            c.execute("SELECT nazwa_klasy FROM klasy")
            klasy_l = [k[0] for k in c.fetchall()]
            
            p_nauczyciel = st.selectbox("Nauczyciel:", nauczyciele_l if nauczyciele_l else ["Brak"])
            p_przedmiot = st.selectbox("Przedmiot:", WSZYSTKIE_PRZEDMIOTY)
            p_klasa = st.selectbox("Klasa:", klasy_l if klasy_l else ["1c"])
            
            if st.form_submit_button("Przypisz przedmiot", type="primary"):
                if p_nauczyciel != "Brak":
                    c.execute("INSERT INTO przypisania (nauczyciel, przedmiot, klasa) VALUES (?, ?, ?)", (p_nauczyciel, p_przedmiot, p_klasa))
                    conn.commit()
                    st.success("Przypisano przedmiot i nauczyciela do klasy!")
                    st.rerun()
                    
        st.markdown("---")
        st.write("### Aktualne przypisania")
        df_przypisania = pd.read_sql("SELECT id, nauczyciel as [Nauczyciel], przedmiot as [Przedmiot], klasa as [Klasa] FROM przypisania", conn)
        if not df_przypisania.empty:
            st.dataframe(df_przypisania, use_container_width=True, hide_index=True)
            with st.form("form_usun_przypisanie"):
                id_prz_del = st.selectbox("Wybierz ID przypisania do usunięcia:", df_przypisania["id"].tolist())
                if st.form_submit_button("Usuń przypisanie", type="primary"):
                    c.execute("DELETE FROM przypisania WHERE id = ?", (id_prz_del,))
                    conn.commit()
                    st.success("Usunięto przypisanie!")
                    st.rerun()
        else:
            st.info("Brak przypisań w bazie.")

    with adm_tab5:
        st.subheader("Zarządzanie Planem Lekcji")
        with st.form("form_dodaj_plan_lekcji"):
            c.execute("SELECT nazwa_klasy FROM klasy")
            klasy_p_l = [k[0] for k in c.fetchall()]
            
            pl_klasa = st.selectbox("Klasa:", klasy_p_l if klasy_p_l else ["1c"])
            pl_dzien = st.selectbox("Dzień tygodnia:", DNI_TYGODNIA)
            pl_nr = st.selectbox("Numer i godzina lekcji:", PELNE_GODZINY_LEKCYJNE)
            pl_przedmiot = st.selectbox("Przedmiot:", WSZYSTKIE_PRZEDMIOTY)
            
            if st.form_submit_button("Dodaj lekcję do planu", type="primary"):
                c.execute("INSERT INTO plan_lekcji (klasa, dzien, nr_lekcji, przedmiot) VALUES (?, ?, ?, ?)",
                          (pl_klasa, pl_dzien, pl_nr, pl_przedmiot))
                conn.commit()
                st.success("Dodano lekcję do planu!")
                st.rerun()
                
        st.markdown("---")
        st.write("### Usuwanie wpisów z planu lekcji")
        df_plan_all = pd.read_sql("SELECT id, klasa as [Klasa], dzien as [Dzień], nr_lekcji as [Lekcja], przedmiot as [Przedmiot] FROM plan_lekcji", conn)
        if not df_plan_all.empty:
            st.dataframe(df_plan_all, use_container_width=True, hide_index=True)
            with st.form("form_usun_plan_wpis"):
                id_pl_del = st.selectbox("Wybierz ID wpisu do usunięcia:", df_plan_all["id"].tolist())
                if st.form_submit_button("Usuń wpis", type="primary"):
                    c.execute("DELETE FROM plan_lekcji WHERE id = ?", (id_pl_del,))
                    conn.commit()
                    st.success("Usunięto wpis z planu!")
                    st.rerun()
        else:
            st.info("Brak wpisów w planie lekcji.")

    with adm_tab6:
        st.subheader("Zarządzanie Dyżurami Nauczycieli")
        with st.form("form_dodaj_dyzur"):
            c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE rola = 'Nauczyciel'")
            nauczyciele_l = [n[0] for n in c.fetchall()]
            dyz_osoba = st.selectbox("Nauczyciel:", nauczyciele_l if nauczyciele_l else ["Olivier"])
            dyz_miejsce = st.text_input("Miejsce dyżuru (np. Parter — Wejście główne):")
            dyz_dzien = st.selectbox("Dzień:", DNI_TYGODNIA)
            dyz_godzina = st.text_input("Godzina / Przerwa (np. Przerwa 09:40 - 09:50):")
            
            if st.form_submit_button("Dodaj dyżur", type="primary"):
                c.execute("INSERT INTO dyzury (osoba, miejsce, dzien, godzina) VALUES (?, ?, ?, ?)",
                          (dyz_osoba, dyz_miejsce, dyz_dzien, dyz_godzina))
                conn.commit()
                st.success("Dodano dyżur!")
                st.rerun()

        st.markdown("---")
        st.write("### Aktualne dyżury")
        df_dyz_all = pd.read_sql("SELECT id, osoba as [Nauczyciel], miejsce as [Miejsce], dzien as [Dzień], godzina as [Godzina] FROM dyzury", conn)
        if not df_dyz_all.empty:
            st.dataframe(df_dyz_all, use_container_width=True, hide_index=True)
            with st.form("form_usun_dyzur"):
                id_dyz_del = st.selectbox("Wybierz ID dyżuru do usunięcia:", df_dyz_all["id"].tolist())
                if st.form_submit_button("Usuń dyżur", type="primary"):
                    c.execute("DELETE FROM dyzury WHERE id = ?", (id_dyz_del,))
                    conn.commit()
                    st.success("Usunięto dyżur!")
                    st.rerun()
        else:
            st.info("Brak zdefiniowanych dyżurów.")

    with adm_tab7:
        renderuj_zakladke_wiadomosci("Administrator")

# ================= PANEL NAUCZYCIELA =================
elif rola == "Nauczyciel":
    if akt_zakl == "Interfejs" or akt_zakl == "Realizacja":
        st.markdown("### Realizacja programu nauczania — Dziennik lekcyjny i Frekwencja")
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            data_lekcji = st.date_input("Data lekcji:", value=date.today(), key="in_data_lekcji")
        with col_d2:
            klasa_wyb = st.selectbox("Klasa:", ["1c"], key="in_klasa_lekcji")
            
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            nr_jednostki = st.selectbox("Nr lekcji / Godzina:", PELNE_GODZINY_LEKCYJNE, key="in_nr_lekcji")
        with col_l2:
            przedmiot_wyb = st.selectbox("Przedmiot z planu:", WSZYSTKIE_PRZEDMIOTY, key="in_przedmiot_lekcji")
            
        def update_temat():
            st.session_state["lekcja_temat"] = st.session_state["widget_temat_input"]

        temat_lekcji = st.text_input(
            "Temat lekcji:", 
            value=st.session_state["lekcja_temat"], 
            key="widget_temat_input", 
            on_change=update_temat
        )
        st.session_state["lekcja_temat"] = temat_lekcji
        
        st.markdown("---")
        st.markdown("### Sprawdź obecność uczniów na klasie")
        
        c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE klasa = ? AND rola = 'Uczeń'", (klasa_wyb,))
        uczniowie_klas = c.fetchall()
        
        frekwencja_wyniki = {}
        if uczniowie_klas:
            for idx, uczen in enumerate(uczniowie_klas, 1):
                col_u_name, col_u_radio = st.columns([2, 5])
                with col_u_name:
                    st.write(f"{idx}. {uczen[0]}")
                with col_u_radio:
                    status = st.radio(
                        f"st_{uczen[0]}", 
                        ["ob", "nb", "u", "sp", "zw"], 
                        horizontal=True, 
                        label_visibility="collapsed", 
                        key=f"radio_freq_{uczen[0]}"
                    )
                    frekwencja_wyniki[uczen[0]] = status
        else:
            st.info("Brak uczniów w tej klasie.")
            
        st.markdown("")
        if st.button("Zapisz lekcję i frekwencję", type="primary"):
            for uczen, status in frekwencja_wyniki.items():
                c.execute("INSERT INTO frekwencja (uczen, data, lekcja, status) VALUES (?, ?, ?, ?)",
                          (uczen, str(data_lekcji), nr_jednostki, status))
            conn.commit()
            st.success("Zapisano lekcję i frekwencję pomyślnie! Temat zapamiętany w dzienniku.")

    elif akt_zakl == "Oceny":
        st.markdown("### Dziennik Ocen — Zarządzanie ocenami z przedmiotu")
        
        col_op1, col_op2 = st.columns(2)
        with col_op1:
            wybrany_przedmiot = st.selectbox("Wybierz przedmiot:", WSZYSTKIE_PRZEDMIOTY)
        with col_op2:
            c.execute("SELECT nazwa_klasy FROM klasy")
            klasy_baza = [k[0] for k in c.fetchall()]
            wybrana_klasa = st.selectbox("Wybierz klasę:", klasy_baza if klasy_baza else ["1c"])

        st.markdown("---")
        nauczyciel_tabs = st.tabs(["📋 Widok tabeli ocen (Librus)", "➕ Wystaw nową ocenę", "✏️ Edytuj / Popraw / Usuń ocenę"])

        with nauczyciel_tabs[0]:
            st.subheader(f"Tabela ocen z przedmiotu: {wybrany_przedmiot} (Klasa: {wybrana_klasa})")
            c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE klasa = ? AND rola = 'Uczeń'", (wybrana_klasa,))
            uczniowie_klasy = c.fetchall()
            
            if uczniowie_klasy:
                tabela_wiersze = []
                for idx, uczen_row in enumerate(uczniowie_klasy, 1):
                    u_nazwisko = uczen_row[0]
                    df_oceny_u = pd.read_sql("SELECT ocena FROM oceny WHERE uczen = ? AND przedmiot = ?", conn, params=(u_nazwisko, wybrany_przedmiot))
                    
                    if not df_oceny_u.empty:
                        badge_list = []
                        for r in df_oceny_u.itertuples():
                            v_str = str(r.ocena)
                            cls = f"g-{v_str}" if v_str in ["0", "1", "2", "3", "4", "5", "6"] else "g-np"
                            badge_list.append(f'<span class="grade-badge {cls}">{v_str}</span>')
                        badge_str = " ".join(badge_list)
                    else:
                        badge_str = '<span style="color: gray;">Brak ocen</span>'
                        
                    tabela_wiersze.append({
                        "Nr": idx,
                        "Nazwisko i imię": u_nazwisko,
                        "Oceny bieżące": badge_str
                    })
                df_widok = pd.DataFrame(tabela_wiersze)
                st.write(df_widok.to_html(escape=False, index=False), unsafe_allow_html=True)
            else:
                st.info("Brak uczniów w wybranej klasie.")

        with nauczyciel_tabs[1]:
            st.subheader("Wystawianie oceny")
            with st.form("form_wystaw_ocene_librus"):
                c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE klasa = ? AND rola = 'Uczeń'", (wybrana_klasa,))
                uczniowie_l = [u[0] for u in c.fetchall()]
                
                row_o1, row_o2, row_o3 = st.columns(3)
                with row_o1:
                    uczen_docelowy = st.selectbox("Uczeń:", uczniowie_l if uczniowie_l else ["Brak"])
                with row_o2:
                    ocena_val = st.selectbox("Ocena:", ["0", "1", "2", "3", "4", "5", "6", "np"], index=5)
                with row_o3:
                    data_oceny = st.date_input("Data oceny:", value=date.today())
                    
                row_o4, row_o5 = st.columns(2)
                with row_o4:
                    kategoria_val = st.selectbox("Kategoria:", KATEGORIE_OCEN, index=7)
                with row_o5:
                    waga_val = st.number_input("Waga:", min_value=1, max_value=10, value=5)
                    
                komentarz_val = st.text_area("Komentarz / Opis:")
                
                if st.form_submit_button("OK (Zapisz ocenę)", type="primary"):
                    if uczen_docelowy != "Brak":
                        c.execute("INSERT INTO oceny (uczen, przedmiot, ocena, waga, kategoria, data, komentarz) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                  (uczen_docelowy, wybrany_przedmiot, ocena_val, waga_val, kategoria_val, str(data_oceny), komentarz_val))
                        conn.commit()
                        st.success("Wystawiono ocenę pomyślnie!")
                        st.rerun()

        with nauczyciel_tabs[2]:
            st.subheader("Edycja, poprawa lub usuwanie istniejących ocen")
            df_wszystkie_oceny = pd.read_sql("SELECT id, uczen as [Uczeń], przedmiot as [Przedmiot], ocena as [Ocena], kategoria as [Kategoria], data as [Data], komentarz as [Komentarz] FROM oceny WHERE przedmiot = ?", conn, params=(wybrany_przedmiot,))
            
            if not df_wszystkie_oceny.empty:
                st.dataframe(df_wszystkie_oceny, use_container_width=True, hide_index=True)
                
                wybrane_id_oceny = st.selectbox("Wybierz ID oceny do edycji / usunięcia:", df_wszystkie_oceny["id"].tolist())
                
                c.execute("SELECT uczen, przedmiot, ocena, waga, kategoria, data, komentarz FROM oceny WHERE id = ?", (wybrane_id_oceny,))
                wybrana_o_dane = c.fetchone()
                
                if wybrana_o_dane:
                    with st.form("form_edytuj_ocene_dokladnie"):
                        st.write(f"**Uczeń:** {wybrana_o_dane[0]} | **Przedmiot:** {wybrana_o_dane[1]}")
                        e_kat = st.selectbox("Kategoria:", KATEGORIE_OCEN, index=KATEGORIE_OCEN.index(wybrana_o_dane[4]) if wybrana_o_dane[4] in KATEGORIE_OCEN else 0)
                        
                        mozliwe_oceny = ["0", "1", "2", "3", "4", "5", "6", "np"]
                        akt_ocena_str = str(wybrana_o_dane[2])
                        idx_oceny = mozliwe_oceny.index(akt_ocena_str) if akt_ocena_str in mozliwe_oceny else 5
                        
                        e_ocena = st.selectbox("Ocena:", mozliwe_oceny, index=idx_oceny)
                        e_waga = st.number_input("Waga:", min_value=1, max_value=10, value=int(wybrana_o_dane[3]))
                        e_komentarz = st.text_area("Komentarz:", value=wybrana_o_dane[6] if wybrana_o_dane[6] else "")
                        
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            btn_zapisz_zmiany = st.form_submit_button("💾 Popraw / Zapisz zmiany", type="primary")
                        with col_btn2:
                            btn_usun_ocene = st.form_submit_button("🗑️ Usuń ocenę")
                            
                        if btn_zapisz_zmiany:
                            c.execute("UPDATE oceny SET kategoria = ?, ocena = ?, waga = ?, komentarz = ? WHERE id = ?",
                                      (e_kat, e_ocena, e_waga, e_komentarz, wybrane_id_oceny))
                            conn.commit()
                            st.success("Zaktualizowano ocenę pomyślnie!")
                            st.rerun()
                            
                        if btn_usun_ocene:
                            c.execute("DELETE FROM oceny WHERE id = ?", (wybrane_id_oceny,))
                            conn.commit()
                            st.success("Usunięto ocenę pomyślnie!")
                            st.rerun()
            else:
                st.info(f"Brak ocen z przedmiotu {wybrany_przedmiot}.")

    elif akt_zakl == "Uwagi":
        st.subheader("Wpisywanie uwag (w tym tryb seryjny)")
        
        tryb_uwag = st.radio("Wybierz tryb wpisywania uwag:", ["Pojedyncza uwaga", "Seryjne dodawanie uwag dla całej klasy"], horizontal=True)
        
        if tryb_uwag == "Pojedyncza uwaga":
            with st.form("form_uwaga_pojedyncza"):
                c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE rola = 'Uczeń'")
                uczniowie_l = [u[0] for u in c.fetchall()]
                uw_uczen = st.selectbox("Uczeń:", uczniowie_l if uczniowie_l else ["Emilia Widomska"])
                uw_typ = st.selectbox("Typ:", ["Pozytywna", "Neutralna", "Negatywna"])
                uw_tresc = st.text_area("Treść uwagi:")
                if st.form_submit_button("Dodaj uwagę", type="primary"):
                    c.execute("INSERT INTO uwagi (uczen, nauczyciel, typ, tresc, data) VALUES (?, ?, ?, ?, ?)",
                              (uw_uczen, user, uw_typ, uw_tresc, str(date.today())))
                    conn.commit()
                    st.success("Dodano uwagę!")
                    st.rerun()
        else:
            with st.form("form_uwaga_seryjna"):
                c.execute("SELECT nazwa_klasy FROM klasy")
                klasy_s_l = [k[0] for k in c.fetchall()]
                s_klasa = st.selectbox("Wybierz klasę do wpisów seryjnych:", klasy_s_l if klasy_s_l else ["1c"])
                
                s_typ = st.selectbox("Typ uwagi dla zaznaczonych:", ["Pozytywna", "Neutralna", "Negatywna"])
                s_tresc = st.text_area("Treść uwagi (wspólna):")
                
                c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE klasa = ? AND rola = 'Uczeń'", (s_klasa,))
                uczniowie_w_klasie = [u[0] for u in c.fetchall()]
                
                st.write("Zaznacz uczniów, którym chcesz dopisać powyższą uwagę:")
                zaznaczeni_uczniowie = {}
                for uczen in uczniowie_w_klasie:
                    zaznaczeni_uczniowie[uczen] = st.checkbox(uczen, value=False, key=f"ser_uw_{uczen}")
                
                if st.form_submit_button("Wpisz seryjnie uwagi", type="primary"):
                    licznik = 0
                    for uczen, zaznaczony in zaznaczeni_uczniowie.items():
                        if zaznaczony and s_tresc.strip():
                            c.execute("INSERT INTO uwagi (uczen, nauczyciel, typ, tresc, data) VALUES (?, ?, ?, ?, ?)",
                                      (uczen, user, s_typ, s_tresc, str(date.today())))
                            licznik += 1
                    conn.commit()
                    if licznik > 0:
                        st.success(f"Dodano pomyślnie seryjne uwagi dla {licznik} uczniów!")
                        st.rerun()
                    else:
                        st.warning("Nie zaznaczono żadnego ucznia lub treść uwagi była pusta!")

    elif akt_zakl == "Wiadomości":
        renderuj_zakladke_wiadomosci(user)

    elif akt_zakl == "Plan":
        nauczyciel_plan_tabs = st.tabs(["📅 Plan lekcji (Klasy)", "🛡️ Dyżury nauczycieli"])
        with nauczyciel_plan_tabs[0]:
            renderuj_tabelue_planu_dla_klasy("1c", allow_change=True)
        with nauczyciel_plan_tabs[1]:
            st.subheader("Harmonogram dyżurów nauczycielskich")
            df_dyzury_n = pd.read_sql("SELECT osoba as [Nauczyciel], miejsce as [Miejsce], dzien as [Dzień], godzina as [Godzina] FROM dyzury", conn)
            if not df_dyzury_n.empty:
                st.dataframe(df_dyzury_n, use_container_width=True, hide_index=True)
            else:
                st.info("Brak zaplanowanych dyżurów.")
        
    elif akt_zakl == "Frekwencja":
        st.subheader("Zestawienie frekwencji")
        df_fr = pd.read_sql("SELECT uczen as [Uczeń], data as [Data], lekcja as [Lekcja], status as [Status] FROM frekwencja", conn)
        if not df_fr.empty:
            st.dataframe(df_fr, use_container_width=True, hide_index=True)
        else:
            st.info("Brak wpisów frekwencji.")

# ================= PANEL UCZNIA =================
elif rola == "Uczeń":
    c.execute("SELECT klasa FROM uzytkownicy WHERE imie_nazwisko = ?", (user,))
    res_ku = c.fetchone()
    klasa_ucz = res_ku[0] if res_ku and res_ku[0] != "-" else "1c"

    if akt_zakl == "Oceny" or akt_zakl == "Interfejs":
        renderuj_tabelue_ocen_dla_ucznia(user)
    elif akt_zakl == "Plan":
        renderuj_tabelue_planu_dla_klasy(klasa_ucz)
    elif akt_zakl == "Wiadomości":
        renderuj_zakladke_wiadomosci(user)
    elif akt_zakl == "Uwagi":
        st.subheader("Moje uwagi i zachowanie")
        df_uw = pd.read_sql("SELECT data as [Data], typ as [Typ], nauczyciel as [Nauczyciel], tresc as [Treść] FROM uwagi WHERE uczen = ?", conn, params=(user,))
        if not df_uw.empty:
            st.dataframe(df_uw, use_container_width=True, hide_index=True)
        else:
            st.info("Brak uwag.")
            
        st.markdown("---")
        st.subheader("Oceny z zachowania")
        df_oz = pd.read_sql("SELECT okres as [Okres], ocena as [Ocena], opis as [Opis] FROM oceny_zachowania WHERE uczen = ?", conn, params=(user,))
        if not df_oz.empty:
            st.dataframe(df_oz, use_container_width=True, hide_index=True)
        else:
            st.info("Brak ocen z zachowania.")
    elif akt_zakl == "Frekwencja":
        st.subheader("Moja frekwencja")
        df_f_ucz = pd.read_sql("SELECT data as [Data], lekcja as [Lekcja], status as [Status] FROM frekwencja WHERE uczen = ?", conn, params=(user,))
        if not df_f_ucz.empty:
            st.dataframe(df_f_ucz, use_container_width=True, hide_index=True)
        else:
            st.info("Brak wpisów frekwencji.")

# ================= PANEL RODZICA =================
elif rola == "Rodzic":
    c.execute("SELECT powiazany_uczen FROM uzytkownicy WHERE imie_nazwisko = ?", (user,))
    res_p = c.fetchone()
    dziecko = res_p[0] if res_p and res_p[0] != "-" else "Emilia Widomska"
    
    c.execute("SELECT klasa FROM uzytkownicy WHERE imie_nazwisko = ?", (dziecko,))
    res_kd = c.fetchone()
    klasa_dziecka = res_kd[0] if res_kd and res_kd[0] != "-" else "1c"
    
    st.subheader(f"Panel Rodzica — Podgląd dziecka: **{dziecko}**")
    
    if akt_zakl == "Oceny" or akt_zakl == "Interfejs":
        renderuj_tabelue_ocen_dla_ucznia(dziecko)
    elif akt_zakl == "Plan":
        renderuj_tabelue_planu_dla_klasy(klasa_dziecka)
    elif akt_zakl == "Uwagi":
        st.subheader(f"Uwagi o uczniu: {dziecko}")
        df_uw = pd.read_sql("SELECT data as [Data], typ as [Typ], nauczyciel as [Nauczyciel], tresc as [Treść] FROM uwagi WHERE uczen = ?", conn, params=(dziecko,))
        if not df_uw.empty:
            st.dataframe(df_uw, use_container_width=True, hide_index=True)
        else:
            st.info("Brak uwag.")
    elif akt_zakl == "Frekwencja":
        st.subheader(f"Frekwencja ucznia: {dziecko}")
        df_f_d = pd.read_sql("SELECT data as [Data], lekcja as [Lekcja], status as [Status] FROM frekwencja WHERE uczen = ?", conn, params=(dziecko,))
        if not df_f_d.empty:
            st.dataframe(df_f_d, use_container_width=True, hide_index=True)
        else:
            st.info("Brak wpisów frekwencji.")
    elif akt_zakl == "Wiadomości":
        renderuj_zakladke_wiadomosci(user)
