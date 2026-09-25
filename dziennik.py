import sqlite3
import streamlit as st
import pandas as pd
from datetime import date

# ================= TRYB PRZERWY TECHNICZNEJ =================
# Zmień na False, gdy chcesz odblokować aplikację dla użytkowników
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
    
    .uwaga-poz { background-color: #d4edda; color: #155724; padding: 6px; border-left: 4px solid #28a745; margin-bottom: 5px; border-radius: 3px; }
    .uwaga-neut { background-color: #e2e3e5; color: #383d41; padding: 6px; border-left: 4px solid #6c757d; margin-bottom: 5px; border-radius: 3px; }
    .uwaga-neg { background-color: #f8d7da; color: #721c24; padding: 6px; border-left: 4px solid #dc3545; margin-bottom: 5px; border-radius: 3px; }

    .zastepstwo-box { background-color: #fff3cd; color: #856404; padding: 8px; border-left: 4px solid #ffc107; margin-bottom: 5px; border-radius: 3px; font-size: 13px; }

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

# Inicjalizacja tabel
c.execute("CREATE TABLE IF NOT EXISTS uzytkownicy (id INTEGER PRIMARY KEY AUTOINCREMENT, imie_nazwisko TEXT, login TEXT UNIQUE, haslo TEXT, rola TEXT, klasa TEXT, powiazany_uczen TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS klasy (id INTEGER PRIMARY KEY AUTOINCREMENT, nazwa_klasy TEXT UNIQUE, wychowawca TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS przypisania (id INTEGER PRIMARY KEY AUTOINCREMENT, nauczyciel TEXT, przedmiot TEXT, klasa TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS oceny (id INTEGER PRIMARY KEY AUTOINCREMENT, uczen TEXT, przedmiot TEXT, ocena INTEGER, waga INTEGER, kategoria TEXT, data TEXT, komentarz TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS frekwencja (id INTEGER PRIMARY KEY AUTOINCREMENT, uczen TEXT, data TEXT, lekcja TEXT, status TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS wiadomosci (id INTEGER PRIMARY KEY AUTOINCREMENT, nadawca TEXT, odbiorca TEXT, temat TEXT, tresc TEXT, data TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS uwagi (id INTEGER PRIMARY KEY AUTOINCREMENT, uczen TEXT, nauczyciel TEXT, typ TEXT, tresc TEXT, data TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS plan_lekcji (id INTEGER PRIMARY KEY AUTOINCREMENT, klasa TEXT, dzien TEXT, nr_lekcji TEXT, przedmiot TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS zastepstwa (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, klasa TEXT, nr_lekcji TEXT, stary_przedmiot TEXT, nowy_przedmiot TEXT, nauczyciel TEXT, informacja TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS dyzury (id INTEGER PRIMARY KEY AUTOINCREMENT, osoba TEXT, miejsce TEXT, dzien TEXT, godzina TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS oceny_zachowania (id INTEGER PRIMARY KEY AUTOINCREMENT, uczen TEXT, okres TEXT, ocena TEXT, opis TEXT)")

# Bezpieczna migracja kolumn w ocenach
try:
    c.execute("ALTER TABLE oceny ADD COLUMN kategoria TEXT")
    conn.commit()
except sqlite3.OperationalError:
    pass

try:
    c.execute("ALTER TABLE oceny ADD COLUMN komentarz TEXT")
    conn.commit()
except sqlite3.OperationalError:
    pass

# Dane domyślne startowe
c.execute("SELECT COUNT(*) FROM uzytkownicy")
if c.fetchone()[0] == 0:
    c.execute("INSERT INTO uzytkownicy (imie_nazwisko, login, haslo, rola, klasa, powiazany_uczen) VALUES (?, ?, ?, ?, ?, ?)", ("Administrator", "admin", "admin123", "Admin", "-", "-"))
    c.execute("INSERT INTO uzytkownicy (imie_nazwisko, login, haslo, rola, klasa, powiazany_uczen) VALUES (?, ?, ?, ?, ?, ?)", ("Alicja Ołowniuk", "alicja", "admin123", "Nauczyciel", "7c SP5", "-"))
    c.execute("INSERT INTO uzytkownicy (imie_nazwisko, login, haslo, rola, klasa, powiazany_uczen) VALUES (?, ?, ?, ?, ?, ?)", ("Olivier", "olivier", "admin123", "Nauczyciel", "1c SP5", "-"))
    c.execute("INSERT INTO uzytkownicy (imie_nazwisko, login, haslo, rola, klasa, powiazany_uczen) VALUES (?, ?, ?, ?, ?, ?)", ("Emilia Nowak", "emilia", "emilia123", "Uczeń", "1c SP5", "-"))
    c.execute("INSERT INTO uzytkownicy (imie_nazwisko, login, haslo, rola, klasa, powiazany_uczen) VALUES (?, ?, ?, ?, ?, ?)", ("Jan Nowak (Rodzic)", "rodzic_emilia", "rodzic123", "Rodzic", "1c SP5", "Emilia Nowak"))
    c.execute("INSERT INTO klasy (nazwa_klasy, wychowawca) VALUES (?, ?)", ("7c SP5", "Alicja Ołowniuk"))
    c.execute("INSERT INTO klasy (nazwa_klasy, wychowawca) VALUES (?, ?)", ("1c SP5", "Olivier"))
    conn.commit()

c.execute("SELECT COUNT(*) FROM plan_lekcji")
if c.fetchone()[0] == 0:
    domyslny_plan = [
        ("7c SP5", "Poniedziałek", "1 [07:10 - 07:55]", "Język polski"),
        ("7c SP5", "Poniedziałek", "2 [08:00 - 08:45]", "Matematyka"),
        ("1c SP5", "Poniedziałek", "1 [07:10 - 07:55]", "Plastyka"),
        ("1c SP5", "Poniedziałek", "2 [08:00 - 08:45]", "Matematyka"),
        ("1c SP5", "Wtorek", "1 [07:10 - 07:55]", "Wychowanie fizyczne"),
    ]
    c.executemany("INSERT INTO plan_lekcji (klasa, dzien, nr_lekcji, przedmiot) VALUES (?, ?, ?, ?)", domyslny_plan)
    conn.commit()

if "dziennik_user" not in st.session_state:
    st.session_state["dziennik_user"] = None
if "dziennik_rola" not in st.session_state:
    st.session_state["dziennik_rola"] = None
if "librus_aktywna_zakladka" not in st.session_state:
    st.session_state["librus_aktywna_zakladka"] = "Oceny"

WSZYSTKIE_PRZEDMIOTY = [
    "Biologia", "Chemia", "Doradztwo zawodowe", "Edukacja zdrowotna", "Fizyka", 
    "Geografia", "Historia", "Informatyka", "Język angielski", "Język niemiecki", 
    "Język polski", "Matematyka", "Muzyka", "Plastyka", "Religia", "Technika", 
    "Wychowanie fizyczne", "Zajęcia z wychowawcą", "Edukacja dla bezpieczeństwa", "Wiedza o społeczeństwie", "Edukacja wczesnoszkolna"
]

KATEGORIE_OCEN = ["aktywność", "inna", "kartkówka", "odpowiedź ustna", "przewidywana roczna", "przewidywana śródroczna", "roczna", "sprawdzian", "śródroczna", "zadanie", "zeszyt"]

def renderuj_tabelue_planu_dla_klasy(docelowa_klasa, allow_change=False):
    c.execute("SELECT nazwa_klasy FROM klasy")
    klasy_baza = [k[0] for k in c.fetchall()]
    if not klasy_baza:
        klasy_baza = ["7c SP5"]
        
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
        dni_kolejnosc = [d for d in ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek"] if d in pivot_plan.columns]
        pozostale_dni = [d for d in pivot_plan.columns if d not in dni_kolejnosc]
        pivot_plan = pivot_plan[dni_kolejnosc + pozostale_dni]
        st.dataframe(pivot_plan, use_container_width=True)
    else:
        st.info(f"Brak zdefiniowanego planu lekcji dla klasy {wybrana_klasa}.")

    st.markdown("---")
    st.subheader("Aktywne zastępstwa dla klasy")
    df_zast = pd.read_sql("SELECT data as [Data], nr_lekcji as [Lekcja], stary_przedmiot as [Zastąpiony przedmiot], nowy_przedmiot as [Nowy przedmiot / Zmiana], nauczyciel as [Nauczyciel], informacja as [Uwagi] FROM zastepstwa WHERE klasa = ?", conn, params=(wybrana_klasa,))
    if not df_zast.empty:
        st.dataframe(df_zast, use_container_width=True, hide_index=True)
    else:
        st.info("Brak zaplanowanych zastępstw dla tej klasy.")

def renderuj_tabelue_ocen_dla_ucznia(imie_ucznia):
    c.execute("SELECT klasa FROM uzytkownicy WHERE imie_nazwisko = ?", (imie_ucznia,))
    res_k = c.fetchone()
    klasa_ucznia = res_k[0] if res_k and res_k[0] != "-" else "1c SP5"
    
    c.execute("SELECT DISTINCT przedmiot FROM plan_lekcji WHERE klasa = ?", (klasa_ucznia,))
    przedmioty_klasy = [row[0] for row in c.fetchall()]
    
    if not przedmioty_klasy:
        przedmioty_klasy = ["Edukacja wczesnoszkolna", "Wychowanie fizyczne"]

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
                val = int(row.ocena)
                waga = int(row.waga)
                if val > 0:
                    suma_wazona += val * waga
                    suma_wag += waga
                badge_list.append(f'<span class="grade-badge g-{val}" title="Ocena: {val}">({val})</span>' if val==0 else f'<span class="grade-badge g-{val}">{val}</span>')
            okres_1_html = " ".join(badge_list)
            if suma_wag > 0:
                srednia_p = round(suma_wazona / suma_wag, 2)
        else:
            okres_1_html = '<span style="color: gray; font-size: 12px;">Brak ocen</span>'
            
        tabela_dane.append({
            "Przedmiot": przedm,
            "Okres 1 (Oceny bieżące)": okres_1_html,
            "Śr. 1": srednia_p,
            "Okres 2 (Oceny bieżące)": '<span style="color: gray; font-size: 12px;">Brak ocen</span>',
            "Śr. 2": "-",
            "Śr. R": srednia_p
        })
    
    df_librus = pd.DataFrame(tabela_dane)
    st.write(df_librus.to_html(escape=False, index=False), unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Szczegóły ocen (Kategoria, Waga, Komentarz nauczyciela)")
    df_szczegoly = pd.read_sql("SELECT data as [Data], przedmiot as [Przedmiot], ocena as [Ocena], kategoria as [Kategoria], waga as [Waga], komentarz as [Komentarz] FROM oceny WHERE uczen = ?", conn, params=(imie_ucznia,))
    if not df_szczegoly.empty:
        st.dataframe(df_szczegoly, use_container_width=True, hide_index=True)
    else:
        st.info("Brak szczegółowych wpisów ocen.")

def renderuj_uwagi_dla_osoby(imie_osoby):
    st.subheader(f"Uwagi o uczniu / zachowaniu")
    df_uw = pd.read_sql("SELECT data as [Data], typ as [Typ], nauczyciel as [Nauczyciel], tresc as [Treść uwagi] FROM uwagi WHERE uczen = ?", conn, params=(imie_osoby,))
    if not df_uw.empty:
        for idx, row in df_uw.iterrows():
            t_typ = row["Typ"]
            css_klasa = "uwaga-poz" if t_typ == "Pozytywna" else ("uwaga-neg" if t_typ == "Negatywna" else "uwaga-neut")
            st.markdown(f"""
                <div class="{css_klasa}">
                    <b>[{row['Data']}] Typ: {t_typ}</b> (Nauczyciel: {row['Nauczyciel']})<br>
                    {row['Treść uwagi']}
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Brak wpisanych uwag.")

    st.markdown("---")
    st.subheader("Oceny z zachowania")
    df_zach = pd.read_sql("SELECT okres as [Okres], ocena as [Ocena z zachowania], opis as [Uzasadnienie] FROM oceny_zachowania WHERE uczen = ?", conn, params=(imie_osoby,))
    if not df_zach.empty:
        st.dataframe(df_zach, use_container_width=True, hide_index=True)
    else:
        st.info("Brak wystawionych ocen z zachowania.")

def renderuj_panel_dyzurow():
    st.subheader("Harmonogram Dyżurów (Nauczycielskie / Korytarzowe)")
    df_dyz = pd.read_sql("SELECT dzien as [Dzień], godzina as [Godzina / Przerwa], miejsce as [Miejsce / Sektor], osoba as [Osoba pełniąca dyżur] FROM dyzury", conn)
    if not df_dyz.empty:
        st.dataframe(df_dyz, use_container_width=True, hide_index=True)
    else:
        st.info("Brak zaplanowanych dyżurów w systemie.")

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
                
                col_btn_odp, col_btn_del = st.columns([4, 1])
                with col_btn_del:
                    # Przycisk usuwania otrzymanej wiadomości
                    if st.button("🗑️ Usuń", key=f"del_msg_{row['id']}"):
                        c.execute("DELETE FROM wiadomosci WHERE id = ?", (row['id'],))
                        conn.commit()
                        st.success("Wiadomość została usunięta!")
                        st.rerun()
                
                with st.form(f"form_odpowiedz_{row['id']}"):
                    st.text(f"Odpowiedz do: {row['Od']}")
                    odp_tresc = st.text_area("Treść odpowiedzi:", key=f"odp_text_{row['id']}")
                    if st.form_submit_button("Wyślij odpowiedź", type="secondary"):
                        if odp_tresc.strip():
                            temat_odp = f"RE: {row['Temat']}"
                            c.execute("INSERT INTO wiadomosci (nadawca, odbiorca, temat, tresc, data) VALUES (?, ?, ?, ?, ?)",
                                      (aktualny_uzytkownik, row['Od'], temat_odp, odp_tresc, str(date.today())))
                            conn.commit()
                            st.success("Odpowiedź została wysłana!")
                            st.rerun()
                        else:
                            st.warning("Treść odpowiedzi nie może być pusta!")
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
                c.execute("SELECT imie_nazwisko, rola FROM uzytkownicy WHERE login = ? AND haslo = ?", (login_in, haslo_in))
                res = c.fetchone()
                if res:
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
        <div style="font-size: 12px; color: #555;">ostatnie logowanie: 2026-09-24 18:00</div>
    </div>
""", unsafe_allow_html=True)

cols_ikony = st.columns(9)
with cols_ikony[0]:
    if st.button("&#127968;\nInterfejs", use_container_width=True):
        st.session_state["librus_aktywna_zakladka"] = "Interfejs"
        st.rerun()
with cols_ikony[1]:
    btn_label = "&#128214;\nLekcja (N)" if st.session_state["dziennik_rola"] == "Nauczyciel" else "&#128214;\nLekcja"
    if st.button(btn_label, use_container_width=True):
        st.session_state["librus_aktywna_zakladka"] = "Realizacja" if st.session_state["dziennik_rola"] == "Nauczyciel" else "Plan"
        st.rerun()
with cols_ikony[2]:
    if st.button("&#128202;\nOceny", use_container_width=True):
        st.session_state["librus_aktywna_zakladka"] = "Oceny"
        st.rerun()
with cols_ikony[3]:
    if st.button("&#9888;\nUwagi", use_container_width=True):
        st.session_state["librus_aktywna_zakladka"] = "Uwagi"
        st.rerun()
with cols_ikony[4]:
    if st.button("&#128203;\nFrekwencja", use_container_width=True):
        st.session_state["librus_aktywna_zakladka"] = "Frekwencja"
        st.rerun()
with cols_ikony[5]:
    if st.button("&#9993;\nWiadomości", use_container_width=True):
        st.session_state["librus_aktywna_zakladka"] = "Wiadomości"
        st.rerun()
with cols_ikony[6]:
    if st.button("&#128197;\nPlan/Zast.", use_container_width=True):
        st.session_state["librus_aktywna_zakladka"] = "Plan"
        st.rerun()
with cols_ikony[7]:
    if st.button("&#9881;\nUstawienia", use_container_width=True):
        st.session_state["librus_aktywna_zakladka"] = "Ustawienia"
        st.rerun()
with cols_ikony[8]:
    if st.button("&#128682;\nWyloguj", use_container_width=True):
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

c.execute("SELECT klasa FROM uzytkownicy WHERE imie_nazwisko = ?", (st.session_state["dziennik_user"],))
res_u_klasa = c.fetchone()
moja_klasa = res_u_klasa[0] if res_u_klasa and res_u_klasa[0] != "-" else "7c SP5"

# ================= OBSŁUGA ZAKŁADKI USTAWIENIA =================
if akt_zakl == "Ustawienia":
    st.subheader("Ustawienia konta — Zmiana hasła")
    with st.form("form_zmien_haslo"):
        st_haslo_stare = st.text_input("Aktualne hasło:", type="password")
        st_haslo_nowe = st.text_input("Nowe hasło:", type="password")
        st_haslo_nowe_powt = st.text_input("Powtórz nowe hasło:", type="password")
        
        btn_zmien = st.form_submit_button("Zmień hasło", type="primary")
        if btn_zmien:
            c.execute("SELECT haslo FROM uzytkownicy WHERE imie_nazwisko = ?", (st.session_state["dziennik_user"],))
            db_haslo = c.fetchone()[0]
            if st_haslo_stare != db_haslo:
                st.error("Podane aktualne hasło jest niepoprawne!")
            elif not st_haslo_nowe or len(st_haslo_nowe) < 4:
                st.error("Nowe hasło musi mieć co najmniej 4 znaki!")
            elif st_haslo_nowe != st_haslo_nowe_powt:
                st.error("Nowe hasła nie zgadzają się!")
            else:
                c.execute("UPDATE uzytkownicy SET haslo = ? WHERE imie_nazwisko = ?", (st_haslo_nowe, st.session_state["dziennik_user"]))
                conn.commit()
                st.success("Hasło zostało pomyślnie zmienione!")

# ================= 1. PANEL ADMINISTRATORA =================
elif st.session_state["dziennik_rola"] == "Admin":
    st.subheader("Panel Administratora — Zarządzanie Szkołą")
    adm_tab1, adm_tab2, adm_tab3, adm_tab4, adm_tab5, adm_tab6 = st.tabs(["Klasy", "Użytkownicy", "Plan Lekcji", "Zastępstwa i Dyżury", "Przypisania", "Wiadomości"])
    
    with adm_tab1:
        with st.form("form_klasa"):
            k_nazwa = st.text_input("Nazwa nowej klasy (np. 1c SP5):")
            c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE rola = 'Nauczyciel'")
            nauczyciele_l = [n[0] for n in c.fetchall()]
            k_wych = st.selectbox("Wychowawca:", nauczyciele_l) if nauczyciele_l else ""
            if st.form_submit_button("Utwórz klasę", type="primary"):
                try:
                    c.execute("INSERT INTO klasy (nazwa_klasy, wychowawca) VALUES (?, ?)", (k_nazwa, k_wych))
                    conn.commit()
                    st.success(f"Dodano klasę {k_nazwa}!")
                    st.rerun()
                except: st.error("Taka klasa już istnieje!")
        
        st.markdown("---")
        st.write("### Lista klas i usuwanie klas")
        df_klasy_adm = pd.read_sql("SELECT id, nazwa_klasy as [Klasa], wychowawca as [Wychowawca] FROM klasy", conn)
        if not df_klasy_adm.empty:
            st.dataframe(df_klasy_adm, use_container_width=True, hide_index=True)
            with st.form("form_usun_klase"):
                klasa_id_do_usuniecia = st.selectbox("Wybierz ID klasy do usunięcia:", df_klasy_adm["id"].tolist())
                btn_usun_k = st.form_submit_button("Usuń wybraną klasę", type="primary")
                if btn_usun_k:
                    c.execute("DELETE FROM klasy WHERE id = ?", (klasa_id_do_usuniecia,))
                    conn.commit()
                    st.success(f"Usunięto klasę o ID: {klasa_id_do_usuniecia}!")
                    st.rerun()
        else:
            st.info("Brak zdefiniowanych klas.")

    with adm_tab2:
        with st.form("form_user"):
            st.write("### Dodaj nowego użytkownika")
            u_imie = st.text_input("Imię i nazwisko:")
            u_login = st.text_input("Login:")
            u_haslo = st.text_input("Hasło:", type="password")
            u_rola = st.selectbox("Rola:", ["Uczeń", "Rodzic", "Nauczyciel", "Admin"])
            c.execute("SELECT nazwa_klasy FROM klasy")
            klasy_l = [k[0] for k in c.fetchall()]
            u_klasa = st.selectbox("Klasa:", ["-"] + klasy_l)
            c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE rola = 'Uczeń'")
            uczniowie_l = [uc[0] for uc in c.fetchall()]
            u_powiazanie = st.selectbox("Powiązany uczeń (dla Rodzica):", ["-"] + uczniowie_l)
            
            if st.form_submit_button("Utwórz konto", type="primary"):
                try:
                    c.execute("INSERT INTO uzytkownicy (imie_nazwisko, login, haslo, rola, klasa, powiazany_uczen) VALUES (?, ?, ?, ?, ?, ?)", 
                              (u_imie, u_login, u_haslo, u_rola, u_klasa, u_powiazanie))
                    conn.commit()
                    st.success(f"Utworzono konto dla {u_imie}!")
                    st.rerun()
                except: st.error("Ten login jest już zajęty!")
        
        st.markdown("---")
        st.write("### Lista użytkowników, edycja i usuwanie")
        df_users_adm = pd.read_sql("SELECT id, imie_nazwisko as [Imię i Nazwisko], login as [Login], haslo as [Hasło], rola as [Rola], klasa as [Klasa], powiazany_uczen as [Powiązany uczeń] FROM uzytkownicy", conn)
        if not df_users_adm.empty:
            st.dataframe(df_users_adm, use_container_width=True, hide_index=True)
            
            st.markdown("#### Edycja danych użytkownika")
            wybrany_id_edycji = st.selectbox("Wybierz ID użytkownika do edycji:", df_users_adm["id"].tolist(), key="sel_ed_u_id")
            
            c.execute("SELECT imie_nazwisko, login, haslo, rola, klasa, powiazany_uczen FROM uzytkownicy WHERE id = ?", (wybrany_id_edycji,))
            akt_dane_u = c.fetchone()
            
            with st.form("form_edytuj_uzytkownika"):
                ed_imie = st.text_input("Imię i nazwisko:", value=akt_dane_u[0] if akt_dane_u else "")
                ed_login = st.text_input("Login:", value=akt_dane_u[1] if akt_dane_u else "")
                ed_haslo = st.text_input("Hasło:", value=akt_dane_u[2] if akt_dane_u else "")
                
                role_opcje = ["Uczeń", "Rodzic", "Nauczyciel", "Admin"]
                akt_rola_idx = role_opcje.index(akt_dane_u[3]) if akt_dane_u and akt_dane_u[3] in role_opcje else 0
                ed_rola = st.selectbox("Rola:", role_opcje, index=akt_rola_idx)
                
                c.execute("SELECT nazwa_klasy FROM klasy")
                klasy_l_ed = [k[0] for k in c.fetchall()]
                klasy_wybor = ["-"] + klasy_l_ed
                akt_klasa_idx = klasy_wybor.index(akt_dane_u[4]) if akt_dane_u and akt_dane_u[4] in klasy_wybor else 0
                ed_klasa = st.selectbox("Klasa:", klasy_wybor, index=akt_klasa_idx)
                
                c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE rola = 'Uczeń'")
                uczniowie_l_ed = ["-"] + [uc[0] for uc in c.fetchall()]
                akt_pow_idx = uczniowie_l_ed.index(akt_dane_u[5]) if akt_dane_u and akt_dane_u[5] in uczniowie_l_ed else 0
                ed_powiazanie = st.selectbox("Powiązany uczeń (dla Rodzica):", uczniowie_l_ed, index=akt_pow_idx)
                
                btn_zapisz_edycje_u = st.form_submit_button("Zapisz zmiany użytkownika", type="primary")
                if btn_zapisz_edycje_u:
                    try:
                        c.execute("UPDATE uzytkownicy SET imie_nazwisko = ?, login = ?, haslo = ?, rola = ?, klasa = ?, powiazany_uczen = ? WHERE id = ?",
                                      (ed_imie, ed_login, ed_haslo, ed_rola, ed_klasa, ed_powiazanie, wybrany_id_edycji))
                        conn.commit()
                        st.success("Dane użytkownika zostały pomyślnie zaktualizowane!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Podany login jest już zajęty przez innego użytkownika!")

            st.markdown("---")
            with st.form("form_usun_uzytkownika"):
                st.write("#### Usuwanie użytkownika")
                user_id_do_usuniecia = st.selectbox("Wybierz ID użytkownika do usunięcia:", df_users_adm["id"].tolist(), key="del_u_sel")
                btn_usun_u = st.form_submit_button("Usuń wybranego użytkownika", type="primary")
                if btn_usun_u:
                    c.execute("DELETE FROM uzytkownicy WHERE id = ?", (user_id_do_usuniecia,))
                    conn.commit()
                    st.success(f"Usunięto użytkownika o ID: {user_id_do_usuniecia}!")
                    st.rerun()

    with adm_tab3:
        st.subheader("Edycja Planu Lekcji (Dodawanie i Usuwanie wpisów)")
        with st.form("form_plan"):
            c.execute("SELECT nazwa_klasy FROM klasy")
            klasy_p = [k[0] for k in c.fetchall()]
            p_klasa = st.selectbox("Wybierz klasę:", klasy_p if klasy_p else ["1c SP5"])
            p_dzien = st.selectbox("Dzień tygodnia:", ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek"])
            p_nr = st.selectbox("Nr lekcji / Godzina:", [
                "1 [07:10 - 07:55]", "2 [08:00 - 08:45]", "3 [08:50 - 09:35]", 
                "4 [09:45 - 10:30]", "5 [10:40 - 11:25]", "6 [11:40 - 12:25]"
            ])
            p_przedmiot = st.selectbox("Przedmiot:", WSZYSTKIE_PRZEDMIOTY)
            if st.form_submit_button("Dodaj do planu", type="primary"):
                c.execute("INSERT INTO plan_lekcji (klasa, dzien, nr_lekcji, przedmiot) VALUES (?, ?, ?, ?)", (p_klasa, p_dzien, p_nr, p_przedmiot))
                conn.commit()
                st.success("Dodano lekcję do planu!")
                st.rerun()

        st.markdown("---")
        renderuj_tabelue_planu_dla_klasy("1c SP5", allow_change=True)

        st.markdown("---")
        st.write("### Usuwanie lekcji z planu")
        df_plan_all = pd.read_sql("SELECT id, klasa as [Klasa], dzien as [Dzień], nr_lekcji as [Lekcja], przedmiot as [Przedmiot] FROM plan_lekcji", conn)
        if not df_plan_all.empty:
            st.dataframe(df_plan_all, use_container_width=True, hide_index=True)
            with st.form("form_usun_lekcje_z_planu"):
                plan_id_do_usuniecia = st.selectbox("Wybierz ID wpisu planu do usunięcia:", df_plan_all["id"].tolist())
                btn_usun_pl = st.form_submit_button("Usuń wybraną lekcję z planu", type="primary")
                if btn_usun_pl:
                    c.execute("DELETE FROM plan_lekcji WHERE id = ?", (plan_id_do_usuniecia,))
                    conn.commit()
                    st.success(f"Usunięto lekcję o ID: {plan_id_do_usuniecia}!")
                    st.rerun()
        else:
            st.info("Brak lekcji w planie.")

    with adm_tab4:
        st.subheader("Zarządzanie Zastępstwami")
        with st.form("form_zastepstwo_adm"):
            z_data = st.date_input("Data zastępstwa:", value=date.today())
            c.execute("SELECT nazwa_klasy FROM klasy")
            klasy_z = [k[0] for k in c.fetchall()]
            z_klasa = st.selectbox("Klasa:", klasy_z if klasy_z else ["1c SP5"])
            z_nr = st.selectbox("Nr lekcji:", ["1 [07:10 - 07:55]", "2 [08:00 - 08:45]", "3 [08:50 - 09:35]", "4 [09:45 - 10:30]"])
            z_stary = st.text_input("Zastąpiony przedmiot (np. Matematyka):")
            z_nowy = st.text_input("Nowy przedmiot / Zmiana (np. Zastępstwo / Informatyka):")
            c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE rola = 'Nauczyciel'")
            nauczyciele_z = [n[0] for n in c.fetchall()]
            z_nauczyciel = st.selectbox("Nauczyciel prowadzący:", nauczyciele_z if nauczyciele_z else ["-"])
            z_info = st.text_input("Informacja / Komentarz (np. Odwołane, Sala 12):")
            
            if st.form_submit_button("Dodaj zastępstwo", type="primary"):
                c.execute("INSERT INTO zastepstwa (data, klasa, nr_lekcji, stary_przedmiot, nowy_przedmiot, nauczyciel, informacja) VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (str(z_data), z_klasa, z_nr, z_stary, z_nowy, z_nauczyciel, z_info))
                conn.commit()
                st.success("Dodano zastępstwo!")
                st.rerun()

    with adm_tab5:
        st.subheader("Przypisania Nauczycieli do Przedmiotów i Klas")
        with st.form("form_przypisanie"):
            c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE rola = 'Nauczyciel'")
            nauczyciele_p = [n[0] for n in c.fetchall()]
            pr_nauczyciel = st.selectbox("Nauczyciel:", nauczyciele_p if nauczyciele_p else ["-"])
            pr_przedmiot = st.selectbox("Przedmiot:", WSZYSTKIE_PRZEDMIOTY)
            c.execute("SELECT nazwa_klasy FROM klasy")
            klasy_p = [k[0] for k in c.fetchall()]
            pr_klasa = st.selectbox("Klasa:", klasy_p if klasy_p else ["1c SP5"])
            
            if st.form_submit_button("Zapisz przypisanie", type="primary"):
                c.execute("INSERT INTO przypisania (nauczyciel, przedmiot, klasa) VALUES (?, ?, ?)", (pr_nauczyciel, pr_przedmiot, pr_klasa))
                conn.commit()
                st.success("Zapisano przypisanie nauczyciela!")
                st.rerun()

    with adm_tab6:
        renderuj_zakladke_wiadomosci("Administrator")

# ================= 2. PANEL NAUCZYCIELA =================
elif st.session_state["dziennik_rola"] == "Nauczyciel":
    nauczyciel_zalogowany = st.session_state["dziennik_user"]
    st.subheader(f"Panel Nauczyciela — {nauczyciel_zalogowany}")
    
    n_tab1, n_tab2, n_tab3, n_tab4, n_tab5, n_tab6, n_tab7 = st.tabs([
        "Realizacja lekcji", "Wystawianie Ocen", "Frekwencja", "Uwagi i Zachowanie", "Plan i Dyżury", "Zastępstwa", "Wiadomości"
    ])
    
    with n_tab1:
        st.subheader("Dziennik lekcyjny — Wpis tematu i obecności")
        c.execute("SELECT DISTINCT klasa, przedmiot FROM przypisania WHERE nauczyciel = ?", (nauczyciel_zalogowany,))
        przypisane_lekcje = c.fetchall()
        
        if przypisane_lekcje:
            opcje_lekcji = [f"{kl} — {przh}" for kl, przh in przypisane_lekcje]
            wybrana_lekcja = st.selectbox("Wybierz przedmiot i klasę:", opcje_lekcji)
            w_klasa, w_przedmiot = wybrana_lekcja.split(" — ")
            
            with st.form("form_realizacja_lekcji"):
                data_lekcji = st.date_input("Data lekcji:", value=date.today())
                nr_jednostki = st.selectbox("Numer lekcji:", ["1 [07:10 - 07:55]", "2 [08:00 - 08:45]", "3 [08:50 - 09:35]", "4 [09:45 - 10:30]", "5 [10:40 - 11:25]"])
                temat_lekcji = st.text_input("Temat lekcji:")
                
                st.write("### Sprawdzenie frekwencji uczniów w klasie")
                c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE klasa = ? AND rola = 'Uczeń'", (w_klasa,))
                uczniowie_klas = c.fetchall()
                
                frekwencja_slownik = {}
                if uczniowie_klas:
                    for uczen in uczniowie_klas:
                        status_obecnosci = st.selectbox(f"{uczen[0]}", ["Obecny", "Nieobecny", "Spóźniony", "Usprawiedliwiony"], key=f"freq_{uczen[0]}")
                        frekwencja_slownik[uczen[0]] = status_obecnosci
                else:
                    st.info("Brak uczniów przypisanych do tej klasy.")
                
                if st.form_submit_button("Zapisz lekcję i frekwencję", type="primary"):
                    for uczen, status in frekwencja_slownik.items():
                        c.execute("INSERT INTO frekwencja (uczen, data, lekcja, status) VALUES (?, ?, ?, ?)",
                                  (uczen, str(data_lekcji), nr_jednostki, status))
                    conn.commit()
                    st.success("Zapisano temat lekcji oraz frekwencję uczniów!")
        else:
            st.info("Nie masz jeszcze przypisanych żadnych przedmiotów i klas przez Administratora.")

    with n_tab2:
        st.subheader("Wystawianie oceny bieżącej")
        with st.form("form_wystaw_ocene"):
            c.execute("SELECT DISTINCT klasa FROM przypisania WHERE nauczyciel = ?", (nauczyciel_zalogowany,))
            klasy_nauczyciela = [k[0] for k in c.fetchall()]
            wybrana_klasa_ocena = st.selectbox("Wybierz klasę:", klasy_nauczyciela if klasy_nauczyciela else ["1c SP5"])
            
            c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE klasa = ? AND rola = 'Uczeń'", (wybrana_klasa_ocena,))
            uczniowie_w_klasie = [u[0] for u in c.fetchall()]
            uczen_docelowy = st.selectbox("Uczeń:", uczniowie_w_klasie if uczniowie_w_klasie else ["Brak"])
            
            c.execute("SELECT DISTINCT przedmiot FROM przypisania WHERE nauczyciel = ? AND klasa = ?", (nauczyciel_zalogowany, wybrana_klasa_ocena))
            przedmioty_nauczyciela = [p[0] for p in c.fetchall()]
            przedmiot_docelowy = st.selectbox("Przedmiot:", przedmioty_nauczyciela if przedmioty_nauczyciela else WSZYSTKIE_PRZEDMIOTY)
            
            ocena_val = st.selectbox("Ocena:", [1, 2, 3, 4, 5, 6])
            waga_val = st.slider("Waga oceny:", min_value=1, max_value=3, value=1)
            kategoria_val = st.selectbox("Kategoria:", KATEGORIE_OCEN)
            komentarz_val = st.text_input("Komentarz / Opis oceny:")
            data_oceny = st.date_input("Data wystawienia:", value=date.today())
            
            if st.form_submit_button("Wystaw ocenę", type="primary"):
                if uczen_docelowy != "Brak":
                    c.execute("INSERT INTO oceny (uczen, przedmiot, ocena, waga, kategoria, data, komentarz) VALUES (?, ?, ?, ?, ?, ?, ?)",
                              (uczen_docelowy, przedmiot_docelowy, ocena_val, waga_val, kategoria_val, str(data_oceny), komentarz_val))
                    conn.commit()
                    st.success(f"Wystawiono ocenę {ocena_val} dla ucznia {uczen_docelowy}!")
                    st.rerun()
                else:
                    st.error("Brak ucznia w wybranej klasie.")

    with n_tab3:
        st.subheader("Historia i zestawienie frekwencji")
        c.execute("SELECT uczen as [Uczeń], data as [Data], lekcja as [Lekcja], status as [Status] FROM frekwencja")
        df_fr = c.fetchall()
        if df_fr:
            st.dataframe(pd.DataFrame(df_fr, columns=["Uczeń", "Data", "Lekcja", "Status"]), use_container_width=True, hide_index=True)
        else:
            st.info("Brak wpisów frekwencji.")

    with n_tab4:
        st.subheader("Wpisywanie uwagi o zachowaniu / postępach")
        with st.form("form_uwaga"):
            c.execute("SELECT imie_nazwisko FROM uzytkownicy WHERE rola = 'Uczeń'")
            wszyscy_uczniowie = [u[0] for u in c.fetchall()]
            uw_uczen = st.selectbox("Wybierz ucznia:", wszyscy_uczniowie if wszyscy_uczniowie else ["Brak"])
            uw_typ = st.selectbox("Typ uwagi:", ["Pozytywna", "Neutralna", "Negatywna"])
            uw_tresc = st.text_area("Treść uwagi:")
            
            if st.form_submit_button("Dodaj uwagę", type="primary"):
                if uw_uczen != "Brak" and uw_tresc.strip():
                    c.execute("INSERT INTO uwagi (uczen, nauczyciel, typ, tresc, data) VALUES (?, ?, ?, ?, ?)",
                              (uw_uczen, nauczyciel_zalogowany, uw_typ, uw_tresc, str(date.today())))
                    conn.commit()
                    st.success("Dodano uwagę pomyślnie!")
                    st.rerun()
                else:
                    st.error("Uzupełnij treść uwagi.")

    with n_tab5:
        renderuj_tabelue_planu_dla_klasy(moja_klasa, allow_change=True)
        st.markdown("---")
        renderuj_panel_dyzurow()

    with n_tab6:
        st.subheader("Zastępstwa w szkole")
        df_z_all = pd.read_sql("SELECT data as [Data], klasa as [Klasa], nr_lekcji as [Lekcja], stary_przedmiot as [Stary przedmiot], nowy_przedmiot as [Nowy przedmiot], nauczyciel as [Nauczyciel], informacja as [Informacje] FROM zastepstwa", conn)
        if not df_z_all.empty:
            st.dataframe(df_z_all, use_container_width=True, hide_index=True)
        else:
            st.info("Brak zastępstw w bazie.")

    with n_tab7:
        renderuj_zakladke_wiadomosci(nauczyciel_zalogowany)

# ================= 3. PANEL UCZNIA =================
elif st.session_state["dziennik_rola"] == "Uczeń":
     uczen_zalogowany = st.session_state["dziennik_user"]
     st.subheader(f"Panel Ucznia — {uczen_zalogowany}")
     
     u_tab1, u_tab2, u_tab3, u_tab4, u_tab5 = st.tabs(["Oceny", "Plan lekcji", "Uwagi i Zachowanie", "Frekwencja", "Wiadomości"])
     
     with u_tab1:
         renderuj_tabelue_ocen_dla_ucznia(uczen_zalogowany)
         
     with u_tab2:
         renderuj_tabelue_planu_dla_klasy(moja_klasa)
         
     with u_tab3:
         renderuj_uwagi_dla_osoby(uczen_zalogowany)
         
     with u_tab4:
         st.subheader("Moja frekwencja")
         df_f_ucz = pd.read_sql("SELECT data as [Data], lekcja as [Lekcja], status as [Status] FROM frekwencja WHERE uczen = ?", conn, params=(uczen_zalogowany,))
         if not df_f_ucz.empty:
             st.dataframe(df_f_ucz, use_container_width=True, hide_index=True)
         else:
             st.info("Brak wpisów frekwencji.")
             
     with u_tab5:
         renderuj_zakladke_wiadomosci(uczen_zalogowany)

# ================= 4. PANEL RODZICA =================
elif st.session_state["dziennik_rola"] == "Rodzic":
    rodzic_zalogowany = st.session_state["dziennik_user"]
    c.execute("SELECT powiazany_uczen FROM uzytkownicy WHERE imie_nazwisko = ?", (rodzic_zalogowany,))
    res_p = c.fetchone()
    dziecko = res_p[0] if res_p and res_p[0] != "-" else "Emilia Nowak"
    
    st.subheader(f"Panel Rodzica — Podgląd dziecka: **{dziecko}**")
    
    r_tab1, r_tab2, r_tab3, r_tab4, r_tab5 = st.tabs(["Oceny dziecka", "Plan lekcji", "Uwagi i Zachowanie", "Frekwencja", "Wiadomości"])
    
    with r_tab1:
        renderuj_tabelue_ocen_dla_ucznia(dziecko)
        
    with r_tab2:
        c.execute("SELECT klasa FROM uzytkownicy WHERE imie_nazwisko = ?", (dziecko,))
        res_dk = c.fetchone()
        klasa_dziecka = res_dk[0] if res_dk and res_dk[0] != "-" else "1c SP5"
        renderuj_tabelue_planu_dla_klasy(klasa_dziecka)
        
    with r_tab3:
        renderuj_uwagi_dla_osoby(dziecko)
        
    with r_tab4:
        st.subheader(f"Frekwencja ucznia: {dziecko}")
        df_f_d = pd.read_sql("SELECT data as [Data], lekcja as [Lekcja], status as [Status] FROM frekwencja WHERE uczen = ?", conn, params=(dziecko,))
        if not df_f_d.empty:
            st.dataframe(df_f_d, use_container_width=True, hide_index=True)
        else:
            st.info("Brak wpisów frekwencji dla dziecka.")
            
    with r_tab5:
        renderuj_zakladke_wiadomosci(rodzic_zalogowany)
