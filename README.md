# tikaweb-mood-music-recommendations
Musiikki ehdotukset
Sovelluksen tarkoituksena on auttaa käyttäjiä löytämään uusia biisejä erityisesti tunnelman perusteella

Toiminnot:
- Käyttäjä pystyy luomaan tunnuksen ja kirjautumaan sisään sovellukseen
- Kirjautuneet käyttäjät pystyvät lisäämään, muokkaamaan sekä poistamaan biisejä
- Biiseille voidaan valita genre ja tunnelma valmiista luokista
- Käyttäjä näkee omat sekä muiden julkaisemat biisit
- Biisit luokitellaan genren ja tunnelman mukaan
- Käyttäjä pystyy hakemaan biisin nimeä, artistia tai genreä, mutta tärkeimpänä sovelluksen ominaisuutena, ehdotuksia tunnelman mukaan
- Biisi tai artisti haetaan vapaalla hakusanalla kun taas genre ja tunnelma valitsemalla valmis luokka
- Käyttäjät voivat myös lisätä arvosteluja (arvosana 1-10 sekä kommentti).
- Käyttäjät pystyvät tykkäämään biiseistä ja biisit voidaan järjestää haussa tykkäysten määrän perusteella
- Käyttäjäsivulla näkyy käyttäjän lisätyt biisit sekä arvostelut

Pääasiallinen tietokohde on musiikkiehdotus ja toissijainen tietokohde on arvostelu. Tyk¢käykset lisäominaisuutena

Käyttö:
1. Kloonaa repositorio käyttämällä "git clone https://github.com/nessamerivirta/tikaweb-mood-music-recommendations.git"
2. Siirry terminaalissa kansioon "cd tikaweb-mood-music-recommendations"
3. Luo virtuaaliympäristö "python -m venv .venv"
4. Aktivoi riippuen käyttöjärjestelmästä :"source .venv/bin/activate" (macOS/Linux), ".venv\Scripts\activate" (Windows)
5. Asenna flask "pip install flask"
6. Käynnistä sovellus "python app.py"
