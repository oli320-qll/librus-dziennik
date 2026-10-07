import streamlit as st
import pandas as pd

# Konfiguracja strony
st.set_page_config(page_title="Prosta przeglądarka - Librus", layout="wide")

st.title("📚 Dziennik Lekcyjny - Sprawdzanie i Sumowanie Obecności")

# Lista uczniów
uczniowie = [
    "Adam Nowak",
    "Barbara Kozakowska",
    "Katarzyna Nowakówna",
    "Łucja Widomska",
    "Adam Kazimierz"
]

# Dostępne statusy obecności
statusy_opcje = ["ob", "nb", "u", "sp", "zw"]

# Inicjalizacja stanu sesji (session_state) do przechowywania historii/stanu obecności
if "dane_obecnosci" not in st.session_state:
    # Tworzymy słownik przechowujący dla każdego ucznia liczbę poszczególnych statusów
    st.session_state.dane_obecnosci = {
        uczen: {status: 0 for status in statusy_opcje} for uczen in uczniowie
    }

st.subheader("📝 Sprawdź obecność na dzisiejszej lekcji")

# Formularz do zaznaczania obecności
with st.form(key="formularz_obecnosci"):
    wybory_biezace = {}
    
    for i, uczen in enumerate(uczniowie, start=1):
        st.markdown(f"**{i}. {uczen}**")
        # Radio button dla każdego ucznia
        wybory_biezace[uczen] = st.radio(
            f"Status_{uczen}",
            statusy_opcje,
            key=f"st_{uczen}",
            horizontal=True,
            label_visibility="collapsed"
        )
        st.divider()

    # Przycisk zapisujący i sumujący wyniki
    submit_button = st.form_submit_button(label="Zatwierdź i sumuj obecności")

if submit_button:
    # Aktualizujemy (sumujemy) dane w session_state
    for uczen, status in wybory_biezace.items():
        st.session_state.dane_obecnosci[uczen][status] += 1
    st.success("Zapisano i zaktualizowano sumy obecności!")

# --- SEKCJA PODSUMOWANIA ---
st.markdown("---")
st.subheader("📊 Podsumowanie sumaryczne (Skumulowane)")

# Przygotowanie danych do tabeli podsumowującej
tabela_danych = []
for uczen, staty in st.session_state.dane_obecnosci.items():
    wiersz = {"Uczeń": uczen}
    wiersz.update(staty)
    # Dodanie kolumny z sumą wszystkich wpisów dla ucznia
    wiersz["Suma wpisów"] = sum(staty.values())
    tabela_danych.append(wiersz)

df_podsumowanie = pd.DataFrame(tabela_danych)

# Wyświetlenie ładnej tabeli z podsumowaniem
st.dataframe(df_podsumowanie, use_container_width=True, hide_index=True)

# Opcja resetowania podsumowania
if st.button("Resetuj statystyki"):
    st.session_state.dane_obecnosci = {
        uczen: {status: 0 for status in statusy_opcje} for uczen in uczniowie
    }
    st.rerun()
