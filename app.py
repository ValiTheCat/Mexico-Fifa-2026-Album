import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import requests
from PIL import Image
from io import BytesIO
import base64
import time

st.set_page_config(
    page_title="FIFA 2026 Sticker Tracker",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Sticker card base */
.s-card {
    border-radius: 12px;
    padding: 8px 6px 6px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s ease;
    border: 2.5px solid #374151;
    background: #1f2937;
    min-height: 155px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
}
/* Missing = faded */
.s-missing { opacity: 0.35; filter: grayscale(60%); }
/* Owned = full color */
.s-owned   { opacity: 1.0;  filter: none; }

/* Rarity borders — USA only */
.r-base   { border-color: #4b5563; }
.r-blue   { border-color: #3b82f6; background: #1e3a5f; }
.r-purple { border-color: #a855f7; background: #2e1a47; }
.r-red    { border-color: #ef4444; background: #3b1219; }
.r-foil   { border-color: #f59e0b; background: #3b2a08; }
.r-none   { border-color: #374151; }

.s-img {
    width: 64px; height: 72px;
    object-fit: cover; object-position: top center;
    border-radius: 8px;
    background: #374151;
}
.s-placeholder {
    width: 64px; height: 72px;
    border-radius: 8px;
    background: #374151;
    display: flex; align-items: center; justify-content: center;
    font-size: 26px;
}
.s-id   { font-size: 10px; font-weight: 700; color: #9ca3af; }
.s-name { font-size: 9px;  color: #6b7280; line-height: 1.2; }
.s-check{ font-size: 11px; color: #34d399; font-weight: 700; }

/* Rarity pill selector */
.rarity-row { display: flex; gap: 3px; justify-content: center; flex-wrap: wrap; margin-top: 3px; }
.r-pill {
    font-size: 8px; padding: 1px 5px;
    border-radius: 10px; cursor: pointer;
    border: 1px solid transparent;
    font-weight: 600; transition: all 0.15s;
}
.r-pill-base   { background:#374151; color:#9ca3af; }
.r-pill-blue   { background:#1e3a5f; color:#60a5fa; border-color:#3b82f6; }
.r-pill-purple { background:#2e1a47; color:#c084fc; border-color:#a855f7; }
.r-pill-red    { background:#3b1219; color:#f87171; border-color:#ef4444; }
.r-pill-foil   { background:#3b2a08; color:#fbbf24; border-color:#f59e0b; }

/* Team header */
.team-bar {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 14px; border-radius: 10px;
    background: #1f2937; border: 1px solid #374151;
    cursor: pointer; margin-bottom: 4px;
}
.team-flag { font-size: 22px; }
.team-nm   { font-size: 15px; font-weight: 600; color: #f3f4f6; flex: 1; }
.team-ct   { font-size: 12px; color: #6b7280; }
.prog-bg   { height: 3px; background: #374151; border-radius: 2px; margin-bottom: 8px; }
.prog-fill { height: 3px; border-radius: 2px; background: #3b82f6; transition: width .3s; }
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
RARITY_CONFIG = {
    "base":   {"label_es":"Base",   "label_en":"Base",   "color":"#4b5563","border":"#4b5563","bg":"#1f2937","pill":"r-pill-base"},
    "blue":   {"label_es":"Azul",   "label_en":"Blue",   "color":"#3b82f6","border":"#3b82f6","bg":"#1e3a5f","pill":"r-pill-blue"},
    "purple": {"label_es":"Morado", "label_en":"Purple", "color":"#a855f7","border":"#a855f7","bg":"#2e1a47","pill":"r-pill-purple"},
    "red":    {"label_es":"Rojo",   "label_en":"Red",    "color":"#ef4444","border":"#ef4444","bg":"#3b1219","pill":"r-pill-red"},
    "foil":   {"label_es":"Foil",   "label_en":"Foil",   "color":"#f59e0b","border":"#f59e0b","bg":"#3b2a08","pill":"r-pill-foil"},
}
RARITY_STAR = {"base":"⬜","blue":"🟦","purple":"🟣","red":"🟥","foil":"🌟"}

# ── Teams ──────────────────────────────────────────────────────────────────────
TEAMS = [
    {"code":"MEX","es":"México","en":"Mexico","flag":"🇲🇽","wiki":"Mexico national football team","players_es":["Luis Malagón","Johan Vasquez","Jorge Sánchez","Cesar Montes","Jesus Gallardo","Israel Reyes","Diego Lainez","Carlos Rodriguez","Edson Alvarez","Orbelin Pineda","Marcel Ruiz","Foto del Equipo","Érick Sánchez","Hirving Lozano","Santiago Giménez","Raúl Jiménez","Alexis Vega","Roberto Alvarado","Cesar Huerta"],"players_en":["Luis Malagón","Johan Vasquez","Jorge Sánchez","Cesar Montes","Jesus Gallardo","Israel Reyes","Diego Lainez","Carlos Rodriguez","Edson Alvarez","Orbelin Pineda","Marcel Ruiz","Team Photo","Érick Sánchez","Hirving Lozano","Santiago Giménez","Raúl Jiménez","Alexis Vega","Roberto Alvarado","Cesar Huerta"]},
    {"code":"USA","es":"Estados Unidos","en":"USA","flag":"🇺🇸","wiki":"United States men's national soccer team","players_es":["Matt Freese","Chris Richards","Tim Ream","Mark McKenzie","Alex Freeman","Antonee Robinson","Tyler Adams","Tanner Tessmann","Weston McKennie","Christian Roldan","Timothy Weah","Foto del Equipo","Diego Luna","Malik Tillman","Christian Pulisic","Brenden Aaronson","Ricardo Pepi","Haji Wright","Folarin Balogun"],"players_en":["Matt Freese","Chris Richards","Tim Ream","Mark McKenzie","Alex Freeman","Antonee Robinson","Tyler Adams","Tanner Tessmann","Weston McKennie","Christian Roldan","Timothy Weah","Team Photo","Diego Luna","Malik Tillman","Christian Pulisic","Brenden Aaronson","Ricardo Pepi","Haji Wright","Folarin Balogun"]},
    {"code":"CAN","es":"Canadá","en":"Canada","flag":"🇨🇦","wiki":"Canada men's national soccer team","players_es":["Dayne St.Clair","Alphonso Davies","Alistair Johnston","Samuel Adekugbe","Riche Larvea","Derek Cornelius","Moïse Bombito","Kamal Miller","Stephen Eustáquio","Ismaël Koné","Jonathan Osorio","Foto del Equipo","Jacob Shaffelburg","Mathieu Choinière","Niko Sigur","Tajon Buchanan","Liam Millar","Cyle Larin","Jonathan David"],"players_en":["Dayne St.Clair","Alphonso Davies","Alistair Johnston","Samuel Adekugbe","Riche Larvea","Derek Cornelius","Moïse Bombito","Kamal Miller","Stephen Eustáquio","Ismaël Koné","Jonathan Osorio","Team Photo","Jacob Shaffelburg","Mathieu Choinière","Niko Sigur","Tajon Buchanan","Liam Millar","Cyle Larin","Jonathan David"]},
    {"code":"BRA","es":"Brasil","en":"Brazil","flag":"🇧🇷","wiki":"Brazil national football team","players_es":["Alisson","Bento","Marquinhos","Éder Militão","Gabriel Magalhães","Danilo","Wesley","Lucas Paquetá","Casemiro","Bruno Guimarães","Luiz Henrique","Foto del Equipo","Vinicius Júnior","Rodrygo","João Pedro","Matheus Cunha","Gabriel Martinelli","Raphinha","Estévão"],"players_en":["Alisson","Bento","Marquinhos","Éder Militão","Gabriel Magalhães","Danilo","Wesley","Lucas Paquetá","Casemiro","Bruno Guimarães","Luiz Henrique","Team Photo","Vinicius Júnior","Rodrygo","João Pedro","Matheus Cunha","Gabriel Martinelli","Raphinha","Estévão"]},
    {"code":"ARG","es":"Argentina","en":"Argentina","flag":"🇦🇷","wiki":"Argentina national football team","players_es":["Franco Armani","Emiliano Martínez","Nahuel Molina","Cristian Romero","Lisandro Martínez","Nicolás Otamendi","Marcos Acuña","Rodrigo De Paul","Leandro Paredes","Giovani Lo Celso","Ángel Di María","Foto del Equipo","Alexis Mac Allister","Nicolás González","Lautaro Martínez","Julián Álvarez","Paulo Dybala","Thiago Almada","Valentin Carboni"],"players_en":["Franco Armani","Emiliano Martínez","Nahuel Molina","Cristian Romero","Lisandro Martínez","Nicolás Otamendi","Marcos Acuña","Rodrigo De Paul","Leandro Paredes","Giovani Lo Celso","Ángel Di María","Team Photo","Alexis Mac Allister","Nicolás González","Lautaro Martínez","Julián Álvarez","Paulo Dybala","Thiago Almada","Valentin Carboni"]},
    {"code":"ENG","es":"Inglaterra","en":"England","flag":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","wiki":"England national football team","players_es":["Jordan Pickford","Dean Henderson","Reece James","John Stones","Harry Maguire","Luke Shaw","Kieran Trippier","Declan Rice","Jude Bellingham","Phil Foden","Bukayo Saka","Foto del Equipo","Morgan Rogers","Marcus Rashford","Harry Kane","Ollie Watkins","Cole Palmer","Anthony Gordon","Jarrod Bowen"],"players_en":["Jordan Pickford","Dean Henderson","Reece James","John Stones","Harry Maguire","Luke Shaw","Kieran Trippier","Declan Rice","Jude Bellingham","Phil Foden","Bukayo Saka","Team Photo","Morgan Rogers","Marcus Rashford","Harry Kane","Ollie Watkins","Cole Palmer","Anthony Gordon","Jarrod Bowen"]},
    {"code":"GER","es":"Alemania","en":"Germany","flag":"🇩🇪","wiki":"Germany national football team","players_es":["Manuel Neuer","Marc ter Stegen","Jonathan Tah","Nico Schlotterbeck","David Raum","Max Mittelstädt","Robert Andrich","Joshua Kimmich","Florian Wirtz","Ilkay Gündogan","Leon Goretzka","Foto del Equipo","Leroy Sané","Jamal Musiala","Thomas Müller","Serge Gnabry","Kai Havertz","Niclas Füllkrug","Deniz Undav"],"players_en":["Manuel Neuer","Marc ter Stegen","Jonathan Tah","Nico Schlotterbeck","David Raum","Max Mittelstädt","Robert Andrich","Joshua Kimmich","Florian Wirtz","Ilkay Gündogan","Leon Goretzka","Team Photo","Leroy Sané","Jamal Musiala","Thomas Müller","Serge Gnabry","Kai Havertz","Niclas Füllkrug","Deniz Undav"]},
    {"code":"FRA","es":"Francia","en":"France","flag":"🇫🇷","wiki":"France national football team","players_es":["Mike Maignan","Alphonse Areola","Jules Koundé","Dayot Upamecano","William Saliba","Theo Hernandez","Lucas Hernandez","Aurélien Tchouaméni","Eduardo Camavinga","Mattéo Guendouzi","Adrien Rabiot","Foto del Equipo","Antoine Griezmann","Ousmane Dembélé","Kylian Mbappé","Marcus Thuram","Randal Kolo Muani","Jonathan Clauss","Bradley Barcola"],"players_en":["Mike Maignan","Alphonse Areola","Jules Koundé","Dayot Upamecano","William Saliba","Theo Hernandez","Lucas Hernandez","Aurélien Tchouaméni","Eduardo Camavinga","Mattéo Guendouzi","Adrien Rabiot","Team Photo","Antoine Griezmann","Ousmane Dembélé","Kylian Mbappé","Marcus Thuram","Randal Kolo Muani","Jonathan Clauss","Bradley Barcola"]},
    {"code":"ESP","es":"España","en":"Spain","flag":"🇪🇸","wiki":"Spain national football team","players_es":["Unai Simón","David Raya","Dani Carvajal","Aymeric Laporte","Robin Le Normand","Alejandro Grimaldo","Jesús Navas","Rodri","Pedri","Fabián Ruiz","Dani Olmo","Foto del Equipo","Ferrán Torres","Nico Williams","Álvaro Morata","Joselu","Mikel Oyarzabal","Lamine Yamal","Yeremy Pino"],"players_en":["Unai Simón","David Raya","Dani Carvajal","Aymeric Laporte","Robin Le Normand","Alejandro Grimaldo","Jesús Navas","Rodri","Pedri","Fabián Ruiz","Dani Olmo","Team Photo","Ferrán Torres","Nico Williams","Álvaro Morata","Joselu","Mikel Oyarzabal","Lamine Yamal","Yeremy Pino"]},
    {"code":"POR","es":"Portugal","en":"Portugal","flag":"🇵🇹","wiki":"Portugal national football team","players_es":["Rui Patrício","Diogo Costa","João Cancelo","Rúben Dias","Pepe","Nuno Mendes","Danilo Pereira","Bruno Fernandes","Bernardo Silva","João Palhinha","Vitinha","Foto del Equipo","Rafael Leão","Diogo Jota","Cristiano Ronaldo","Gonçalo Ramos","Pedro Neto","João Félix","Francisco Conceição"],"players_en":["Rui Patrício","Diogo Costa","João Cancelo","Rúben Dias","Pepe","Nuno Mendes","Danilo Pereira","Bruno Fernandes","Bernardo Silva","João Palhinha","Vitinha","Team Photo","Rafael Leão","Diogo Jota","Cristiano Ronaldo","Gonçalo Ramos","Pedro Neto","João Félix","Francisco Conceição"]},
    {"code":"NED","es":"Países Bajos","en":"Netherlands","flag":"🇳🇱","wiki":"Netherlands national football team","players_es":["Bart Verbruggen","Mark Flekken","Denzel Dumfries","Virgil van Dijk","Stefan de Vrij","Nathan Aké","Tyrell Malacia","Ryan Gravenberch","Tijjani Reijnders","Teun Koopmeiners","Davy Klaassen","Foto del Equipo","Steven Bergwijn","Cody Gakpo","Memphis Depay","Wout Weghorst","Donyell Malen","Xavi Simons","Brian Brobbey"],"players_en":["Bart Verbruggen","Mark Flekken","Denzel Dumfries","Virgil van Dijk","Stefan de Vrij","Nathan Aké","Tyrell Malacia","Ryan Gravenberch","Tijjani Reijnders","Teun Koopmeiners","Davy Klaassen","Team Photo","Steven Bergwijn","Cody Gakpo","Memphis Depay","Wout Weghorst","Donyell Malen","Xavi Simons","Brian Brobbey"]},
    {"code":"ITA","es":"Italia","en":"Italy","flag":"🇮🇹","wiki":"Italy national football team","players_es":["Gianluigi Donnarumma","Alex Meret","Giovanni Di Lorenzo","Alessandro Bastoni","Federico Gatti","Federico Dimarco","Davide Frattesi","Sandro Tonali","Nicolò Barella","Lorenzo Pellegrini","Nicolò Fagioli","Foto del Equipo","Federico Chiesa","Matteo Politano","Gianluca Scamacca","Lorenzo Lucca","Giacomo Raspadori","Mateo Retegui","Wilfried Gnonto"],"players_en":["Gianluigi Donnarumma","Alex Meret","Giovanni Di Lorenzo","Alessandro Bastoni","Federico Gatti","Federico Dimarco","Davide Frattesi","Sandro Tonali","Nicolò Barella","Lorenzo Pellegrini","Nicolò Fagioli","Team Photo","Federico Chiesa","Matteo Politano","Gianluca Scamacca","Lorenzo Lucca","Giacomo Raspadori","Mateo Retegui","Wilfried Gnonto"]},
    {"code":"SCO","es":"Escocia","en":"Scotland","flag":"🏴󠁧󠁢󠁳󠁣󠁴󠁿","wiki":"Scotland national football team","players_es":["Angus Gunn","Jack Hendry","Kieran Tierney","Aaron Hickey","Andrew Robertson","Scott McKenna","John Souttar","Anthony Ralston","Grant Hanley","Scott McTominay","Billy Gilmour","Foto del Equipo","Lewis Ferguson","Ryan Christie","Kenny McLean","John McGinn","Lyndon Dykes","Che Adams","Ben Doak"],"players_en":["Angus Gunn","Jack Hendry","Kieran Tierney","Aaron Hickey","Andrew Robertson","Scott McKenna","John Souttar","Anthony Ralston","Grant Hanley","Scott McTominay","Billy Gilmour","Team Photo","Lewis Ferguson","Ryan Christie","Kenny McLean","John McGinn","Lyndon Dykes","Che Adams","Ben Doak"]},
    {"code":"CZE","es":"Chequia","en":"Czechia","flag":"🇨🇿","wiki":"Czech Republic national football team","players_es":["Matej Kovar","Jindrich Stanek","Ladislav Krejci","Vladimir Coufal","Jaroslav Zeleny","Tomas Holes","David Zima","Michal Sadilek","Lukas Provod","Lukas Cerv","Tomas Soucek","Foto del Equipo","Pavel Sulc","Matej Vydra","Vasil Kusej","Tomas Chory","Vaclav Cerny","Adam Hlozek","Patrik Schick"],"players_en":["Matej Kovar","Jindrich Stanek","Ladislav Krejci","Vladimir Coufal","Jaroslav Zeleny","Tomas Holes","David Zima","Michal Sadilek","Lukas Provod","Lukas Cerv","Tomas Soucek","Team Photo","Pavel Sulc","Matej Vydra","Vasil Kusej","Tomas Chory","Vaclav Cerny","Adam Hlozek","Patrik Schick"]},
    {"code":"NOR","es":"Noruega","en":"Norway","flag":"🇳🇴","wiki":"Norway national football team","players_es":["Orjan Nyland","Mats Selnaes","Kristoffer Ajer","Leo Ostigard","Andreas Hanche-Olsen","Birger Meling","Vegar Hedenstad","Mathias Normann","Patrick Berg","Fredrik Aursnes","Sander Berge","Foto del Equipo","Martin Odegaard","Antonio Nusa","Mohamed Elyounoussi","Erling Haaland","Alexander Sorloth","Ola Solbakken","Jens Petter Hauge"],"players_en":["Orjan Nyland","Mats Selnaes","Kristoffer Ajer","Leo Ostigard","Andreas Hanche-Olsen","Birger Meling","Vegar Hedenstad","Mathias Normann","Patrick Berg","Fredrik Aursnes","Sander Berge","Team Photo","Martin Odegaard","Antonio Nusa","Mohamed Elyounoussi","Erling Haaland","Alexander Sorloth","Ola Solbakken","Jens Petter Hauge"]},
    {"code":"SWE","es":"Suecia","en":"Sweden","flag":"🇸🇪","wiki":"Sweden national football team","players_es":["Robin Olsen","Isak Pettersson","Carl Starfelt","Victor Lindelöf","Isak Hien","Marcus Danielson","Emil Krafth","Jens Cajuste","Viktor Claesson","Hugo Larsson","Viktor Johansson","Foto del Equipo","Dejan Kulusevski","Alexander Isak","Robin Quaison","Jordan Larsson","Kristoffer Zachrisson","Emil Forsberg","Pontus Almqvist"],"players_en":["Robin Olsen","Isak Pettersson","Carl Starfelt","Victor Lindelöf","Isak Hien","Marcus Danielson","Emil Krafth","Jens Cajuste","Viktor Claesson","Hugo Larsson","Viktor Johansson","Team Photo","Dejan Kulusevski","Alexander Isak","Robin Quaison","Jordan Larsson","Kristoffer Zachrisson","Emil Forsberg","Pontus Almqvist"]},
    {"code":"AUS","es":"Australia","en":"Australia","flag":"🇦🇺","wiki":"Australia national soccer team","players_es":["Mathew Ryan","Joe Gauci","Harry Souttar","Alessandro Circati","Jordan Bos","Aziz Behich","Cameron Burgess","Lewis Miller","Milos Degenek","Jackson Irvine","Riley McGree","Foto del Equipo","Aiden O'Neill","Connor Metcalfe","Patrick Yazbek","Craig Goodwin","Kusini Yengi","Nestory Irankunda","Mohamed Touré"],"players_en":["Mathew Ryan","Joe Gauci","Harry Souttar","Alessandro Circati","Jordan Bos","Aziz Behich","Cameron Burgess","Lewis Miller","Milos Degenek","Jackson Irvine","Riley McGree","Team Photo","Aiden O'Neill","Connor Metcalfe","Patrick Yazbek","Craig Goodwin","Kusini Yengi","Nestory Irankunda","Mohamed Touré"]},
    {"code":"RSA","es":"Sudáfrica","en":"South Africa","flag":"🇿🇦","wiki":"South Africa national football team","players_es":["Ronwen Williams","Sipho Chaine","Aubrey Modiba","Samukele Kabini","Mbekezeli Mbokazi","Khulumani Ndamane","Siyabonga Ngezana","Khuliso Mudau","Nkosinathi Sibisi","Teboho Mokoena","Thalente Mbatha","Foto del Equipo","Bathasi Aubaas","Yaya Sithole","Sipho Mbule","Lyle Foster","Iqraam Rayners","Mohau Nkota","Oswin Appollis"],"players_en":["Ronwen Williams","Sipho Chaine","Aubrey Modiba","Samukele Kabini","Mbekezeli Mbokazi","Khulumani Ndamane","Siyabonga Ngezana","Khuliso Mudau","Nkosinathi Sibisi","Teboho Mokoena","Thalente Mbatha","Team Photo","Bathasi Aubaas","Yaya Sithole","Sipho Mbule","Lyle Foster","Iqraam Rayners","Mohau Nkota","Oswin Appollis"]},
    {"code":"KOR","es":"Corea del Sur","en":"South Korea","flag":"🇰🇷","wiki":"South Korea national football team","players_es":["Hyeon-woo Jo","Seung-Gyu Kim","Min-jae Kim","Yu-min Cho","Young-woo Seol","Han-beom Lee","Tae-seok Lee","Myung-jae Lee","Jae-sung Lee","In-beom Hwang","Kang-in Lee","Foto del Equipo","Seung-ho Paik","Jens Castrop","Dong-yeong Lee","Gue-sung Cho","Heung-min Son","Hee-chan Hwang","Hyeon-Gyu Oh"],"players_en":["Hyeon-woo Jo","Seung-Gyu Kim","Min-jae Kim","Yu-min Cho","Young-woo Seol","Han-beom Lee","Tae-seok Lee","Myung-jae Lee","Jae-sung Lee","In-beom Hwang","Kang-in Lee","Team Photo","Seung-ho Paik","Jens Castrop","Dong-yeong Lee","Gue-sung Cho","Heung-min Son","Hee-chan Hwang","Hyeon-Gyu Oh"]},
    {"code":"JPN","es":"Japón","en":"Japan","flag":"🇯🇵","wiki":"Japan national football team","players_es":["Shuichi Gonda","Daniel Schmidt","Takehiro Tomiyasu","Ko Itakura","Shogo Taniguchi","Yuto Nagatomo","Hiroki Ito","Wataru Endo","Ao Tanaka","Hidemasa Morita","Junya Ito","Foto del Equipo","Takumi Minamino","Kaoru Mitoma","Ritsu Doan","Ayase Ueda","Yukinari Sugawara","Daichi Kamada","Keito Nakamura"],"players_en":["Shuichi Gonda","Daniel Schmidt","Takehiro Tomiyasu","Ko Itakura","Shogo Taniguchi","Yuto Nagatomo","Hiroki Ito","Wataru Endo","Ao Tanaka","Hidemasa Morita","Junya Ito","Team Photo","Takumi Minamino","Kaoru Mitoma","Ritsu Doan","Ayase Ueda","Yukinari Sugawara","Daichi Kamada","Keito Nakamura"]},
    {"code":"EGY","es":"Egipto","en":"Egypt","flag":"🇪🇬","wiki":"Egypt national football team","players_es":["Mohamed Abou Gabal","Mohamed El-Shenawy","Ahmed Hegazy","Omar Kamal","Mohamed Abdelmonem","Akram Tawfik","Mahmoud El Wensh","Amr El Sulaya","Mohamed Elneny","Taher Mohamed Taher","Mohamed Hamdy","Foto del Equipo","Emam Ashour","Zizo","Omar Marmoush","Mostafa Mohamed","Hussein El Shahat","Marwan Attia","Trezeguet"],"players_en":["Mohamed Abou Gabal","Mohamed El-Shenawy","Ahmed Hegazy","Omar Kamal","Mohamed Abdelmonem","Akram Tawfik","Mahmoud El Wensh","Amr El Sulaya","Mohamed Elneny","Taher Mohamed Taher","Mohamed Hamdy","Team Photo","Emam Ashour","Zizo","Omar Marmoush","Mostafa Mohamed","Hussein El Shahat","Marwan Attia","Trezeguet"]},
    {"code":"IRN","es":"Irán","en":"Iran","flag":"🇮🇷","wiki":"Iran national football team","players_es":["Alireza Beiranvand","Amir Abedzadeh","Shoja Khalilzadeh","Majid Hosseini","Hossein Kanaanizadegan","Milad Mohammadi","Roozbeh Cheshmi","Saeid Ezatolahi","Ali Karimi","Mehdi Torabi","Ahmad Noorollahi","Foto del Equipo","Sardar Azmoun","Saman Ghoddos","Karim Ansarifard","Mehdi Taremi","Ali Gholizadeh","Allahyar Sayyadmanesh","Omid Noorafkan"],"players_en":["Alireza Beiranvand","Amir Abedzadeh","Shoja Khalilzadeh","Majid Hosseini","Hossein Kanaanizadegan","Milad Mohammadi","Roozbeh Cheshmi","Saeid Ezatolahi","Ali Karimi","Mehdi Torabi","Ahmad Noorollahi","Team Photo","Sardar Azmoun","Saman Ghoddos","Karim Ansarifard","Mehdi Taremi","Ali Gholizadeh","Allahyar Sayyadmanesh","Omid Noorafkan"]},
    {"code":"QAT","es":"Catar","en":"Qatar","flag":"🇶🇦","wiki":"Qatar national football team","players_es":["Meshaal Barsham","Sultan Albrake","Lucas Mendes","Homam Ahmed","Boualem Khoukhi","Pedro Miguel","Tarek Salman","Mohamed Al-Mannai","Karim Boudiaf","Assim Madibo","Ahmed Fatehi","Foto del Equipo","Mohammed Waad","Abdulaziz Hatem","Hassan Al-Haydos","Edmilson Junior","Akram Afif","Ahmed Al Ganehi","Almoez Ali"],"players_en":["Meshaal Barsham","Sultan Albrake","Lucas Mendes","Homam Ahmed","Boualem Khoukhi","Pedro Miguel","Tarek Salman","Mohamed Al-Mannai","Karim Boudiaf","Assim Madibo","Ahmed Fatehi","Team Photo","Mohammed Waad","Abdulaziz Hatem","Hassan Al-Haydos","Edmilson Junior","Akram Afif","Ahmed Al Ganehi","Almoez Ali"]},
    {"code":"SUI","es":"Suiza","en":"Switzerland","flag":"🇨🇭","wiki":"Switzerland national football team","players_es":["Gregor Kobel","Yvon Mvogo","Manuel Akanji","Ricardo Rodriguez","Nico Elvedi","Aurèle Amenda","Silvan Widmer","Granit Xhaka","Denis Zakaria","Remo Freuler","Fabian Rieder","Foto del Equipo","Ardon Jashari","Johan Manzambi","Michel Aebischer","Breel Embolo","Ruben Vargas","Dan Ndoye","Zeki Amdouni"],"players_en":["Gregor Kobel","Yvon Mvogo","Manuel Akanji","Ricardo Rodriguez","Nico Elvedi","Aurèle Amenda","Silvan Widmer","Granit Xhaka","Denis Zakaria","Remo Freuler","Fabian Rieder","Team Photo","Ardon Jashari","Johan Manzambi","Michel Aebischer","Breel Embolo","Ruben Vargas","Dan Ndoye","Zeki Amdouni"]},
    {"code":"MAR","es":"Marruecos","en":"Morocco","flag":"🇲🇦","wiki":"Morocco national football team","players_es":["Yassine Bounou","Munir El Kajoui","Achraf Hakimi","Noussair Mazraoui","Nayef Aguerd","Roman Saiss","Jawad El Yamiq","Adam Masina","Sofyan Amrabat","Azzedine Ounahi","Eliesse Ben Seghir","Foto del Equipo","Bilal El Khannouss","Ismael Saibari","Youssef En-Nesyri","Abde Ezzalzouli","Soufiane Rahimi","Brahim Diaz","Ayoub El Kaabi"],"players_en":["Yassine Bounou","Munir El Kajoui","Achraf Hakimi","Noussair Mazraoui","Nayef Aguerd","Roman Saiss","Jawad El Yamiq","Adam Masina","Sofyan Amrabat","Azzedine Ounahi","Eliesse Ben Seghir","Team Photo","Bilal El Khannouss","Ismael Saibari","Youssef En-Nesyri","Abde Ezzalzouli","Soufiane Rahimi","Brahim Diaz","Ayoub El Kaabi"]},
    {"code":"COL","es":"Colombia","en":"Colombia","flag":"🇨🇴","wiki":"Colombia national football team","players_es":["David Ospina","Camilo Vargas","Davinson Sánchez","Yerry Mina","Daniel Muñoz","Johan Mojica","Lerma","Wilmar Barrios","Mateus Uribe","Luis Díaz","James Rodríguez","Foto del Equipo","Rafael Santos Borré","Cucho Hernández","Falcao","Jhon Córdoba","Miguel Borja","Jhon Durán","Jhon Arias"],"players_en":["David Ospina","Camilo Vargas","Davinson Sánchez","Yerry Mina","Daniel Muñoz","Johan Mojica","Lerma","Wilmar Barrios","Mateus Uribe","Luis Díaz","James Rodríguez","Team Photo","Rafael Santos Borré","Cucho Hernández","Falcao","Jhon Córdoba","Miguel Borja","Jhon Durán","Jhon Arias"]},
    {"code":"URU","es":"Uruguay","en":"Uruguay","flag":"🇺🇾","wiki":"Uruguay national football team","players_es":["Fernando Muslera","Sergio Rochet","Ronald Araújo","José María Giménez","Mathías Olivera","Nahitan Nández","Lucas Torreira","Federico Valverde","Rodrigo Bentancur","Giorgian De Arrascaeta","Facundo Pellistri","Foto del Equipo","Darwin Núñez","Luis Suárez","Edinson Cavani","Maxi Gómez","Brian Rodríguez","Agustín Canobbio","Ignacio De La Cruz"],"players_en":["Fernando Muslera","Sergio Rochet","Ronald Araújo","José María Giménez","Mathías Olivera","Nahitan Nández","Lucas Torreira","Federico Valverde","Rodrigo Bentancur","Giorgian De Arrascaeta","Facundo Pellistri","Team Photo","Darwin Núñez","Luis Suárez","Edinson Cavani","Maxi Gómez","Brian Rodríguez","Agustín Canobbio","Ignacio De La Cruz"]},
    {"code":"GHA","es":"Ghana","en":"Ghana","flag":"🇬🇭","wiki":"Ghana national football team","players_es":["Lawrence Ati-Zigi","Jojo Wollacott","Andy Yiadom","Alexander Djiku","Daniel Amartey","Alidu Seidu","Baba Rahman","Thomas Partey","Salis Abdul Samed","Mohammed Kudus","Emmanuel Gyasi","Foto del Equipo","Antoine Semenyo","Jordan Ayew","Andre Ayew","Felix Afena-Gyan","Gideon Mensah","Kamaldeen Sulemana","Inaki Williams"],"players_en":["Lawrence Ati-Zigi","Jojo Wollacott","Andy Yiadom","Alexander Djiku","Daniel Amartey","Alidu Seidu","Baba Rahman","Thomas Partey","Salis Abdul Samed","Mohammed Kudus","Emmanuel Gyasi","Team Photo","Antoine Semenyo","Jordan Ayew","Andre Ayew","Felix Afena-Gyan","Gideon Mensah","Kamaldeen Sulemana","Inaki Williams"]},
    {"code":"SEN","es":"Senegal","en":"Senegal","flag":"🇸🇳","wiki":"Senegal national football team","players_es":["Edouard Mendy","Seny Dieng","Kalidou Koulibaly","Abdou Diallo","Ismail Jakobs","Formose Mendy","Pape Abou Cissé","Lamine Camara","Idrissa Gana Gueye","Nampalys Mendy","Krepin Diatta","Foto del Equipo","Iliman Ndiaye","Boulaye Dia","Sadio Mané","Nicolas Jackson","Ismaila Sarr","Habib Diallo","Yehvann Diouf"],"players_en":["Edouard Mendy","Seny Dieng","Kalidou Koulibaly","Abdou Diallo","Ismail Jakobs","Formose Mendy","Pape Abou Cissé","Lamine Camara","Idrissa Gana Gueye","Nampalys Mendy","Krepin Diatta","Team Photo","Iliman Ndiaye","Boulaye Dia","Sadio Mané","Nicolas Jackson","Ismaila Sarr","Habib Diallo","Yehvann Diouf"]},
    {"code":"NGA","es":"Nigeria","en":"Nigeria","flag":"🇳🇬","wiki":"Nigeria national football team","players_es":["Francis Uzoho","Stanley Nwabali","Semi Ajayi","William Troost-Ekong","Zaidu Sanusi","Bright Osayi-Samuel","Ola Aina","Frank Onyeka","Alex Iwobi","Wilfred Ndidi","Kelechi Iheanacho","Foto del Equipo","Samuel Chukwueze","Ademola Lookman","Moses Simon","Victor Osimhen","Terem Moffi","Taiwo Awoniyi","Cyriel Dessers"],"players_en":["Francis Uzoho","Stanley Nwabali","Semi Ajayi","William Troost-Ekong","Zaidu Sanusi","Bright Osayi-Samuel","Ola Aina","Frank Onyeka","Alex Iwobi","Wilfred Ndidi","Kelechi Iheanacho","Team Photo","Samuel Chukwueze","Ademola Lookman","Moses Simon","Victor Osimhen","Terem Moffi","Taiwo Awoniyi","Cyriel Dessers"]},
    {"code":"TUR","es":"Turquía","en":"Türkiye","flag":"🇹🇷","wiki":"Turkey national football team","players_es":["Ugurcan Cakir","Mert Gunok","Çaglar Söyüncü","Merih Demiral","Samet Akaydin","Ferdi Kadioglu","Zeki Celik","Hakan Calhanoglu","Kaan Ayhan","Orkun Kökcü","Kenan Yildiz","Foto del Equipo","Arda Güler","Yunus Akgun","Baris Alper Yilmaz","Efecan Karaca","Cenk Tosun","Umut Bozok","Serdar Dursun"],"players_en":["Ugurcan Cakir","Mert Gunok","Çaglar Söyüncü","Merih Demiral","Samet Akaydin","Ferdi Kadioglu","Zeki Celik","Hakan Calhanoglu","Kaan Ayhan","Orkun Kökcü","Kenan Yildiz","Team Photo","Arda Güler","Yunus Akgun","Baris Alper Yilmaz","Efecan Karaca","Cenk Tosun","Umut Bozok","Serdar Dursun"]},
    {"code":"AUT","es":"Austria","en":"Austria","flag":"🇦🇹","wiki":"Austria national football team","players_es":["Patrick Pentz","Heinz Lindner","Stefan Posch","David Alaba","Gernot Trauner","Philipp Mwene","Maximilian Wöber","Nicolas Seiwald","Konrad Laimer","Marcel Sabitzer","Xaver Schlager","Foto del Equipo","Florian Kainz","Patrick Wimmer","Marko Arnautovic","Michael Gregoritsch","Christoph Baumgartner","Louis Schaub","Romano Schmid"],"players_en":["Patrick Pentz","Heinz Lindner","Stefan Posch","David Alaba","Gernot Trauner","Philipp Mwene","Maximilian Wöber","Nicolas Seiwald","Konrad Laimer","Marcel Sabitzer","Xaver Schlager","Team Photo","Florian Kainz","Patrick Wimmer","Marko Arnautovic","Michael Gregoritsch","Christoph Baumgartner","Louis Schaub","Romano Schmid"]},
    {"code":"BIH","es":"Bosnia y Herz.","en":"Bosnia & Herz.","flag":"🇧🇦","wiki":"Bosnia and Herzegovina national football team","players_es":["Nikola Vasilj","Amer Dedic","Sead Kolasinac","Tarik Muharemovic","Nihad Mujakic","Nikola Katic","Amir Hadziahmetovic","Benjamin Tahirovic","Armin Gigovic","Ivan Sunjic","Ivan Basic","Foto del Equipo","Dzenis Burnic","Esmir Bajraktarevic","Amar Memic","Ermedin Demirovic","Edin Dzeko","Samed Bazdar","Haris Tabakovic"],"players_en":["Nikola Vasilj","Amer Dedic","Sead Kolasinac","Tarik Muharemovic","Nihad Mujakic","Nikola Katic","Amir Hadziahmetovic","Benjamin Tahirovic","Armin Gigovic","Ivan Sunjic","Ivan Basic","Team Photo","Dzenis Burnic","Esmir Bajraktarevic","Amar Memic","Ermedin Demirovic","Edin Dzeko","Samed Bazdar","Haris Tabakovic"]},
    {"code":"UZB","es":"Uzbekistán","en":"Uzbekistan","flag":"🇺🇿","wiki":"Uzbekistan national football team","players_es":["Utkir Yusupov","Sherzod Nishonov","Sherzod Qoraboyev","Khurshid Tursunov","Akbar Bobojonov","Timur Jorayev","Oston Urunov","Jaloliddin Masharipov","Odil Akhmedov","Farrukh Tashkentov","Jamshid Iskanderov","Foto del Equipo","Eldor Shomurodov","Abbosbek Fayzullaev","Sherzod Nasrullaev","Bobur Abdixoliqov","Otabek Shukurov","Dostonbek Xolmatov","Khojiakbar Alijonov"],"players_en":["Utkir Yusupov","Sherzod Nishonov","Sherzod Qoraboyev","Khurshid Tursunov","Akbar Bobojonov","Timur Jorayev","Oston Urunov","Jaloliddin Masharipov","Odil Akhmedov","Farrukh Tashkentov","Jamshid Iskanderov","Team Photo","Eldor Shomurodov","Abbosbek Fayzullaev","Sherzod Nasrullaev","Bobur Abdixoliqov","Otabek Shukurov","Dostonbek Xolmatov","Khojiakbar Alijonov"]},
    {"code":"HAI","es":"Haití","en":"Haiti","flag":"🇭🇹","wiki":"Haiti national football team","players_es":["Johny Placide","Carlens Arcus","Martin Expérience","Jean-Kevin Duverne","Ricardo Adé","Duke Lacroix","Garven Metusala","Hannes Delcroix","Leverton Pierre","Danley Jean Jacques","Jean-Ricner Bellegarde","Foto del Equipo","Christopher Attys","Derrick Etienne Jr","Josue Casimir","Ruben Providence","Duckens Nazon","Louicius Deedson","Frantzdy Pierrot"],"players_en":["Johny Placide","Carlens Arcus","Martin Expérience","Jean-Kevin Duverne","Ricardo Adé","Duke Lacroix","Garven Metusala","Hannes Delcroix","Leverton Pierre","Danley Jean Jacques","Jean-Ricner Bellegarde","Team Photo","Christopher Attys","Derrick Etienne Jr","Josue Casimir","Ruben Providence","Duckens Nazon","Louicius Deedson","Frantzdy Pierrot"]},
    {"code":"PAR","es":"Paraguay","en":"Paraguay","flag":"🇵🇾","wiki":"Paraguay national football team","players_es":["Roberto Fernandez","Orlando Gill","Gustavo Gomez","Fabián Balbuena","Juan José Cáceres","Omar Alderete","Junior Alonso","Mathías Villasanti","Diego Gomez","Damián Bobadilla","Andres Cubas","Foto del Equipo","Matias Galarza","Julio Enciso","Alejandro Romero","Miguel Almirón","Ramon Sosa","Angel Romero","Antonio Sanabria"],"players_en":["Roberto Fernandez","Orlando Gill","Gustavo Gomez","Fabián Balbuena","Juan José Cáceres","Omar Alderete","Junior Alonso","Mathías Villasanti","Diego Gomez","Damián Bobadilla","Andres Cubas","Team Photo","Matias Galarza","Julio Enciso","Alejandro Romero","Miguel Almirón","Ramon Sosa","Angel Romero","Antonio Sanabria"]},
    {"code":"ECU","es":"Ecuador","en":"Ecuador","flag":"🇪🇨","wiki":"Ecuador national football team","players_es":["Hernán Galíndez","Alexander Domínguez","Ángelo Preciado","Piero Hincapié","Jackson Porozo","Pervis Estupiñán","Diego Palacios","Carlos Gruezo","Jhegson Méndez","Moisés Caicedo","Jeremy Sarmiento","Foto del Equipo","Gonzalo Plata","Michael Estrada","Romario Ibarra","Enner Valencia","Ángel Mena","Jordy Caicedo","Leonardo Campana"],"players_en":["Hernán Galíndez","Alexander Domínguez","Ángelo Preciado","Piero Hincapié","Jackson Porozo","Pervis Estupiñán","Diego Palacios","Carlos Gruezo","Jhegson Méndez","Moisés Caicedo","Jeremy Sarmiento","Team Photo","Gonzalo Plata","Michael Estrada","Romario Ibarra","Enner Valencia","Ángel Mena","Jordy Caicedo","Leonardo Campana"]},
    {"code":"IRQ","es":"Irak","en":"Iraq","flag":"🇮🇶","wiki":"Iraq national football team","players_es":["Jalal Hassan","Fahad Tariq","Ali Adnan","Saad Natiq","Rebin Sulaka","Ahmed Ibrahim","Mustafa Nadhim","Hussein Ali","Amjad Attwan","Osama Rashid","Bashar Resan","Foto del Equipo","Mohanad Ali","Amir Al Ammari","Aymen Hussein","Ali Jasim","Ibrahim Bayesh","Alaa Abbas","Amir Al Saddah"],"players_en":["Jalal Hassan","Fahad Tariq","Ali Adnan","Saad Natiq","Rebin Sulaka","Ahmed Ibrahim","Mustafa Nadhim","Hussein Ali","Amjad Attwan","Osama Rashid","Bashar Resan","Team Photo","Mohanad Ali","Amir Al Ammari","Aymen Hussein","Ali Jasim","Ibrahim Bayesh","Alaa Abbas","Amir Al Saddah"]},
    {"code":"CMR","es":"Camerún","en":"Cameroon","flag":"🇨🇲","wiki":"Cameroon national football team","players_es":["André Onana","Fabrice Ondoa","Harold Moukoudi","Jean-Charles Castelletto","Collins Fai","Ambroise Oyongo","Nicolas Nkoulou","Samuel Oum Gouet","Frank Zambo Anguissa","Pierre Kunde","Martin Hongla","Foto del Equipo","Bryan Mbeumo","Karl Toko Ekambi","Vincent Aboubakar","Eric Choupo-Moting","Stéphane Bahoken","Georges-Kevin N'Koudou","Ignatius Ganago"],"players_en":["André Onana","Fabrice Ondoa","Harold Moukoudi","Jean-Charles Castelletto","Collins Fai","Ambroise Oyongo","Nicolas Nkoulou","Samuel Oum Gouet","Frank Zambo Anguissa","Pierre Kunde","Martin Hongla","Team Photo","Bryan Mbeumo","Karl Toko Ekambi","Vincent Aboubakar","Eric Choupo-Moting","Stéphane Bahoken","Georges-Kevin N'Koudou","Ignatius Ganago"]},
    {"code":"CIV","es":"Costa de Marfil","en":"Côte d'Ivoire","flag":"🇨🇮","wiki":"Ivory Coast national football team","players_es":["Yahia Fofana","Badra Sangaré","Simon Deli","Willy Boly","Serge Aurier","Ghislain Konan","Wilfried Kanon","Ibrahim Sangaré","Jean-Michaël Seri","Franck Kessie","Sekou Sanogo","Foto del Equipo","Nicolas Pépé","Jonathan Bamba","Wilfried Zaha","Sébastien Haller","Simon Adingra","Oumar Diakité","Odilon Kossounou"],"players_en":["Yahia Fofana","Badra Sangaré","Simon Deli","Willy Boly","Serge Aurier","Ghislain Konan","Wilfried Kanon","Ibrahim Sangaré","Jean-Michaël Seri","Franck Kessie","Sekou Sanogo","Team Photo","Nicolas Pépé","Jonathan Bamba","Wilfried Zaha","Sébastien Haller","Simon Adingra","Oumar Diakité","Odilon Kossounou"]},
    {"code":"CHI","es":"Chile","en":"Chile","flag":"🇨🇱","wiki":"Chile national football team","players_es":["Brayan Cortés","Gabriel Arias","Paulo Díaz","Guillermo Maripán","Benjamín Kuscevic","Mauricio Isla","Gabriel Suazo","Arturo Vidal","Charles Aránguiz","Erick Pulgar","César Pinares","Foto del Equipo","Alexis Sánchez","Eduardo Vargas","Sebastián Driussi","Víctor Dávila","Marcos Bolados","Jean Meneses","Darío Osorio"],"players_en":["Brayan Cortés","Gabriel Arias","Paulo Díaz","Guillermo Maripán","Benjamín Kuscevic","Mauricio Isla","Gabriel Suazo","Arturo Vidal","Charles Aránguiz","Erick Pulgar","César Pinares","Team Photo","Alexis Sánchez","Eduardo Vargas","Sebastián Driussi","Víctor Dávila","Marcos Bolados","Jean Meneses","Darío Osorio"]},
    {"code":"PAN","es":"Panamá","en":"Panama","flag":"🇵🇦","wiki":"Panama national football team","players_es":["Luis Mejía","Orlando Mosquera","Harold Cummings","Eric Davis","Anibal Godoy","Fidel Escobar","Adalberto Carrasquilla","Roderick Miller","Édgar Bárcenas","Rolando Blackburn","Alberto Quintero","Foto del Equipo","Cecilio Waterman","Abdiel Ayarza","Ismael Díaz","Freddie Hall","José Fajardo","Blas Pérez","Giovanny Ramos"],"players_en":["Luis Mejía","Orlando Mosquera","Harold Cummings","Eric Davis","Anibal Godoy","Fidel Escobar","Adalberto Carrasquilla","Roderick Miller","Édgar Bárcenas","Rolando Blackburn","Alberto Quintero","Team Photo","Cecilio Waterman","Abdiel Ayarza","Ismael Díaz","Freddie Hall","José Fajardo","Blas Pérez","Giovanny Ramos"]},
    {"code":"CRC","es":"Costa Rica","en":"Costa Rica","flag":"🇨🇷","wiki":"Costa Rica national football team","players_es":["Keylor Navas","Esteban Alvarado","Keysher Fuller","Francisco Calvo","Juan Pablo Vargas","Bryan Oviedo","Kendall Waston","Yeltsin Tejeda","Douglas Sequeira","Celso Borges","Joel Campbell","Foto del Equipo","Brandon Aguilera","Jewison Bennette","Álvaro Zamora","Anthony Contreras","Alonso Martínez","Johan Venegas","Bryan Ruiz"],"players_en":["Keylor Navas","Esteban Alvarado","Keysher Fuller","Francisco Calvo","Juan Pablo Vargas","Bryan Oviedo","Kendall Waston","Yeltsin Tejeda","Douglas Sequeira","Celso Borges","Joel Campbell","Team Photo","Brandon Aguilera","Jewison Bennette","Álvaro Zamora","Anthony Contreras","Alonso Martínez","Johan Venegas","Bryan Ruiz"]},
    {"code":"HON","es":"Honduras","en":"Honduras","flag":"🇭🇳","wiki":"Honduras national football team","players_es":["Luis López","Edrick Menjívar","Denil Maldonado","Marcelo Pereira","Devron García","Kervin Arriaga","Maynor Figueroa","Alberth Elis","Romell Quioto","Rigoberto Rivas","Edwin Rodríguez","Foto del Equipo","Jorge Benguché","Andy Najar","Michaell Chirinos","Eddie Hernández","Alexander López","Deybi Flores","Joaquín Arias"],"players_en":["Luis López","Edrick Menjívar","Denil Maldonado","Marcelo Pereira","Devron García","Kervin Arriaga","Maynor Figueroa","Alberth Elis","Romell Quioto","Rigoberto Rivas","Edwin Rodríguez","Team Photo","Jorge Benguché","Andy Najar","Michaell Chirinos","Eddie Hernández","Alexander López","Deybi Flores","Joaquín Arias"]},
    {"code":"JAM","es":"Jamaica","en":"Jamaica","flag":"🇯🇲","wiki":"Jamaica national football team","players_es":["Andre Blake","Dillon Barnes","Damion Lowe","Adrian Mariappa","Liam Moore","Greg Leigh","Javain Brown","Rolando Aarons","Daniel Johnson","Je-Vaughn Watson","Bobby Decordova-Reid","Foto del Equipo","Michail Antonio","Leon Bailey","Shamar Nicholson","Cory Burke","Oniel Fisher","Chedwyn Evans","Demarai Gray"],"players_en":["Andre Blake","Dillon Barnes","Damion Lowe","Adrian Mariappa","Liam Moore","Greg Leigh","Javain Brown","Rolando Aarons","Daniel Johnson","Je-Vaughn Watson","Bobby Decordova-Reid","Team Photo","Michail Antonio","Leon Bailey","Shamar Nicholson","Cory Burke","Oniel Fisher","Chedwyn Evans","Demarai Gray"]},
]

# ── Google Sheets ──────────────────────────────────────────────────────────────
@st.cache_resource
def get_sheet(tab_name):
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        scopes = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open("fifa2026_tracker")
        try:
            sheet = spreadsheet.worksheet(tab_name)
        except:
            sheet = spreadsheet.add_worksheet(title=tab_name, rows=1100, cols=3)
            sheet.append_row(["sticker_id","owned","rarity"])
        return sheet
    except Exception as e:
        st.sidebar.error(f"Sheets error: {e}")
        return None

def load_data(sheet):
    owned, rarity_map = set(), {}
    try:
        rows = sheet.get_all_records()
        for row in rows:
            sid = str(row.get("sticker_id","")).strip()
            if not sid: continue
            if str(row.get("owned","")).strip().upper() == "TRUE":
                owned.add(sid)
            r = str(row.get("rarity","base")).strip().lower()
            if r in RARITY_CONFIG:
                rarity_map[sid] = r
    except: pass
    return owned, rarity_map

def batch_save(sheet, owned, rarity_map, all_ids):
    """Rewrite entire sheet from current state."""
    try:
        rows = [["sticker_id","owned","rarity"]]
        for sid in all_ids:
            rows.append([sid, str(sid in owned), rarity_map.get(sid,"base")])
        sheet.clear()
        sheet.update("A1", rows)
    except Exception as e:
        st.warning(f"Save error: {e}")

# ── Wikipedia photo (improved search) ─────────────────────────────────────────
@st.cache_data(ttl=86400, show_spinner=False)
def get_photo_url(query: str, is_team: bool = False) -> str | None:
    try:
        # First try exact page
        params = {"action":"query","format":"json","prop":"pageimages",
                  "titles":query,"pithumbsize":300,"pilimit":1,"redirects":1}
        r = requests.get("https://en.wikipedia.org/w/api.php", params=params, timeout=5)
        pages = r.json().get("query",{}).get("pages",{})
        for page in pages.values():
            url = page.get("thumbnail",{}).get("source")
            if url and "svg" not in url.lower():
                return url
        # Fallback: search
        params2 = {"action":"query","format":"json","list":"search",
                   "srsearch": query + (" football" if not is_team else ""),
                   "srlimit":1}
        r2 = requests.get("https://en.wikipedia.org/w/api.php", params=params2, timeout=5)
        results = r2.json().get("query",{}).get("search",[])
        if results:
            title = results[0]["title"]
            params3 = {"action":"query","format":"json","prop":"pageimages",
                       "titles":title,"pithumbsize":300,"pilimit":1}
            r3 = requests.get("https://en.wikipedia.org/w/api.php", params=params3, timeout=5)
            pages3 = r3.json().get("query",{}).get("pages",{})
            for page in pages3.values():
                url = page.get("thumbnail",{}).get("source")
                if url and "svg" not in url.lower():
                    return url
    except: pass
    return None

@st.cache_data(ttl=86400, show_spinner=False)
def get_img_b64(url: str) -> str | None:
    try:
        r = requests.get(url, timeout=5)
        img = Image.open(BytesIO(r.content)).convert("RGB")
        img.thumbnail((120, 140))
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=80)
        return base64.b64encode(buf.getvalue()).decode()
    except: return None

# ── Build sticker list ─────────────────────────────────────────────────────────
def build_stickers():
    all_s = []
    for t in TEAMS:
        # Badge (X1)
        all_s.append({"id":f"{t['code']}1","name_es":"Escudo","name_en":"Badge",
                       "team":t["code"],"flag":t["flag"],"wiki":t["wiki"],
                       "default_rarity":"foil","stype":"badge"})
        for i,(p_es,p_en) in enumerate(zip(t["players_es"],t["players_en"])):
            num = i+2
            is_photo = "Foto" in p_es or "Photo" in p_en
            all_s.append({"id":f"{t['code']}{num}","name_es":p_es,"name_en":p_en,
                           "team":t["code"],"flag":t["flag"],"wiki":t["wiki"],
                           "default_rarity":"foil" if is_photo else "base",
                           "stype":"team_photo" if is_photo else "player"})
    return all_s

ALL_STICKERS = build_stickers()
ALL_IDS = [s["id"] for s in ALL_STICKERS]

# ── Session state ──────────────────────────────────────────────────────────────
for k,v in [("version","mx"),("mx_owned",set()),("mx_rarity",{}),
             ("usa_owned",set()),("usa_rarity",{}),
             ("mx_loaded",False),("usa_loaded",False),("dirty",False)]:
    if k not in st.session_state:
        st.session_state[k] = v

ver = st.session_state.version
lang = "es" if ver=="mx" else "en"
tab_name = "mexico_tracker" if ver=="mx" else "usa_tracker"
sheet = get_sheet(tab_name)

if ver=="mx" and not st.session_state.mx_loaded and sheet:
    o,r = load_data(sheet)
    st.session_state.mx_owned=o; st.session_state.mx_rarity=r
    st.session_state.mx_loaded=True
elif ver=="usa" and not st.session_state.usa_loaded and sheet:
    o,r = load_data(sheet)
    st.session_state.usa_owned=o; st.session_state.usa_rarity=r
    st.session_state.usa_loaded=True

owned    = st.session_state.mx_owned   if ver=="mx" else st.session_state.usa_owned
rmap     = st.session_state.mx_rarity  if ver=="mx" else st.session_state.usa_rarity
show_rar = (ver=="usa")

def get_r(sid, default): return rmap.get(sid, default)

# ── Save button (manual batch save) ───────────────────────────────────────────
def do_save():
    if sheet:
        batch_save(sheet, owned, rmap, ALL_IDS)
        st.session_state.dirty = False

# ── Version toggle ─────────────────────────────────────────────────────────────
c1,c2,c3 = st.columns([1,2,1])
with c2:
    t1,t2 = st.columns(2)
    with t1:
        if st.button("🇲🇽 Versión México", use_container_width=True,
                     type="primary" if ver=="mx" else "secondary"):
            if st.session_state.dirty: do_save()
            st.session_state.version="mx"; st.rerun()
    with t2:
        if st.button("🇺🇸 USA Version", use_container_width=True,
                     type="primary" if ver=="usa" else "secondary"):
            if st.session_state.dirty: do_save()
            st.session_state.version="usa"; st.rerun()

st.markdown("---")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"## ⚽ {'Álbum FIFA 2026' if lang=='es' else 'FIFA 2026 Tracker'}")
    total = len(ALL_STICKERS)
    own_n = len(owned)
    pct   = round(own_n/total*100,1)
    st.metric("Colección" if lang=="es" else "Collection", f"{own_n}/{total}", f"{pct}%")

    if show_rar:
        c1s,c2s = st.columns(2)
        c1s.metric("🌟 Foil",   sum(1 for s in ALL_STICKERS if s["id"] in owned and get_r(s["id"],s["default_rarity"])=="foil"))
        c2s.metric("🟦 Blue",   sum(1 for s in ALL_STICKERS if s["id"] in owned and get_r(s["id"],s["default_rarity"])=="blue"))
        c1s.metric("🟣 Purple", sum(1 for s in ALL_STICKERS if s["id"] in owned and get_r(s["id"],s["default_rarity"])=="purple"))
        c2s.metric("🟥 Red",    sum(1 for s in ALL_STICKERS if s["id"] in owned and get_r(s["id"],s["default_rarity"])=="red"))

    st.markdown("---")
    search = st.text_input("🔍 Buscar" if lang=="es" else "🔍 Search","")
    flt_owned = st.selectbox(
        "Mostrar" if lang=="es" else "Show",
        ["Todos","Solo tengo","Me faltan"] if lang=="es" else ["All","Owned only","Missing only"])
    sel_team = st.selectbox(
        "Equipo" if lang=="es" else "Team",
        (["Todos los equipos"] if lang=="es" else ["All teams"]) + [t["es" if lang=="es" else "en"] for t in TEAMS])

    if show_rar:
        st.markdown("---")
        st.markdown("**Rareza / Rarity**")
        for k,rc in RARITY_CONFIG.items():
            st.markdown(f"{RARITY_STAR[k]} **{rc['label_en']}** — border color")

    st.markdown("---")
    if st.button("💾 Guardar cambios" if lang=="es" else "💾 Save changes", use_container_width=True):
        do_save()
        st.success("¡Guardado!" if lang=="es" else "Saved!")

# ── Main: team grid ────────────────────────────────────────────────────────────
title = "## 📋 Copa Mundial FIFA 2026 — Mi Álbum" if lang=="es" else "## 📋 FIFA World Cup 2026 — Sticker Collection"
st.markdown(title)

for t in TEAMS:
    tname = t["es"] if lang=="es" else t["en"]
    all_s_team = [s for s in ALL_STICKERS if s["team"]==t["code"]]

    # Filter
    show_s = []
    for s in all_s_team:
        nm = s["name_es"] if lang=="es" else s["name_en"]
        if search and search.lower() not in nm.lower() and search.lower() not in tname.lower():
            continue
        is_owned = s["id"] in owned
        if flt_owned in ("Solo tengo","Owned only") and not is_owned: continue
        if flt_owned in ("Me faltan","Missing only") and is_owned: continue
        show_s.append(s)

    if sel_team not in ("Todos los equipos","All teams") and tname != sel_team:
        continue
    if not show_s: continue

    t_own = sum(1 for s in all_s_team if s["id"] in owned)
    t_tot = len(all_s_team)
    t_pct = round(t_own/t_tot*100)

    with st.expander(f"{t['flag']} **{tname}** — {t_own}/{t_tot} ({t_pct}%)",
                     expanded=(sel_team not in ("Todos los equipos","All teams"))):
        prog_html = f'<div class="prog-bg"><div class="prog-fill" style="width:{t_pct}%"></div></div>'
        st.markdown(prog_html, unsafe_allow_html=True)

        # Render in rows of 5
        for row_start in range(0, len(show_s), 5):
            row_s = show_s[row_start:row_start+5]
            cols = st.columns(5)
            for ci, s in enumerate(row_s):
                with cols[ci]:
                    sid      = s["id"]
                    is_owned = sid in owned
                    r        = get_r(sid, s["default_rarity"])
                    rc       = RARITY_CONFIG[r]
                    nm       = s["name_es"] if lang=="es" else s["name_en"]
                    short_nm = nm[:14]+"…" if len(nm)>14 else nm
                    border_cls = f"r-{r}" if show_rar else "r-none"
                    state_cls  = "s-owned" if is_owned else "s-missing"

                    # Fetch photo
                    photo_html = ""
                    if s["stype"] == "badge":
                        url = get_photo_url(s["wiki"], is_team=True)
                    elif s["stype"] == "team_photo":
                        url = get_photo_url(s["wiki"]+" squad", is_team=True)
                    else:
                        url = get_photo_url(s["name_en"]+" footballer")
                    
                    if url:
                        b64 = get_img_b64(url)
                        if b64:
                            photo_html = f'<img class="s-img" src="data:image/jpeg;base64,{b64}" alt="{nm}"/>'
                    if not photo_html:
                        emoji = "🛡️" if s["stype"]=="badge" else ("👥" if s["stype"]=="team_photo" else "⚽")
                        photo_html = f'<div class="s-placeholder">{emoji}</div>'

                    check = '<div class="s-check">✓</div>' if is_owned else ""

                    # Rarity pills (USA only)
                    pills_html = ""
                    if show_rar:
                        pills = ""
                        for rk, rcfg in RARITY_CONFIG.items():
                            active_style = f"border:1.5px solid {rcfg['color']};" if rk==r else ""
                            label = rcfg["label_en"][0]  # single letter B/P/R/F
                            pills += f'<span class="r-pill {rcfg["pill"]}" style="{active_style}" title="{rcfg["label_en"]}">{label}</span>'
                        pills_html = f'<div class="rarity-row">{pills}</div>'

                    card_html = f"""
                    <div class="s-card {border_cls} {state_cls}">
                        {photo_html}
                        <div class="s-id">{sid}</div>
                        <div class="s-name">{short_nm}</div>
                        {check}
                        {pills_html}
                    </div>"""
                    st.markdown(card_html, unsafe_allow_html=True)

                    # Toggle owned button
                    btn_label = ("✓ Tengo" if is_owned else "+ Tengo") if lang=="es" else ("✓ Owned" if is_owned else "+ Own")
                    if st.button(btn_label, key=f"own_{ver}_{sid}", use_container_width=True):
                        if is_owned:
                            owned.discard(sid)
                        else:
                            owned.add(sid)
                        st.session_state.dirty = True
                        st.rerun()

                    # Rarity selector (USA only, compact)
                    if show_rar:
                        rarity_keys = list(RARITY_CONFIG.keys())
                        new_r = st.selectbox(
                            "", rarity_keys,
                            index=rarity_keys.index(r),
                            format_func=lambda x: f"{RARITY_STAR[x]} {RARITY_CONFIG[x]['label_en']}",
                            key=f"rar_{ver}_{sid}",
                            label_visibility="collapsed")
                        if new_r != r:
                            rmap[sid] = new_r
                            st.session_state.dirty = True
                            st.rerun()
