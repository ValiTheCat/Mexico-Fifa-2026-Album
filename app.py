import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import requests
from PIL import Image
from io import BytesIO

st.set_page_config(
    page_title="FIFA 2026 Sticker Tracker",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Language strings ───────────────────────────────────────────────────────────
LANG = {
    "en": {
        "title": "FIFA 2026 Sticker Tracker",
        "collection": "Collection",
        "filters": "Filters",
        "search": "Search player / team",
        "show": "Show",
        "all": "All",
        "owned_only": "Owned only",
        "missing_only": "Missing only",
        "rarity": "Rarity",
        "all_rarities": "All rarities",
        "team": "Team",
        "all_teams": "All teams",
        "legend": "Legend",
        "mark_owned": "✅ Mark as Owned",
        "mark_missing": "❌ Mark as Missing",
        "set_rarity": "Set rarity",
        "back": "← Back to collection",
        "no_photo": "No photo available",
        "loading": "Loading photo...",
        "owned_label": "✓ owned",
        "open": "Open",
        "page_title": "📋 FIFA World Cup 2026 — Sticker Collection",
        "foil": "Foil", "blue": "Blue", "purple": "Purple",
        "red": "Red", "base": "Base",
        "team_badge": "Team Badge",
        "team_photo": "Team Photo",
        "special": "FIFA Special",
        "version_label": "🇺🇸 USA Version",
    },
    "es": {
        "title": "Álbum FIFA 2026 — Rastreador",
        "collection": "Colección",
        "filters": "Filtros",
        "search": "Buscar jugador / equipo",
        "show": "Mostrar",
        "all": "Todos",
        "owned_only": "Solo tengo",
        "missing_only": "Me faltan",
        "rarity": "Rareza",
        "all_rarities": "Todas",
        "team": "Equipo",
        "all_teams": "Todos los equipos",
        "legend": "Leyenda",
        "mark_owned": "✅ Tengo este",
        "mark_missing": "❌ Me falta",
        "set_rarity": "Rareza",
        "back": "← Regresar al álbum",
        "no_photo": "Foto no disponible",
        "loading": "Cargando foto...",
        "owned_label": "✓ tengo",
        "open": "Ver",
        "page_title": "📋 Copa Mundial FIFA 2026 — Mi Álbum",
        "foil": "Foil", "blue": "Azul", "purple": "Morado",
        "red": "Rojo", "base": "Base",
        "team_badge": "Escudo del equipo",
        "team_photo": "Foto del equipo",
        "special": "FIFA Especial",
        "version_label": "🇲🇽 Versión México",
    }
}

RARITY_CONFIG = {
    "base":   {"star": "⬜", "en": "Base",   "es": "Base",    "color": "#94a3b8", "border": "#cbd5e1", "bg": "#f8fafc"},
    "blue":   {"star": "🟦", "en": "Blue",   "es": "Azul",    "color": "#3b82f6", "border": "#3b82f6", "bg": "#eff6ff"},
    "purple": {"star": "🟣", "en": "Purple", "es": "Morado",  "color": "#a855f7", "border": "#a855f7", "bg": "#faf5ff"},
    "red":    {"star": "🟥", "en": "Red",    "es": "Rojo",    "color": "#ef4444", "border": "#ef4444", "bg": "#fff1f2"},
    "foil":   {"star": "🌟", "en": "Foil",   "es": "Foil",    "color": "#f59e0b", "border": "#f59e0b", "bg": "#fffbeb"},
}

# ── Styling ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.version-toggle { display:flex; gap:0; margin-bottom:1.5rem; border-radius:10px; overflow:hidden; border:1.5px solid #e2e8f0; width:fit-content; }
.sticker-card { border-radius:10px; padding:6px; text-align:center; margin:2px; min-height:140px; display:flex; flex-direction:column; align-items:center; justify-content:space-between; }
.rarity-base   { border:2px solid #cbd5e1; background:#f8fafc; }
.rarity-blue   { border:2px solid #3b82f6; background:#eff6ff; }
.rarity-purple { border:2px solid #a855f7; background:#faf5ff; }
.rarity-red    { border:2px solid #ef4444; background:#fff1f2; }
.rarity-foil   { border:2px solid #f59e0b; background:#fffbeb; }
.rarity-none   { border:2px solid #e2e8f0; background:#fafafa; }
.owned-card  { opacity:1.0; }
.missing-card{ opacity:0.38; }
.sticker-img { border-radius:6px; width:60px; height:60px; object-fit:cover; object-position:top; }
.badge-img   { border-radius:4px; width:50px; height:50px; object-fit:contain; }
.sticker-id  { font-size:10px; font-weight:700; color:#64748b; margin-top:2px; }
.sticker-name{ font-size:9px; color:#94a3b8; margin-top:1px; line-height:1.2; }
.owned-badge { font-size:9px; color:#16a34a; font-weight:700; }
img { max-width:100%; }
</style>
""", unsafe_allow_html=True)

# ── Team data ──────────────────────────────────────────────────────────────────
TEAMS = [
    {"code":"MEX","name":"México","name_en":"Mexico","flag":"🇲🇽","wiki":"Mexico national football team","players":["Luis Malagón","Johan Vasquez","Jorge Sánchez","Cesar Montes","Jesus Gallardo","Israel Reyes","Diego Lainez","Carlos Rodriguez","Edson Alvarez","Orbelin Pineda","Marcel Ruiz","Foto del Equipo","Érick Sánchez","Hirving Lozano","Santiago Giménez","Raúl Jiménez","Alexis Vega","Roberto Alvarado","Cesar Huerta"],"players_en":["Luis Malagón","Johan Vasquez","Jorge Sánchez","Cesar Montes","Jesus Gallardo","Israel Reyes","Diego Lainez","Carlos Rodriguez","Edson Alvarez","Orbelin Pineda","Marcel Ruiz","Team Photo","Érick Sánchez","Hirving Lozano","Santiago Giménez","Raúl Jiménez","Alexis Vega","Roberto Alvarado","Cesar Huerta"]},
    {"code":"USA","name":"Estados Unidos","name_en":"USA","flag":"🇺🇸","wiki":"United States men's national soccer team","players":["Matt Freese","Chris Richards","Tim Ream","Mark McKenzie","Alex Freeman","Antonee Robinson","Tyler Adams","Tanner Tessmann","Weston McKennie","Christian Roldan","Timothy Weah","Foto del Equipo","Diego Luna","Malik Tillman","Christian Pulisic","Brenden Aaronson","Ricardo Pepi","Haji Wright","Folarin Balogun"],"players_en":["Matt Freese","Chris Richards","Tim Ream","Mark McKenzie","Alex Freeman","Antonee Robinson","Tyler Adams","Tanner Tessmann","Weston McKennie","Christian Roldan","Timothy Weah","Team Photo","Diego Luna","Malik Tillman","Christian Pulisic","Brenden Aaronson","Ricardo Pepi","Haji Wright","Folarin Balogun"]},
    {"code":"CAN","name":"Canadá","name_en":"Canada","flag":"🇨🇦","wiki":"Canada men's national soccer team","players":["Dayne St.Clair","Alphonso Davies","Alistair Johnston","Samuel Adekugbe","Riche Larvea","Derek Cornelius","Moïse Bombito","Kamal Miller","Stephen Eustáquio","Ismaël Koné","Jonathan Osorio","Foto del Equipo","Jacob Shaffelburg","Mathieu Choinière","Niko Sigur","Tajon Buchanan","Liam Millar","Cyle Larin","Jonathan David"],"players_en":["Dayne St.Clair","Alphonso Davies","Alistair Johnston","Samuel Adekugbe","Riche Larvea","Derek Cornelius","Moïse Bombito","Kamal Miller","Stephen Eustáquio","Ismaël Koné","Jonathan Osorio","Team Photo","Jacob Shaffelburg","Mathieu Choinière","Niko Sigur","Tajon Buchanan","Liam Millar","Cyle Larin","Jonathan David"]},
    {"code":"BRA","name":"Brasil","name_en":"Brazil","flag":"🇧🇷","wiki":"Brazil national football team","players":["Alisson","Bento","Marquinhos","Éder Militão","Gabriel Magalhães","Danilo","Wesley","Lucas Paquetá","Casemiro","Bruno Guimarães","Luiz Henrique","Foto del Equipo","Vinicius Júnior","Rodrygo","João Pedro","Matheus Cunha","Gabriel Martinelli","Raphinha","Estévão"],"players_en":["Alisson","Bento","Marquinhos","Éder Militão","Gabriel Magalhães","Danilo","Wesley","Lucas Paquetá","Casemiro","Bruno Guimarães","Luiz Henrique","Team Photo","Vinicius Júnior","Rodrygo","João Pedro","Matheus Cunha","Gabriel Martinelli","Raphinha","Estévão"]},
    {"code":"ARG","name":"Argentina","name_en":"Argentina","flag":"🇦🇷","wiki":"Argentina national football team","players":["Franco Armani","Emiliano Martínez","Nahuel Molina","Cristian Romero","Lisandro Martínez","Nicolás Otamendi","Marcos Acuña","Rodrigo De Paul","Leandro Paredes","Giovani Lo Celso","Ángel Di María","Foto del Equipo","Alexis Mac Allister","Nicolás González","Lautaro Martínez","Julián Álvarez","Paulo Dybala","Thiago Almada","Valentin Carboni"],"players_en":["Franco Armani","Emiliano Martínez","Nahuel Molina","Cristian Romero","Lisandro Martínez","Nicolás Otamendi","Marcos Acuña","Rodrigo De Paul","Leandro Paredes","Giovani Lo Celso","Ángel Di María","Team Photo","Alexis Mac Allister","Nicolás González","Lautaro Martínez","Julián Álvarez","Paulo Dybala","Thiago Almada","Valentin Carboni"]},
    {"code":"ENG","name":"Inglaterra","name_en":"England","flag":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","wiki":"England national football team","players":["Jordan Pickford","Dean Henderson","Reece James","John Stones","Harry Maguire","Luke Shaw","Kieran Trippier","Declan Rice","Jude Bellingham","Phil Foden","Bukayo Saka","Foto del Equipo","Morgan Rogers","Marcus Rashford","Harry Kane","Ollie Watkins","Cole Palmer","Anthony Gordon","Jarrod Bowen"],"players_en":["Jordan Pickford","Dean Henderson","Reece James","John Stones","Harry Maguire","Luke Shaw","Kieran Trippier","Declan Rice","Jude Bellingham","Phil Foden","Bukayo Saka","Team Photo","Morgan Rogers","Marcus Rashford","Harry Kane","Ollie Watkins","Cole Palmer","Anthony Gordon","Jarrod Bowen"]},
    {"code":"GER","name":"Alemania","name_en":"Germany","flag":"🇩🇪","wiki":"Germany national football team","players":["Manuel Neuer","Marc ter Stegen","Jonathan Tah","Nico Schlotterbeck","David Raum","Max Mittelstädt","Robert Andrich","Joshua Kimmich","Florian Wirtz","Ilkay Gündogan","Leon Goretzka","Foto del Equipo","Leroy Sané","Jamal Musiala","Thomas Müller","Serge Gnabry","Kai Havertz","Niclas Füllkrug","Deniz Undav"],"players_en":["Manuel Neuer","Marc ter Stegen","Jonathan Tah","Nico Schlotterbeck","David Raum","Max Mittelstädt","Robert Andrich","Joshua Kimmich","Florian Wirtz","Ilkay Gündogan","Leon Goretzka","Team Photo","Leroy Sané","Jamal Musiala","Thomas Müller","Serge Gnabry","Kai Havertz","Niclas Füllkrug","Deniz Undav"]},
    {"code":"FRA","name":"Francia","name_en":"France","flag":"🇫🇷","wiki":"France national football team","players":["Mike Maignan","Alphonse Areola","Jules Koundé","Dayot Upamecano","William Saliba","Theo Hernandez","Lucas Hernandez","Aurélien Tchouaméni","Eduardo Camavinga","Mattéo Guendouzi","Adrien Rabiot","Foto del Equipo","Antoine Griezmann","Ousmane Dembélé","Kylian Mbappé","Marcus Thuram","Randal Kolo Muani","Jonathan Clauss","Bradley Barcola"],"players_en":["Mike Maignan","Alphonse Areola","Jules Koundé","Dayot Upamecano","William Saliba","Theo Hernandez","Lucas Hernandez","Aurélien Tchouaméni","Eduardo Camavinga","Mattéo Guendouzi","Adrien Rabiot","Team Photo","Antoine Griezmann","Ousmane Dembélé","Kylian Mbappé","Marcus Thuram","Randal Kolo Muani","Jonathan Clauss","Bradley Barcola"]},
    {"code":"ESP","name":"España","name_en":"Spain","flag":"🇪🇸","wiki":"Spain national football team","players":["Unai Simón","David Raya","Dani Carvajal","Aymeric Laporte","Robin Le Normand","Alejandro Grimaldo","Jesús Navas","Rodri","Pedri","Fabián Ruiz","Dani Olmo","Foto del Equipo","Ferrán Torres","Nico Williams","Álvaro Morata","Joselu","Mikel Oyarzabal","Lamine Yamal","Yeremy Pino"],"players_en":["Unai Simón","David Raya","Dani Carvajal","Aymeric Laporte","Robin Le Normand","Alejandro Grimaldo","Jesús Navas","Rodri","Pedri","Fabián Ruiz","Dani Olmo","Team Photo","Ferrán Torres","Nico Williams","Álvaro Morata","Joselu","Mikel Oyarzabal","Lamine Yamal","Yeremy Pino"]},
    {"code":"POR","name":"Portugal","name_en":"Portugal","flag":"🇵🇹","wiki":"Portugal national football team","players":["Rui Patrício","Diogo Costa","João Cancelo","Rúben Dias","Pepe","Nuno Mendes","Danilo Pereira","Bruno Fernandes","Bernardo Silva","João Palhinha","Vitinha","Foto del Equipo","Rafael Leão","Diogo Jota","Cristiano Ronaldo","Gonçalo Ramos","Pedro Neto","João Félix","Francisco Conceição"],"players_en":["Rui Patrício","Diogo Costa","João Cancelo","Rúben Dias","Pepe","Nuno Mendes","Danilo Pereira","Bruno Fernandes","Bernardo Silva","João Palhinha","Vitinha","Team Photo","Rafael Leão","Diogo Jota","Cristiano Ronaldo","Gonçalo Ramos","Pedro Neto","João Félix","Francisco Conceição"]},
    {"code":"NED","name":"Países Bajos","name_en":"Netherlands","flag":"🇳🇱","wiki":"Netherlands national football team","players":["Bart Verbruggen","Mark Flekken","Denzel Dumfries","Virgil van Dijk","Stefan de Vrij","Nathan Aké","Tyrell Malacia","Ryan Gravenberch","Tijjani Reijnders","Teun Koopmeiners","Davy Klaassen","Foto del Equipo","Steven Bergwijn","Cody Gakpo","Memphis Depay","Wout Weghorst","Donyell Malen","Xavi Simons","Brian Brobbey"],"players_en":["Bart Verbruggen","Mark Flekken","Denzel Dumfries","Virgil van Dijk","Stefan de Vrij","Nathan Aké","Tyrell Malacia","Ryan Gravenberch","Tijjani Reijnders","Teun Koopmeiners","Davy Klaassen","Team Photo","Steven Bergwijn","Cody Gakpo","Memphis Depay","Wout Weghorst","Donyell Malen","Xavi Simons","Brian Brobbey"]},
    {"code":"ITA","name":"Italia","name_en":"Italy","flag":"🇮🇹","wiki":"Italy national football team","players":["Gianluigi Donnarumma","Alex Meret","Giovanni Di Lorenzo","Alessandro Bastoni","Federico Gatti","Federico Dimarco","Davide Frattesi","Sandro Tonali","Nicolò Barella","Lorenzo Pellegrini","Nicolò Fagioli","Foto del Equipo","Federico Chiesa","Matteo Politano","Gianluca Scamacca","Lorenzo Lucca","Giacomo Raspadori","Mateo Retegui","Wilfried Gnonto"],"players_en":["Gianluigi Donnarumma","Alex Meret","Giovanni Di Lorenzo","Alessandro Bastoni","Federico Gatti","Federico Dimarco","Davide Frattesi","Sandro Tonali","Nicolò Barella","Lorenzo Pellegrini","Nicolò Fagioli","Team Photo","Federico Chiesa","Matteo Politano","Gianluca Scamacca","Lorenzo Lucca","Giacomo Raspadori","Mateo Retegui","Wilfried Gnonto"]},
    {"code":"SCO","name":"Escocia","name_en":"Scotland","flag":"🏴󠁧󠁢󠁳󠁣󠁴󠁿","wiki":"Scotland national football team","players":["Angus Gunn","Jack Hendry","Kieran Tierney","Aaron Hickey","Andrew Robertson","Scott McKenna","John Souttar","Anthony Ralston","Grant Hanley","Scott McTominay","Billy Gilmour","Foto del Equipo","Lewis Ferguson","Ryan Christie","Kenny McLean","John McGinn","Lyndon Dykes","Che Adams","Ben Doak"],"players_en":["Angus Gunn","Jack Hendry","Kieran Tierney","Aaron Hickey","Andrew Robertson","Scott McKenna","John Souttar","Anthony Ralston","Grant Hanley","Scott McTominay","Billy Gilmour","Team Photo","Lewis Ferguson","Ryan Christie","Kenny McLean","John McGinn","Lyndon Dykes","Che Adams","Ben Doak"]},
    {"code":"CZE","name":"Chequia","name_en":"Czechia","flag":"🇨🇿","wiki":"Czech Republic national football team","players":["Matej Kovar","Jindrich Stanek","Ladislav Krejci","Vladimir Coufal","Jaroslav Zeleny","Tomas Holes","David Zima","Michal Sadilek","Lukas Provod","Lukas Cerv","Tomas Soucek","Foto del Equipo","Pavel Sulc","Matej Vydra","Vasil Kusej","Tomas Chory","Vaclav Cerny","Adam Hlozek","Patrik Schick"],"players_en":["Matej Kovar","Jindrich Stanek","Ladislav Krejci","Vladimir Coufal","Jaroslav Zeleny","Tomas Holes","David Zima","Michal Sadilek","Lukas Provod","Lukas Cerv","Tomas Soucek","Team Photo","Pavel Sulc","Matej Vydra","Vasil Kusej","Tomas Chory","Vaclav Cerny","Adam Hlozek","Patrik Schick"]},
    {"code":"NOR","name":"Noruega","name_en":"Norway","flag":"🇳🇴","wiki":"Norway national football team","players":["Orjan Nyland","Mats Selnaes","Kristoffer Ajer","Leo Ostigard","Andreas Hanche-Olsen","Birger Meling","Vegar Hedenstad","Mathias Normann","Patrick Berg","Fredrik Aursnes","Sander Berge","Foto del Equipo","Martin Odegaard","Antonio Nusa","Mohamed Elyounoussi","Erling Haaland","Alexander Sorloth","Ola Solbakken","Jens Petter Hauge"],"players_en":["Orjan Nyland","Mats Selnaes","Kristoffer Ajer","Leo Ostigard","Andreas Hanche-Olsen","Birger Meling","Vegar Hedenstad","Mathias Normann","Patrick Berg","Fredrik Aursnes","Sander Berge","Team Photo","Martin Odegaard","Antonio Nusa","Mohamed Elyounoussi","Erling Haaland","Alexander Sorloth","Ola Solbakken","Jens Petter Hauge"]},
    {"code":"SWE","name":"Suecia","name_en":"Sweden","flag":"🇸🇪","wiki":"Sweden national football team","players":["Robin Olsen","Isak Pettersson","Carl Starfelt","Victor Lindelöf","Isak Hien","Marcus Danielson","Emil Krafth","Jens Cajuste","Viktor Claesson","Hugo Larsson","Viktor Johansson","Foto del Equipo","Dejan Kulusevski","Alexander Isak","Robin Quaison","Jordan Larsson","Kristoffer Zachrisson","Emil Forsberg","Pontus Almqvist"],"players_en":["Robin Olsen","Isak Pettersson","Carl Starfelt","Victor Lindelöf","Isak Hien","Marcus Danielson","Emil Krafth","Jens Cajuste","Viktor Claesson","Hugo Larsson","Viktor Johansson","Team Photo","Dejan Kulusevski","Alexander Isak","Robin Quaison","Jordan Larsson","Kristoffer Zachrisson","Emil Forsberg","Pontus Almqvist"]},
    {"code":"AUS","name":"Australia","name_en":"Australia","flag":"🇦🇺","wiki":"Australia national soccer team","players":["Mathew Ryan","Joe Gauci","Harry Souttar","Alessandro Circati","Jordan Bos","Aziz Behich","Cameron Burgess","Lewis Miller","Milos Degenek","Jackson Irvine","Riley McGree","Foto del Equipo","Aiden O'Neill","Connor Metcalfe","Patrick Yazbek","Craig Goodwin","Kusini Yengi","Nestory Irankunda","Mohamed Touré"],"players_en":["Mathew Ryan","Joe Gauci","Harry Souttar","Alessandro Circati","Jordan Bos","Aziz Behich","Cameron Burgess","Lewis Miller","Milos Degenek","Jackson Irvine","Riley McGree","Team Photo","Aiden O'Neill","Connor Metcalfe","Patrick Yazbek","Craig Goodwin","Kusini Yengi","Nestory Irankunda","Mohamed Touré"]},
    {"code":"RSA","name":"Sudáfrica","name_en":"South Africa","flag":"🇿🇦","wiki":"South Africa national football team","players":["Ronwen Williams","Sipho Chaine","Aubrey Modiba","Samukele Kabini","Mbekezeli Mbokazi","Khulumani Ndamane","Siyabonga Ngezana","Khuliso Mudau","Nkosinathi Sibisi","Teboho Mokoena","Thalente Mbatha","Foto del Equipo","Bathasi Aubaas","Yaya Sithole","Sipho Mbule","Lyle Foster","Iqraam Rayners","Mohau Nkota","Oswin Appollis"],"players_en":["Ronwen Williams","Sipho Chaine","Aubrey Modiba","Samukele Kabini","Mbekezeli Mbokazi","Khulumani Ndamane","Siyabonga Ngezana","Khuliso Mudau","Nkosinathi Sibisi","Teboho Mokoena","Thalente Mbatha","Team Photo","Bathasi Aubaas","Yaya Sithole","Sipho Mbule","Lyle Foster","Iqraam Rayners","Mohau Nkota","Oswin Appollis"]},
    {"code":"KOR","name":"Corea del Sur","name_en":"South Korea","flag":"🇰🇷","wiki":"South Korea national football team","players":["Hyeon-woo Jo","Seung-Gyu Kim","Min-jae Kim","Yu-min Cho","Young-woo Seol","Han-beom Lee","Tae-seok Lee","Myung-jae Lee","Jae-sung Lee","In-beom Hwang","Kang-in Lee","Foto del Equipo","Seung-ho Paik","Jens Castrop","Dong-yeong Lee","Gue-sung Cho","Heung-min Son","Hee-chan Hwang","Hyeon-Gyu Oh"],"players_en":["Hyeon-woo Jo","Seung-Gyu Kim","Min-jae Kim","Yu-min Cho","Young-woo Seol","Han-beom Lee","Tae-seok Lee","Myung-jae Lee","Jae-sung Lee","In-beom Hwang","Kang-in Lee","Team Photo","Seung-ho Paik","Jens Castrop","Dong-yeong Lee","Gue-sung Cho","Heung-min Son","Hee-chan Hwang","Hyeon-Gyu Oh"]},
    {"code":"JPN","name":"Japón","name_en":"Japan","flag":"🇯🇵","wiki":"Japan national football team","players":["Shuichi Gonda","Daniel Schmidt","Takehiro Tomiyasu","Ko Itakura","Shogo Taniguchi","Yuto Nagatomo","Hiroki Ito","Wataru Endo","Ao Tanaka","Hidemasa Morita","Junya Ito","Foto del Equipo","Takumi Minamino","Kaoru Mitoma","Ritsu Doan","Ayase Ueda","Yukinari Sugawara","Daichi Kamada","Keito Nakamura"],"players_en":["Shuichi Gonda","Daniel Schmidt","Takehiro Tomiyasu","Ko Itakura","Shogo Taniguchi","Yuto Nagatomo","Hiroki Ito","Wataru Endo","Ao Tanaka","Hidemasa Morita","Junya Ito","Team Photo","Takumi Minamino","Kaoru Mitoma","Ritsu Doan","Ayase Ueda","Yukinari Sugawara","Daichi Kamada","Keito Nakamura"]},
    {"code":"EGY","name":"Egipto","name_en":"Egypt","flag":"🇪🇬","wiki":"Egypt national football team","players":["Mohamed Abou Gabal","Mohamed El-Shenawy","Ahmed Hegazy","Omar Kamal","Mohamed Abdelmonem","Akram Tawfik","Mahmoud El Wensh","Amr El Sulaya","Mohamed Elneny","Taher Mohamed Taher","Mohamed Hamdy","Foto del Equipo","Emam Ashour","Zizo","Omar Marmoush","Mostafa Mohamed","Hussein El Shahat","Marwan Attia","Trezeguet"],"players_en":["Mohamed Abou Gabal","Mohamed El-Shenawy","Ahmed Hegazy","Omar Kamal","Mohamed Abdelmonem","Akram Tawfik","Mahmoud El Wensh","Amr El Sulaya","Mohamed Elneny","Taher Mohamed Taher","Mohamed Hamdy","Team Photo","Emam Ashour","Zizo","Omar Marmoush","Mostafa Mohamed","Hussein El Shahat","Marwan Attia","Trezeguet"]},
    {"code":"IRN","name":"Irán","name_en":"Iran","flag":"🇮🇷","wiki":"Iran national football team","players":["Alireza Beiranvand","Amir Abedzadeh","Shoja Khalilzadeh","Majid Hosseini","Hossein Kanaanizadegan","Milad Mohammadi","Roozbeh Cheshmi","Saeid Ezatolahi","Ali Karimi","Mehdi Torabi","Ahmad Noorollahi","Foto del Equipo","Sardar Azmoun","Saman Ghoddos","Karim Ansarifard","Mehdi Taremi","Ali Gholizadeh","Allahyar Sayyadmanesh","Omid Noorafkan"],"players_en":["Alireza Beiranvand","Amir Abedzadeh","Shoja Khalilzadeh","Majid Hosseini","Hossein Kanaanizadegan","Milad Mohammadi","Roozbeh Cheshmi","Saeid Ezatolahi","Ali Karimi","Mehdi Torabi","Ahmad Noorollahi","Team Photo","Sardar Azmoun","Saman Ghoddos","Karim Ansarifard","Mehdi Taremi","Ali Gholizadeh","Allahyar Sayyadmanesh","Omid Noorafkan"]},
    {"code":"QAT","name":"Catar","name_en":"Qatar","flag":"🇶🇦","wiki":"Qatar national football team","players":["Meshaal Barsham","Sultan Albrake","Lucas Mendes","Homam Ahmed","Boualem Khoukhi","Pedro Miguel","Tarek Salman","Mohamed Al-Mannai","Karim Boudiaf","Assim Madibo","Ahmed Fatehi","Foto del Equipo","Mohammed Waad","Abdulaziz Hatem","Hassan Al-Haydos","Edmilson Junior","Akram Afif","Ahmed Al Ganehi","Almoez Ali"],"players_en":["Meshaal Barsham","Sultan Albrake","Lucas Mendes","Homam Ahmed","Boualem Khoukhi","Pedro Miguel","Tarek Salman","Mohamed Al-Mannai","Karim Boudiaf","Assim Madibo","Ahmed Fatehi","Team Photo","Mohammed Waad","Abdulaziz Hatem","Hassan Al-Haydos","Edmilson Junior","Akram Afif","Ahmed Al Ganehi","Almoez Ali"]},
    {"code":"SUI","name":"Suiza","name_en":"Switzerland","flag":"🇨🇭","wiki":"Switzerland national football team","players":["Gregor Kobel","Yvon Mvogo","Manuel Akanji","Ricardo Rodriguez","Nico Elvedi","Aurèle Amenda","Silvan Widmer","Granit Xhaka","Denis Zakaria","Remo Freuler","Fabian Rieder","Foto del Equipo","Ardon Jashari","Johan Manzambi","Michel Aebischer","Breel Embolo","Ruben Vargas","Dan Ndoye","Zeki Amdouni"],"players_en":["Gregor Kobel","Yvon Mvogo","Manuel Akanji","Ricardo Rodriguez","Nico Elvedi","Aurèle Amenda","Silvan Widmer","Granit Xhaka","Denis Zakaria","Remo Freuler","Fabian Rieder","Team Photo","Ardon Jashari","Johan Manzambi","Michel Aebischer","Breel Embolo","Ruben Vargas","Dan Ndoye","Zeki Amdouni"]},
    {"code":"MAR","name":"Marruecos","name_en":"Morocco","flag":"🇲🇦","wiki":"Morocco national football team","players":["Yassine Bounou","Munir El Kajoui","Achraf Hakimi","Noussair Mazraoui","Nayef Aguerd","Roman Saiss","Jawad El Yamiq","Adam Masina","Sofyan Amrabat","Azzedine Ounahi","Eliesse Ben Seghir","Foto del Equipo","Bilal El Khannouss","Ismael Saibari","Youssef En-Nesyri","Abde Ezzalzouli","Soufiane Rahimi","Brahim Diaz","Ayoub El Kaabi"],"players_en":["Yassine Bounou","Munir El Kajoui","Achraf Hakimi","Noussair Mazraoui","Nayef Aguerd","Roman Saiss","Jawad El Yamiq","Adam Masina","Sofyan Amrabat","Azzedine Ounahi","Eliesse Ben Seghir","Team Photo","Bilal El Khannouss","Ismael Saibari","Youssef En-Nesyri","Abde Ezzalzouli","Soufiane Rahimi","Brahim Diaz","Ayoub El Kaabi"]},
    {"code":"COL","name":"Colombia","name_en":"Colombia","flag":"🇨🇴","wiki":"Colombia national football team","players":["David Ospina","Camilo Vargas","Davinson Sánchez","Yerry Mina","Daniel Muñoz","Johan Mojica","Lerma","Wilmar Barrios","Mateus Uribe","Luis Díaz","James Rodríguez","Foto del Equipo","Rafael Santos Borré","Cucho Hernández","Falcao","Jhon Córdoba","Miguel Borja","Jhon Durán","Jhon Arias"],"players_en":["David Ospina","Camilo Vargas","Davinson Sánchez","Yerry Mina","Daniel Muñoz","Johan Mojica","Lerma","Wilmar Barrios","Mateus Uribe","Luis Díaz","James Rodríguez","Team Photo","Rafael Santos Borré","Cucho Hernández","Falcao","Jhon Córdoba","Miguel Borja","Jhon Durán","Jhon Arias"]},
    {"code":"URU","name":"Uruguay","name_en":"Uruguay","flag":"🇺🇾","wiki":"Uruguay national football team","players":["Fernando Muslera","Sergio Rochet","Ronald Araújo","José María Giménez","Mathías Olivera","Nahitan Nández","Lucas Torreira","Federico Valverde","Rodrigo Bentancur","Giorgian De Arrascaeta","Facundo Pellistri","Foto del Equipo","Darwin Núñez","Luis Suárez","Edinson Cavani","Maxi Gómez","Brian Rodríguez","Agustín Canobbio","Ignacio De La Cruz"],"players_en":["Fernando Muslera","Sergio Rochet","Ronald Araújo","José María Giménez","Mathías Olivera","Nahitan Nández","Lucas Torreira","Federico Valverde","Rodrigo Bentancur","Giorgian De Arrascaeta","Facundo Pellistri","Team Photo","Darwin Núñez","Luis Suárez","Edinson Cavani","Maxi Gómez","Brian Rodríguez","Agustín Canobbio","Ignacio De La Cruz"]},
    {"code":"TUR","name":"Turquía","name_en":"Türkiye","flag":"🇹🇷","wiki":"Turkey national football team","players":["Ugurcan Cakir","Mert Gunok","Çaglar Söyüncü","Merih Demiral","Samet Akaydin","Ferdi Kadioglu","Zeki Celik","Hakan Calhanoglu","Kaan Ayhan","Orkun Kökcü","Kenan Yildiz","Foto del Equipo","Arda Güler","Yunus Akgun","Baris Alper Yilmaz","Efecan Karaca","Cenk Tosun","Umut Bozok","Serdar Dursun"],"players_en":["Ugurcan Cakir","Mert Gunok","Çaglar Söyüncü","Merih Demiral","Samet Akaydin","Ferdi Kadioglu","Zeki Celik","Hakan Calhanoglu","Kaan Ayhan","Orkun Kökcü","Kenan Yildiz","Team Photo","Arda Güler","Yunus Akgun","Baris Alper Yilmaz","Efecan Karaca","Cenk Tosun","Umut Bozok","Serdar Dursun"]},
    {"code":"NGA","name":"Nigeria","name_en":"Nigeria","flag":"🇳🇬","wiki":"Nigeria national football team","players":["Francis Uzoho","Stanley Nwabali","Semi Ajayi","William Troost-Ekong","Zaidu Sanusi","Bright Osayi-Samuel","Ola Aina","Frank Onyeka","Alex Iwobi","Wilfred Ndidi","Kelechi Iheanacho","Foto del Equipo","Samuel Chukwueze","Ademola Lookman","Moses Simon","Victor Osimhen","Terem Moffi","Taiwo Awoniyi","Cyriel Dessers"],"players_en":["Francis Uzoho","Stanley Nwabali","Semi Ajayi","William Troost-Ekong","Zaidu Sanusi","Bright Osayi-Samuel","Ola Aina","Frank Onyeka","Alex Iwobi","Wilfred Ndidi","Kelechi Iheanacho","Team Photo","Samuel Chukwueze","Ademola Lookman","Moses Simon","Victor Osimhen","Terem Moffi","Taiwo Awoniyi","Cyriel Dessers"]},
    {"code":"SEN","name":"Senegal","name_en":"Senegal","flag":"🇸🇳","wiki":"Senegal national football team","players":["Edouard Mendy","Seny Dieng","Kalidou Koulibaly","Abdou Diallo","Ismail Jakobs","Formose Mendy","Pape Abou Cissé","Lamine Camara","Idrissa Gana Gueye","Nampalys Mendy","Krepin Diatta","Foto del Equipo","Iliman Ndiaye","Boulaye Dia","Sadio Mané","Nicolas Jackson","Ismaila Sarr","Habib Diallo","Yehvann Diouf"],"players_en":["Edouard Mendy","Seny Dieng","Kalidou Koulibaly","Abdou Diallo","Ismail Jakobs","Formose Mendy","Pape Abou Cissé","Lamine Camara","Idrissa Gana Gueye","Nampalys Mendy","Krepin Diatta","Team Photo","Iliman Ndiaye","Boulaye Dia","Sadio Mané","Nicolas Jackson","Ismaila Sarr","Habib Diallo","Yehvann Diouf"]},
    {"code":"GHA","name":"Ghana","name_en":"Ghana","flag":"🇬🇭","wiki":"Ghana national football team","players":["Lawrence Ati-Zigi","Jojo Wollacott","Andy Yiadom","Alexander Djiku","Daniel Amartey","Alidu Seidu","Baba Rahman","Thomas Partey","Salis Abdul Samed","Mohammed Kudus","Emmanuel Gyasi","Foto del Equipo","Antoine Semenyo","Jordan Ayew","Andre Ayew","Felix Afena-Gyan","Gideon Mensah","Kamaldeen Sulemana","Inaki Williams"],"players_en":["Lawrence Ati-Zigi","Jojo Wollacott","Andy Yiadom","Alexander Djiku","Daniel Amartey","Alidu Seidu","Baba Rahman","Thomas Partey","Salis Abdul Samed","Mohammed Kudus","Emmanuel Gyasi","Team Photo","Antoine Semenyo","Jordan Ayew","Andre Ayew","Felix Afena-Gyan","Gideon Mensah","Kamaldeen Sulemana","Inaki Williams"]},
    {"code":"AUT","name":"Austria","name_en":"Austria","flag":"🇦🇹","wiki":"Austria national football team","players":["Patrick Pentz","Heinz Lindner","Stefan Posch","David Alaba","Gernot Trauner","Philipp Mwene","Maximilian Wöber","Nicolas Seiwald","Konrad Laimer","Marcel Sabitzer","Xaver Schlager","Foto del Equipo","Florian Kainz","Patrick Wimmer","Marko Arnautovic","Michael Gregoritsch","Christoph Baumgartner","Louis Schaub","Romano Schmid"],"players_en":["Patrick Pentz","Heinz Lindner","Stefan Posch","David Alaba","Gernot Trauner","Philipp Mwene","Maximilian Wöber","Nicolas Seiwald","Konrad Laimer","Marcel Sabitzer","Xaver Schlager","Team Photo","Florian Kainz","Patrick Wimmer","Marko Arnautovic","Michael Gregoritsch","Christoph Baumgartner","Louis Schaub","Romano Schmid"]},
    {"code":"BIH","name":"Bosnia y Herz.","name_en":"Bosnia & Herz.","flag":"🇧🇦","wiki":"Bosnia and Herzegovina national football team","players":["Nikola Vasilj","Amer Dedic","Sead Kolasinac","Tarik Muharemovic","Nihad Mujakic","Nikola Katic","Amir Hadziahmetovic","Benjamin Tahirovic","Armin Gigovic","Ivan Sunjic","Ivan Basic","Foto del Equipo","Dzenis Burnic","Esmir Bajraktarevic","Amar Memic","Ermedin Demirovic","Edin Dzeko","Samed Bazdar","Haris Tabakovic"],"players_en":["Nikola Vasilj","Amer Dedic","Sead Kolasinac","Tarik Muharemovic","Nihad Mujakic","Nikola Katic","Amir Hadziahmetovic","Benjamin Tahirovic","Armin Gigovic","Ivan Sunjic","Ivan Basic","Team Photo","Dzenis Burnic","Esmir Bajraktarevic","Amar Memic","Ermedin Demirovic","Edin Dzeko","Samed Bazdar","Haris Tabakovic"]},
    {"code":"UZB","name":"Uzbekistán","name_en":"Uzbekistan","flag":"🇺🇿","wiki":"Uzbekistan national football team","players":["Utkir Yusupov","Sherzod Nishonov","Sherzod Qoraboyev","Khurshid Tursunov","Akbar Bobojonov","Timur Jorayev","Oston Urunov","Jaloliddin Masharipov","Odil Akhmedov","Farrukh Tashkentov","Jamshid Iskanderov","Foto del Equipo","Eldor Shomurodov","Abbosbek Fayzullaev","Sherzod Nasrullaev","Bobur Abdixoliqov","Otabek Shukurov","Dostonbek Xolmatov","Khojiakbar Alijonov"],"players_en":["Utkir Yusupov","Sherzod Nishonov","Sherzod Qoraboyev","Khurshid Tursunov","Akbar Bobojonov","Timur Jorayev","Oston Urunov","Jaloliddin Masharipov","Odil Akhmedov","Farrukh Tashkentov","Jamshid Iskanderov","Team Photo","Eldor Shomurodov","Abbosbek Fayzullaev","Sherzod Nasrullaev","Bobur Abdixoliqov","Otabek Shukurov","Dostonbek Xolmatov","Khojiakbar Alijonov"]},
    {"code":"HAI","name":"Haití","name_en":"Haiti","flag":"🇭🇹","wiki":"Haiti national football team","players":["Johny Placide","Carlens Arcus","Martin Expérience","Jean-Kevin Duverne","Ricardo Adé","Duke Lacroix","Garven Metusala","Hannes Delcroix","Leverton Pierre","Danley Jean Jacques","Jean-Ricner Bellegarde","Foto del Equipo","Christopher Attys","Derrick Etienne Jr","Josue Casimir","Ruben Providence","Duckens Nazon","Louicius Deedson","Frantzdy Pierrot"],"players_en":["Johny Placide","Carlens Arcus","Martin Expérience","Jean-Kevin Duverne","Ricardo Adé","Duke Lacroix","Garven Metusala","Hannes Delcroix","Leverton Pierre","Danley Jean Jacques","Jean-Ricner Bellegarde","Team Photo","Christopher Attys","Derrick Etienne Jr","Josue Casimir","Ruben Providence","Duckens Nazon","Louicius Deedson","Frantzdy Pierrot"]},
    {"code":"PAR","name":"Paraguay","name_en":"Paraguay","flag":"🇵🇾","wiki":"Paraguay national football team","players":["Roberto Fernandez","Orlando Gill","Gustavo Gomez","Fabián Balbuena","Juan José Cáceres","Omar Alderete","Junior Alonso","Mathías Villasanti","Diego Gomez","Damián Bobadilla","Andres Cubas","Foto del Equipo","Matias Galarza","Julio Enciso","Alejandro Romero","Miguel Almirón","Ramon Sosa","Angel Romero","Antonio Sanabria"],"players_en":["Roberto Fernandez","Orlando Gill","Gustavo Gomez","Fabián Balbuena","Juan José Cáceres","Omar Alderete","Junior Alonso","Mathías Villasanti","Diego Gomez","Damián Bobadilla","Andres Cubas","Team Photo","Matias Galarza","Julio Enciso","Alejandro Romero","Miguel Almirón","Ramon Sosa","Angel Romero","Antonio Sanabria"]},
    {"code":"ECU","name":"Ecuador","name_en":"Ecuador","flag":"🇪🇨","wiki":"Ecuador national football team","players":["Hernán Galíndez","Alexander Domínguez","Ángelo Preciado","Piero Hincapié","Jackson Porozo","Pervis Estupiñán","Diego Palacios","Carlos Gruezo","Jhegson Méndez","Moisés Caicedo","Jeremy Sarmiento","Foto del Equipo","Gonzalo Plata","Michael Estrada","Romario Ibarra","Enner Valencia","Ángel Mena","Jordy Caicedo","Leonardo Campana"],"players_en":["Hernán Galíndez","Alexander Domínguez","Ángelo Preciado","Piero Hincapié","Jackson Porozo","Pervis Estupiñán","Diego Palacios","Carlos Gruezo","Jhegson Méndez","Moisés Caicedo","Jeremy Sarmiento","Team Photo","Gonzalo Plata","Michael Estrada","Romario Ibarra","Enner Valencia","Ángel Mena","Jordy Caicedo","Leonardo Campana"]},
    {"code":"IRQ","name":"Irak","name_en":"Iraq","flag":"🇮🇶","wiki":"Iraq national football team","players":["Jalal Hassan","Fahad Tariq","Ali Adnan","Saad Natiq","Rebin Sulaka","Ahmed Ibrahim","Mustafa Nadhim","Hussein Ali","Amjad Attwan","Osama Rashid","Bashar Resan","Foto del Equipo","Mohanad Ali","Amir Al Ammari","Aymen Hussein","Ali Jasim","Ibrahim Bayesh","Alaa Abbas","Amir Al Saddah"],"players_en":["Jalal Hassan","Fahad Tariq","Ali Adnan","Saad Natiq","Rebin Sulaka","Ahmed Ibrahim","Mustafa Nadhim","Hussein Ali","Amjad Attwan","Osama Rashid","Bashar Resan","Team Photo","Mohanad Ali","Amir Al Ammari","Aymen Hussein","Ali Jasim","Ibrahim Bayesh","Alaa Abbas","Amir Al Saddah"]},
    {"code":"CMR","name":"Camerún","name_en":"Cameroon","flag":"🇨🇲","wiki":"Cameroon national football team","players":["André Onana","Fabrice Ondoa","Harold Moukoudi","Jean-Charles Castelletto","Collins Fai","Ambroise Oyongo","Nicolas Nkoulou","Samuel Oum Gouet","Frank Zambo Anguissa","Pierre Kunde","Martin Hongla","Foto del Equipo","Bryan Mbeumo","Karl Toko Ekambi","Vincent Aboubakar","Eric Choupo-Moting","Stéphane Bahoken","Georges-Kevin N'Koudou","Ignatius Ganago"],"players_en":["André Onana","Fabrice Ondoa","Harold Moukoudi","Jean-Charles Castelletto","Collins Fai","Ambroise Oyongo","Nicolas Nkoulou","Samuel Oum Gouet","Frank Zambo Anguissa","Pierre Kunde","Martin Hongla","Team Photo","Bryan Mbeumo","Karl Toko Ekambi","Vincent Aboubakar","Eric Choupo-Moting","Stéphane Bahoken","Georges-Kevin N'Koudou","Ignatius Ganago"]},
    {"code":"CIV","name":"Costa de Marfil","name_en":"Côte d'Ivoire","flag":"🇨🇮","wiki":"Ivory Coast national football team","players":["Yahia Fofana","Badra Sangaré","Simon Deli","Willy Boly","Serge Aurier","Ghislain Konan","Wilfried Kanon","Ibrahim Sangaré","Jean-Michaël Seri","Franck Kessie","Sekou Sanogo","Foto del Equipo","Nicolas Pépé","Jonathan Bamba","Wilfried Zaha","Sébastien Haller","Simon Adingra","Oumar Diakité","Odilon Kossounou"],"players_en":["Yahia Fofana","Badra Sangaré","Simon Deli","Willy Boly","Serge Aurier","Ghislain Konan","Wilfried Kanon","Ibrahim Sangaré","Jean-Michaël Seri","Franck Kessie","Sekou Sanogo","Team Photo","Nicolas Pépé","Jonathan Bamba","Wilfried Zaha","Sébastien Haller","Simon Adingra","Oumar Diakité","Odilon Kossounou"]},
    {"code":"CHI","name":"Chile","name_en":"Chile","flag":"🇨🇱","wiki":"Chile national football team","players":["Brayan Cortés","Gabriel Arias","Paulo Díaz","Guillermo Maripán","Benjamín Kuscevic","Mauricio Isla","Gabriel Suazo","Arturo Vidal","Charles Aránguiz","Erick Pulgar","César Pinares","Foto del Equipo","Alexis Sánchez","Eduardo Vargas","Sebastián Driussi","Víctor Dávila","Marcos Bolados","Jean Meneses","Darío Osorio"],"players_en":["Brayan Cortés","Gabriel Arias","Paulo Díaz","Guillermo Maripán","Benjamín Kuscevic","Mauricio Isla","Gabriel Suazo","Arturo Vidal","Charles Aránguiz","Erick Pulgar","César Pinares","Team Photo","Alexis Sánchez","Eduardo Vargas","Sebastián Driussi","Víctor Dávila","Marcos Bolados","Jean Meneses","Darío Osorio"]},
    {"code":"PAN","name":"Panamá","name_en":"Panama","flag":"🇵🇦","wiki":"Panama national football team","players":["Luis Mejía","Orlando Mosquera","Harold Cummings","Eric Davis","Anibal Godoy","Fidel Escobar","Adalberto Carrasquilla","Roderick Miller","Édgar Bárcenas","Rolando Blackburn","Alberto Quintero","Foto del Equipo","Cecilio Waterman","Abdiel Ayarza","Ismael Díaz","Freddie Hall","José Fajardo","Blas Pérez","Giovanny Ramos"],"players_en":["Luis Mejía","Orlando Mosquera","Harold Cummings","Eric Davis","Anibal Godoy","Fidel Escobar","Adalberto Carrasquilla","Roderick Miller","Édgar Bárcenas","Rolando Blackburn","Alberto Quintero","Team Photo","Cecilio Waterman","Abdiel Ayarza","Ismael Díaz","Freddie Hall","José Fajardo","Blas Pérez","Giovanny Ramos"]},
    {"code":"CRC","name":"Costa Rica","name_en":"Costa Rica","flag":"🇨🇷","wiki":"Costa Rica national football team","players":["Keylor Navas","Esteban Alvarado","Keysher Fuller","Francisco Calvo","Juan Pablo Vargas","Bryan Oviedo","Kendall Waston","Yeltsin Tejeda","Douglas Sequeira","Celso Borges","Joel Campbell","Foto del Equipo","Brandon Aguilera","Jewison Bennette","Álvaro Zamora","Anthony Contreras","Alonso Martínez","Johan Venegas","Bryan Ruiz"],"players_en":["Keylor Navas","Esteban Alvarado","Keysher Fuller","Francisco Calvo","Juan Pablo Vargas","Bryan Oviedo","Kendall Waston","Yeltsin Tejeda","Douglas Sequeira","Celso Borges","Joel Campbell","Team Photo","Brandon Aguilera","Jewison Bennette","Álvaro Zamora","Anthony Contreras","Alonso Martínez","Johan Venegas","Bryan Ruiz"]},
    {"code":"HON","name":"Honduras","name_en":"Honduras","flag":"🇭🇳","wiki":"Honduras national football team","players":["Luis López","Edrick Menjívar","Denil Maldonado","Marcelo Pereira","Devron García","Kervin Arriaga","Maynor Figueroa","Alberth Elis","Romell Quioto","Rigoberto Rivas","Edwin Rodríguez","Foto del Equipo","Jorge Benguché","Andy Najar","Michaell Chirinos","Eddie Hernández","Alexander López","Deybi Flores","Joaquín Arias"],"players_en":["Luis López","Edrick Menjívar","Denil Maldonado","Marcelo Pereira","Devron García","Kervin Arriaga","Maynor Figueroa","Alberth Elis","Romell Quioto","Rigoberto Rivas","Edwin Rodríguez","Team Photo","Jorge Benguché","Andy Najar","Michaell Chirinos","Eddie Hernández","Alexander López","Deybi Flores","Joaquín Arias"]},
    {"code":"JAM","name":"Jamaica","name_en":"Jamaica","flag":"🇯🇲","wiki":"Jamaica national football team","players":["Andre Blake","Dillon Barnes","Damion Lowe","Adrian Mariappa","Liam Moore","Greg Leigh","Javain Brown","Rolando Aarons","Daniel Johnson","Je-Vaughn Watson","Bobby Decordova-Reid","Foto del Equipo","Michail Antonio","Leon Bailey","Shamar Nicholson","Cory Burke","Oniel Fisher","Chedwyn Evans","Demarai Gray"],"players_en":["Andre Blake","Dillon Barnes","Damion Lowe","Adrian Mariappa","Liam Moore","Greg Leigh","Javain Brown","Rolando Aarons","Daniel Johnson","Je-Vaughn Watson","Bobby Decordova-Reid","Team Photo","Michail Antonio","Leon Bailey","Shamar Nicholson","Cory Burke","Oniel Fisher","Chedwyn Evans","Demarai Gray"]},
]

SPECIAL_STICKERS = [
    {"id":"00","name":"Logo Panini","name_en":"Panini Logo","rarity":"foil"},
    {"id":"FWC1","name":"Emblema Oficial","name_en":"Official Emblem","rarity":"foil"},
    {"id":"FWC2","name":"Emblema Oficial 2","name_en":"Official Emblem 2","rarity":"foil"},
    {"id":"FWC3","name":"Mascotas","name_en":"Mascots","rarity":"foil"},
    {"id":"FWC4","name":"Slogan Oficial","name_en":"Official Slogan","rarity":"foil"},
    {"id":"FWC5","name":"Balón Oficial","name_en":"Official Ball","rarity":"foil"},
    {"id":"FWC6","name":"Ciudades Canadá","name_en":"Canada Cities","rarity":"foil"},
    {"id":"FWC7","name":"Ciudades México","name_en":"Mexico Cities","rarity":"foil"},
    {"id":"FWC8","name":"Ciudades EUA","name_en":"USA Cities","rarity":"foil"},
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
        st.error(f"Error conectando a Google Sheets: {e}")
        return None

def load_data(sheet):
    owned, rarity_map = set(), {}
    try:
        rows = sheet.get_all_records()
        for row in rows:
            sid = str(row.get("sticker_id","")).strip()
            if not sid:
                continue
            if str(row.get("owned","")).strip().upper() == "TRUE":
                owned.add(sid)
            r = str(row.get("rarity","base")).strip().lower()
            if r in RARITY_CONFIG:
                rarity_map[sid] = r
    except Exception as e:
        st.warning(f"No se pudieron cargar datos: {e}")
    return owned, rarity_map

def save_sticker(sheet, sticker_id, is_owned, rarity):
    try:
        cell = sheet.find(sticker_id, in_column=1)
        if cell:
            sheet.update(f"A{cell.row}:C{cell.row}", [[sticker_id, str(is_owned), rarity]])
        else:
            sheet.append_row([sticker_id, str(is_owned), rarity])
    except Exception as e:
        st.warning(f"Error guardando: {e}")

# ── Wikipedia photos ───────────────────────────────────────────────────────────
@st.cache_data(ttl=86400)
def get_wiki_photo(query: str):
    try:
        params = {"action":"query","format":"json","prop":"pageimages",
                  "titles":query,"pithumbsize":200,"pilimit":1}
        r = requests.get("https://en.wikipedia.org/w/api.php", params=params, timeout=5)
        pages = r.json().get("query",{}).get("pages",{})
        for page in pages.values():
            url = page.get("thumbnail",{}).get("source")
            if url:
                return url
    except:
        pass
    return None

@st.cache_data(ttl=86400)
def get_team_badge(wiki_title: str):
    return get_wiki_photo(wiki_title)

# ── Build stickers ─────────────────────────────────────────────────────────────
def build_stickers():
    all_s = []
    for s in SPECIAL_STICKERS:
        all_s.append({"id":s["id"],"name":s["name"],"name_en":s["name_en"],
                       "team":"FWC","team_name":"FIFA Especial","team_name_en":"FIFA Special",
                       "flag":"🌍","wiki":"","default_rarity":s["rarity"],"type":"special"})
    for t in TEAMS:
        # Badge sticker (X1)
        all_s.append({"id":f"{t['code']}1","name":"Escudo del equipo","name_en":"Team Badge",
                       "team":t["code"],"team_name":t["name"],"team_name_en":t["name_en"],
                       "flag":t["flag"],"wiki":t["wiki"],"default_rarity":"foil","type":"badge"})
        for i, (p_es, p_en) in enumerate(zip(t["players"], t["players_en"])):
            num = i + 2
            is_photo = p_es in ("Foto del Equipo","Team Photo")
            dr = "foil" if is_photo else "base"
            stype = "team_photo" if is_photo else "player"
            all_s.append({"id":f"{t['code']}{num}","name":p_es,"name_en":p_en,
                           "team":t["code"],"team_name":t["name"],"team_name_en":t["name_en"],
                           "flag":t["flag"],"wiki":t["wiki"],"default_rarity":dr,"type":stype})
    return all_s

ALL_STICKERS = build_stickers()

# ── Session state ──────────────────────────────────────────────────────────────
if "version" not in st.session_state:
    st.session_state.version = "mx"
if "mx_owned" not in st.session_state:
    st.session_state.mx_owned = set()
if "mx_rarity" not in st.session_state:
    st.session_state.mx_rarity = {}
if "usa_owned" not in st.session_state:
    st.session_state.usa_owned = set()
if "usa_rarity" not in st.session_state:
    st.session_state.usa_rarity = {}
if "mx_loaded" not in st.session_state:
    st.session_state.mx_loaded = False
if "usa_loaded" not in st.session_state:
    st.session_state.usa_loaded = False
if "selected" not in st.session_state:
    st.session_state.selected = None

# ── Load data for current version ─────────────────────────────────────────────
v = st.session_state.version
lang = "es" if v == "mx" else "en"
L = LANG[lang]
tab_name = "mexico_tracker" if v == "mx" else "usa_tracker"
sheet = get_sheet(tab_name)

if v == "mx" and not st.session_state.mx_loaded and sheet:
    o, r = load_data(sheet)
    st.session_state.mx_owned = o
    st.session_state.mx_rarity = r
    st.session_state.mx_loaded = True
elif v == "usa" and not st.session_state.usa_loaded and sheet:
    o, r = load_data(sheet)
    st.session_state.usa_owned = o
    st.session_state.usa_rarity = r
    st.session_state.usa_loaded = True

owned = st.session_state.mx_owned if v == "mx" else st.session_state.usa_owned
rarity_map = st.session_state.mx_rarity if v == "mx" else st.session_state.usa_rarity
show_rarity = (v == "usa")

def get_rarity(sid, default):
    return rarity_map.get(sid, default)

# ── Version toggle at top ──────────────────────────────────────────────────────
col_t1, col_t2, col_t3 = st.columns([1,2,1])
with col_t2:
    st.markdown("<br>", unsafe_allow_html=True)
    toggle_col1, toggle_col2 = st.columns(2)
    with toggle_col1:
        mx_style = "primary" if v == "mx" else "secondary"
        if st.button("🇲🇽 Versión México", use_container_width=True, type=mx_style):
            st.session_state.version = "mx"
            st.session_state.selected = None
            st.rerun()
    with toggle_col2:
        us_style = "primary" if v == "usa" else "secondary"
        if st.button("🇺🇸 USA Version", use_container_width=True, type=us_style):
            st.session_state.version = "usa"
            st.session_state.selected = None
            st.rerun()

st.markdown("---")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"## ⚽ {L['title']}")
    st.markdown("---")

    total = len(ALL_STICKERS)
    own_count = len(owned)
    pct = round(own_count / total * 100, 1)
    st.metric(L["collection"], f"{own_count} / {total}", f"{pct}%")

    if show_rarity:
        c1, c2 = st.columns(2)
        foils  = sum(1 for s in ALL_STICKERS if s["id"] in owned and get_rarity(s["id"], s["default_rarity"]) == "foil")
        blues  = sum(1 for s in ALL_STICKERS if s["id"] in owned and get_rarity(s["id"], s["default_rarity"]) == "blue")
        purps  = sum(1 for s in ALL_STICKERS if s["id"] in owned and get_rarity(s["id"], s["default_rarity"]) == "purple")
        reds   = sum(1 for s in ALL_STICKERS if s["id"] in owned and get_rarity(s["id"], s["default_rarity"]) == "red")
        c1.metric("🌟 Foil", foils)
        c2.metric("🟦 Blue", blues)
        c1.metric("🟣 Purple", purps)
        c2.metric("🟥 Red", reds)

    st.markdown("---")
    st.markdown(f"**{L['filters']}**")
    search = st.text_input(L["search"], "")
    filter_owned = st.selectbox(L["show"], [L["all"], L["owned_only"], L["missing_only"]])
    if show_rarity:
        rarity_options = [L["all_rarities"]] + [RARITY_CONFIG[k][lang] for k in RARITY_CONFIG]
        filter_rarity = st.selectbox(L["rarity"], rarity_options)
    else:
        filter_rarity = L["all_rarities"]
    team_options = [L["all_teams"]] + [t["name"] if v == "mx" else t["name_en"] for t in TEAMS]
    selected_team = st.selectbox(L["team"], team_options)

    if show_rarity:
        st.markdown("---")
        st.markdown(f"**{L['legend']}**")
        for k, rc in RARITY_CONFIG.items():
            st.markdown(f"{rc['star']} **{rc[lang]}**")

# ── Sticker detail ─────────────────────────────────────────────────────────────
def show_detail(s):
    r = get_rarity(s["id"], s["default_rarity"])
    rc = RARITY_CONFIG[r]
    is_owned = s["id"] in owned
    name = s["name"] if v == "mx" else s["name_en"]
    team_name = s["team_name"] if v == "mx" else s["team_name_en"]

    st.markdown(f"### {rc['star'] if show_rarity else '⚽'} {s['id']} — {name}")
    st.markdown(f"**{'Equipo' if lang=='es' else 'Team'}:** {team_name}")

    # Load image
    photo_url = None
    with st.spinner(L["loading"]):
        if s["type"] == "badge":
            photo_url = get_team_badge(s["wiki"])
        elif s["type"] == "team_photo":
            photo_url = get_team_badge(s["wiki"])
        elif s["type"] == "player":
            photo_url = get_wiki_photo(s["name_en"])

    if photo_url:
        try:
            resp = requests.get(photo_url, timeout=5)
            img = Image.open(BytesIO(resp.content))
            st.image(img, width=180, caption=name)
        except:
            st.info(L["no_photo"])
    else:
        st.info(L["no_photo"])

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if is_owned:
            if st.button(L["mark_missing"], use_container_width=True):
                owned.discard(s["id"])
                if sheet: save_sticker(sheet, s["id"], False, r)
                st.session_state.selected = None
                st.rerun()
        else:
            if st.button(L["mark_owned"], use_container_width=True):
                owned.add(s["id"])
                if sheet: save_sticker(sheet, s["id"], True, r)
                st.session_state.selected = None
                st.rerun()
    with c2:
        if show_rarity:
            rarity_keys = list(RARITY_CONFIG.keys())
            new_r = st.selectbox(L["set_rarity"], rarity_keys,
                                  index=rarity_keys.index(r),
                                  format_func=lambda x: f"{RARITY_CONFIG[x]['star']} {RARITY_CONFIG[x][lang]}")
            if new_r != r:
                rarity_map[s["id"]] = new_r
                if sheet: save_sticker(sheet, s["id"], is_owned, new_r)
                st.rerun()

    if st.button(L["back"], use_container_width=True):
        st.session_state.selected = None
        st.rerun()

# ── Main view ──────────────────────────────────────────────────────────────────
if st.session_state.selected:
    sid = st.session_state.selected
    match = next((s for s in ALL_STICKERS if s["id"] == sid), None)
    if match:
        show_detail(match)
    else:
        st.session_state.selected = None
        st.rerun()
else:
    st.markdown(f"## {L['page_title']}")

    # Filter
    filtered = []
    for s in ALL_STICKERS:
        r = get_rarity(s["id"], s["default_rarity"])
        is_owned = s["id"] in owned
        name = s["name"] if v == "mx" else s["name_en"]
        tname = s["team_name"] if v == "mx" else s["team_name_en"]

        if search and search.lower() not in name.lower() and search.lower() not in tname.lower():
            continue
        if filter_owned == L["owned_only"] and not is_owned:
            continue
        if filter_owned == L["missing_only"] and is_owned:
            continue
        if show_rarity and filter_rarity != L["all_rarities"]:
            if RARITY_CONFIG[r][lang] != filter_rarity:
                continue
        if selected_team != L["all_teams"] and tname != selected_team:
            continue
        filtered.append(s)

    # Group by team
    teams_shown = {}
    for s in filtered:
        teams_shown.setdefault(s["team"], []).append(s)

    if not teams_shown:
        st.info("No hay figuritas que coincidan." if lang == "es" else "No stickers match your filters.")
    else:
        for team_code, stickers in teams_shown.items():
            t_info = next((t for t in TEAMS if t["code"] == team_code), None)
            tname = t_info["name"] if (t_info and v == "mx") else (t_info["name_en"] if t_info else "FIFA Special")
            flag = t_info["flag"] if t_info else "🌍"

            t_owned = sum(1 for s in stickers if s["id"] in owned)
            t_total = len(stickers)
            t_pct = round(t_owned / t_total * 100)

            with st.expander(f"{flag} **{tname}** — {t_owned}/{t_total} ({t_pct}%)",
                             expanded=(selected_team != L["all_teams"])):
                st.progress(t_pct / 100)
                cols = st.columns(5)
                for i, s in enumerate(stickers):
                    r = get_rarity(s["id"], s["default_rarity"])
                    rc = RARITY_CONFIG[r]
                    is_owned = s["id"] in owned
                    name = s["name"] if v == "mx" else s["name_en"]
                    short = name[:13] + "…" if len(name) > 13 else name
                    border_class = f"rarity-{r}" if show_rarity else "rarity-none"
                    opacity = "owned-card" if is_owned else "missing-card"
                    star = rc["star"] if show_rarity else ("🌟" if r == "foil" else "")

                    with cols[i % 5]:
                        st.markdown(f"""
                        <div class="sticker-card {border_class} {opacity}">
                            <div style="font-size:15px;">{star}</div>
                            <div class="sticker-id">{s['id']}</div>
                            <div class="sticker-name">{short}</div>
                            {'<div class="owned-badge">' + L["owned_label"] + '</div>' if is_owned else ''}
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button(L["open"], key=f"btn_{v}_{s['id']}", use_container_width=True):
                            st.session_state.selected = s["id"]
                            st.rerun()
