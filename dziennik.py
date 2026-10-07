import sqlite3
import streamlit as st
import pandas as pd
from datetime import date

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

# Rozszerzone kategorie ocen o brak zeszytu, ćwiczenia, np itp.
KATEGORIE_OCEN = [
    "aktywność", "brak zeszytu", "ćwiczenia", "inna", "kartkówka", 
    "np (nieprzygotowanie)", "odpowiedź ustna", "przewidywana roczna", 
    "przewidywana śródroczna", "roczna", "sprawdzian", "śródroczna", 
    "zadanie", "zeszyt"
]

def renderuj_podsumowanie_frekwencji(df_frez):
    """Funkcja pomocnicza do wyświetlania kafelków z sumowaniem obecności i nieobecności"""
    if df_frez.empty:
        st.info("Brak danych frekwencyjnych do podsumowania.")
        return
    
    total_wpisow = len(df_frez)
    ile_ob = len(df_frez[df_frez["Status"] == "ob"])
    ile_nb = len(df_frez[df_frez["Status"] == "nb"])
    ile_u = len(df_frez[df_frez["Status"] == "u"])
    ile_sp = len(df_frez[df_frez["Status"] == "sp"])
    ile_zw = len(df_frez[df_frez["Status"] == "zw"])
    
    lacznie_obecnych = ile_ob + ile_sp
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Wszystkie", total_wpisow)
    col2.metric("Obecni (ob)", ile_ob)
    col3.metric("Nieobecni (nb)", ile_nb)
    col4.metric("Usprawiedliwieni (u)", ile_u)
    col5.metric("Spóźnieni/Zwolnieni", f"{ile_sp} / {ile_zw}")
    col6.metric("Obecni łącznie", lacznie_obecnych)

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
    <div class="librus-logo-text">Synergia <sub>Librus
