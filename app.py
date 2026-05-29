import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(
    page_title="FIFA 2026 Sticker Tracker",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── GitHub raw image base URL ──────────────────────────────────────────────────
GITHUB_IMG = "https://raw.githubusercontent.com/ValiTheCat/Mexico-Fifa-2026-Album/main/images/"

st.markdown("""
<style>
.s-card {
    border-radius: 12px; padding: 8px 6px 6px;
    text-align: center; border: 2.5px solid #374151;
    background: #1f2937; min-height: 165px;
    display: flex; flex-direction: column;
    align-items: center; gap: 3px;
}
.s-missing { opacity: 0.28; filter: grayscale(90%); }
.s-owned   { opacity: 1.0;  filter: none; }
.r-base   { border-color: #4b5563 !important; }
.r-blue   { border-color: #3b82f6 !important; background:#1e3a5f !important; }
.r-purple { border-color: #a855f7 !important; background:#2e1a47 !important; }
.r-red    { border-color: #ef4444 !important; background:#3b1219 !important; }
.r-foil   { border-color: #f59e0b !important; background:#3b2a08 !important; }
.s-img  { width:70px; height:78px; object-fit:cover; object-position:top; border-radius:8px; }
.s-ph   { width:70px; height:78px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:30px; }
.s-id   { font-size:10px; font-weight:700; color:#9ca3af; }
.s-name { font-size:9px;  color:#6b7280; line-height:1.2; }
.s-chk  { font-size:11px; color:#34d399; font-weight:700; }
.rarity-row { display:flex; gap:2px; justify-content:center; margin-top:2px; flex-wrap:wrap; }
.r-pill { font-size:8px; padding:1px 4px; border-radius:8px; font-weight:700; border:1.5px solid transparent; cursor:default; }
.prog-bg   { height:4px; background:#374151; border-radius:2px; margin-bottom:10px; }
.prog-fill { height:4px; border-radius:2px; transition:width .3s; }
.in-btn {
    width:100%; margin-top:4px; padding:5px 4px;
    border-radius:8px; font-size:11px; font-weight:600;
    text-align:center; cursor:default;
}
/* Hide the Streamlit toggle buttons visually — they still work on click */
div[data-testid="stButton"] { height:0; overflow:hidden; margin:0; padding:0; }
</style>
""", unsafe_allow_html=True)

RARITY_CONFIG = {
    "base":   {"en":"Base",   "es":"Base",   "star":"⬜","color":"#4b5563","border":"#4b5563","bg":"#1f2937"},
    "blue":   {"en":"Blue",   "es":"Azul",   "star":"🟦","color":"#3b82f6","border":"#3b82f6","bg":"#1e3a5f"},
    "purple": {"en":"Purple", "es":"Morado", "star":"🟣","color":"#a855f7","border":"#a855f7","bg":"#2e1a47"},
    "red":    {"en":"Red",    "es":"Rojo",   "star":"🟥","color":"#ef4444","border":"#ef4444","bg":"#3b1219"},
    "foil":   {"en":"Foil",   "es":"Foil",   "star":"🌟","color":"#f59e0b","border":"#f59e0b","bg":"#3b2a08"},
}

TEAMS = [
    {"code":"MEX","es":"México","en":"Mexico","flag":"🇲🇽","color":"#006847","players_es":["Luis Malagón","Johan Vasquez","Jorge Sánchez","Cesar Montes","Jesus Gallardo","Israel Reyes","Diego Lainez","Carlos Rodriguez","Edson Alvarez","Orbelin Pineda","Marcel Ruiz","Foto del Equipo","Érick Sánchez","Hirving Lozano","Santiago Giménez","Raúl Jiménez","Alexis Vega","Roberto Alvarado","Cesar Huerta"],"players_en":["Luis Malagón","Johan Vasquez","Jorge Sánchez","Cesar Montes","Jesus Gallardo","Israel Reyes","Diego Lainez","Carlos Rodriguez","Edson Alvarez","Orbelin Pineda","Marcel Ruiz","Team Photo","Érick Sánchez","Hirving Lozano","Santiago Giménez","Raúl Jiménez","Alexis Vega","Roberto Alvarado","Cesar Huerta"]},
    {"code":"USA","es":"Estados Unidos","en":"USA","flag":"🇺🇸","color":"#002868","players_es":["Matt Freese","Chris Richards","Tim Ream","Mark McKenzie","Alex Freeman","Antonee Robinson","Tyler Adams","Tanner Tessmann","Weston McKennie","Christian Roldan","Timothy Weah","Foto del Equipo","Diego Luna","Malik Tillman","Christian Pulisic","Brenden Aaronson","Ricardo Pepi","Haji Wright","Folarin Balogun"],"players_en":["Matt Freese","Chris Richards","Tim Ream","Mark McKenzie","Alex Freeman","Antonee Robinson","Tyler Adams","Tanner Tessmann","Weston McKennie","Christian Roldan","Timothy Weah","Team Photo","Diego Luna","Malik Tillman","Christian Pulisic","Brenden Aaronson","Ricardo Pepi","Haji Wright","Folarin Balogun"]},
    {"code":"CAN","es":"Canadá","en":"Canada","flag":"🇨🇦","color":"#c0392b","players_es":["Dayne St.Clair","Alphonso Davies","Alistair Johnston","Samuel Adekugbe","Riche Larvea","Derek Cornelius","Moïse Bombito","Kamal Miller","Stephen Eustáquio","Ismaël Koné","Jonathan Osorio","Foto del Equipo","Jacob Shaffelburg","Mathieu Choinière","Niko Sigur","Tajon Buchanan","Liam Millar","Cyle Larin","Jonathan David"],"players_en":["Dayne St.Clair","Alphonso Davies","Alistair Johnston","Samuel Adekugbe","Riche Larvea","Derek Cornelius","Moïse Bombito","Kamal Miller","Stephen Eustáquio","Ismaël Koné","Jonathan Osorio","Team Photo","Jacob Shaffelburg","Mathieu Choinière","Niko Sigur","Tajon Buchanan","Liam Millar","Cyle Larin","Jonathan David"]},
    {"code":"BRA","es":"Brasil","en":"Brazil","flag":"🇧🇷","color":"#009c3b","players_es":["Alisson","Bento","Marquinhos","Éder Militão","Gabriel Magalhães","Danilo","Wesley","Lucas Paquetá","Casemiro","Bruno Guimarães","Luiz Henrique","Foto del Equipo","Vinicius Júnior","Rodrygo","João Pedro","Matheus Cunha","Gabriel Martinelli","Raphinha","Estévão"],"players_en":["Alisson","Bento","Marquinhos","Éder Militão","Gabriel Magalhães","Danilo","Wesley","Lucas Paquetá","Casemiro","Bruno Guimarães","Luiz Henrique","Team Photo","Vinicius Júnior","Rodrygo","João Pedro","Matheus Cunha","Gabriel Martinelli","Raphinha","Estévão"]},
    {"code":"ARG","es":"Argentina","en":"Argentina","flag":"🇦🇷","color":"#74acdf","players_es":["Franco Armani","Emiliano Martínez","Nahuel Molina","Cristian Romero","Lisandro Martínez","Nicolás Otamendi","Marcos Acuña","Rodrigo De Paul","Leandro Paredes","Giovani Lo Celso","Ángel Di María","Foto del Equipo","Alexis Mac Allister","Nicolás González","Lautaro Martínez","Julián Álvarez","Paulo Dybala","Thiago Almada","Valentin Carboni"],"players_en":["Franco Armani","Emiliano Martínez","Nahuel Molina","Cristian Romero","Lisandro Martínez","Nicolás Otamendi","Marcos Acuña","Rodrigo De Paul","Leandro Paredes","Giovani Lo Celso","Ángel Di María","Team Photo","Alexis Mac Allister","Nicolás González","Lautaro Martínez","Julián Álvarez","Paulo Dybala","Thiago Almada","Valentin Carboni"]},
    {"code":"ENG","es":"Inglaterra","en":"England","flag":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","color":"#012169","players_es":["Jordan Pickford","Dean Henderson","Reece James","John Stones","Harry Maguire","Luke Shaw","Kieran Trippier","Declan Rice","Jude Bellingham","Phil Foden","Bukayo Saka","Foto del Equipo","Morgan Rogers","Marcus Rashford","Harry Kane","Ollie Watkins","Cole Palmer","Anthony Gordon","Jarrod Bowen"],"players_en":["Jordan Pickford","Dean Henderson","Reece James","John Stones","Harry Maguire","Luke Shaw","Kieran Trippier","Declan Rice","Jude Bellingham","Phil Foden","Bukayo Saka","Team Photo","Morgan Rogers","Marcus Rashford","Harry Kane","Ollie Watkins","Cole Palmer","Anthony Gordon","Jarrod Bowen"]},
    {"code":"GER","es":"Alemania","en":"Germany","flag":"🇩🇪","color":"#888888","players_es":["Manuel Neuer","Marc ter Stegen","Jonathan Tah","Nico Schlotterbeck","David Raum","Max Mittelstädt","Robert Andrich","Joshua Kimmich","Florian Wirtz","Ilkay Gündogan","Leon Goretzka","Foto del Equipo","Leroy Sané","Jamal Musiala","Thomas Müller","Serge Gnabry","Kai Havertz","Niclas Füllkrug","Deniz Undav"],"players_en":["Manuel Neuer","Marc ter Stegen","Jonathan Tah","Nico Schlotterbeck","David Raum","Max Mittelstädt","Robert Andrich","Joshua Kimmich","Florian Wirtz","Ilkay Gündogan","Leon Goretzka","Team Photo","Leroy Sané","Jamal Musiala","Thomas Müller","Serge Gnabry","Kai Havertz","Niclas Füllkrug","Deniz Undav"]},
    {"code":"FRA","es":"Francia","en":"France","flag":"🇫🇷","color":"#002395","players_es":["Mike Maignan","Alphonse Areola","Jules Koundé","Dayot Upamecano","William Saliba","Theo Hernandez","Lucas Hernandez","Aurélien Tchouaméni","Eduardo Camavinga","Mattéo Guendouzi","Adrien Rabiot","Foto del Equipo","Antoine Griezmann","Ousmane Dembélé","Kylian Mbappé","Marcus Thuram","Randal Kolo Muani","Jonathan Clauss","Bradley Barcola"],"players_en":["Mike Maignan","Alphonse Areola","Jules Koundé","Dayot Upamecano","William Saliba","Theo Hernandez","Lucas Hernandez","Aurélien Tchouaméni","Eduardo Camavinga","Mattéo Guendouzi","Adrien Rabiot","Team Photo","Antoine Griezmann","Ousmane Dembélé","Kylian Mbappé","Marcus Thuram","Randal Kolo Muani","Jonathan Clauss","Bradley Barcola"]},
    {"code":"ESP","es":"España","en":"Spain","flag":"🇪🇸","color":"#c60b1e","players_es":["Unai Simón","David Raya","Dani Carvajal","Aymeric Laporte","Robin Le Normand","Alejandro Grimaldo","Jesús Navas","Rodri","Pedri","Fabián Ruiz","Dani Olmo","Foto del Equipo","Ferrán Torres","Nico Williams","Álvaro Morata","Joselu","Mikel Oyarzabal","Lamine Yamal","Yeremy Pino"],"players_en":["Unai Simón","David Raya","Dani Carvajal","Aymeric Laporte","Robin Le Normand","Alejandro Grimaldo","Jesús Navas","Rodri","Pedri","Fabián Ruiz","Dani Olmo","Team Photo","Ferrán Torres","Nico Williams","Álvaro Morata","Joselu","Mikel Oyarzabal","Lamine Yamal","Yeremy Pino"]},
    {"code":"POR","es":"Portugal","en":"Portugal","flag":"🇵🇹","color":"#006600","players_es":["Rui Patrício","Diogo Costa","João Cancelo","Rúben Dias","Pepe","Nuno Mendes","Danilo Pereira","Bruno Fernandes","Bernardo Silva","João Palhinha","Vitinha","Foto del Equipo","Rafael Leão","Diogo Jota","Cristiano Ronaldo","Gonçalo Ramos","Pedro Neto","João Félix","Francisco Conceição"],"players_en":["Rui Patrício","Diogo Costa","João Cancelo","Rúben Dias","Pepe","Nuno Mendes","Danilo Pereira","Bruno Fernandes","Bernardo Silva","João Palhinha","Vitinha","Team Photo","Rafael Leão","Diogo Jota","Cristiano Ronaldo","Gonçalo Ramos","Pedro Neto","João Félix","Francisco Conceição"]},
    {"code":"NED","es":"Países Bajos","en":"Netherlands","flag":"🇳🇱","color":"#f36c21","players_es":["Bart Verbruggen","Mark Flekken","Denzel Dumfries","Virgil van Dijk","Stefan de Vrij","Nathan Aké","Tyrell Malacia","Ryan Gravenberch","Tijjani Reijnders","Teun Koopmeiners","Davy Klaassen","Foto del Equipo","Steven Bergwijn","Cody Gakpo","Memphis Depay","Wout Weghorst","Donyell Malen","Xavi Simons","Brian Brobbey"],"players_en":["Bart Verbruggen","Mark Flekken","Denzel Dumfries","Virgil van Dijk","Stefan de Vrij","Nathan Aké","Tyrell Malacia","Ryan Gravenberch","Tijjani Reijnders","Teun Koopmeiners","Davy Klaassen","Team Photo","Steven Bergwijn","Cody Gakpo","Memphis Depay","Wout Weghorst","Donyell Malen","Xavi Simons","Brian Brobbey"]},
    {"code":"ITA","es":"Italia","en":"Italy","flag":"🇮🇹","color":"#0066cc","players_es":["Gianluigi Donnarumma","Alex Meret","Giovanni Di Lorenzo","Alessandro Bastoni","Federico Gatti","Federico Dimarco","Davide Frattesi","Sandro Tonali","Nicolò Barella","Lorenzo Pellegrini","Nicolò Fagioli","Foto del Equipo","Federico Chiesa","Matteo Politano","Gianluca Scamacca","Lorenzo Lucca","Giacomo Raspadori","Mateo Retegui","Wilfried Gnonto"],"players_en":["Gianluigi Donnarumma","Alex Meret","Giovanni Di Lorenzo","Alessandro Bastoni","Federico Gatti","Federico Dimarco","Davide Frattesi","Sandro Tonali","Nicolò Barella","Lorenzo Pellegrini","Nicolò Fagioli","Team Photo","Federico Chiesa","Matteo Politano","Gianluca Scamacca","Lorenzo Lucca","Giacomo Raspadori","Mateo Retegui","Wilfried Gnonto"]},
    {"code":"SCO","es":"Escocia","en":"Scotland","flag":"🏴󠁧󠁢󠁳󠁣󠁴󠁿","color":"#003087","players_es":["Angus Gunn","Jack Hendry","Kieran Tierney","Aaron Hickey","Andrew Robertson","Scott McKenna","John Souttar","Anthony Ralston","Grant Hanley","Scott McTominay","Billy Gilmour","Foto del Equipo","Lewis Ferguson","Ryan Christie","Kenny McLean","John McGinn","Lyndon Dykes","Che Adams","Ben Doak"],"players_en":["Angus Gunn","Jack Hendry","Kieran Tierney","Aaron Hickey","Andrew Robertson","Scott McKenna","John Souttar","Anthony Ralston","Grant Hanley","Scott McTominay","Billy Gilmour","Team Photo","Lewis Ferguson","Ryan Christie","Kenny McLean","John McGinn","Lyndon Dykes","Che Adams","Ben Doak"]},
    {"code":"CZE","es":"Chequia","en":"Czechia","flag":"🇨🇿","color":"#d7141a","players_es":["Matej Kovar","Jindrich Stanek","Ladislav Krejci","Vladimir Coufal","Jaroslav Zeleny","Tomas Holes","David Zima","Michal Sadilek","Lukas Provod","Lukas Cerv","Tomas Soucek","Foto del Equipo","Pavel Sulc","Matej Vydra","Vasil Kusej","Tomas Chory","Vaclav Cerny","Adam Hlozek","Patrik Schick"],"players_en":["Matej Kovar","Jindrich Stanek","Ladislav Krejci","Vladimir Coufal","Jaroslav Zeleny","Tomas Holes","David Zima","Michal Sadilek","Lukas Provod","Lukas Cerv","Tomas Soucek","Team Photo","Pavel Sulc","Matej Vydra","Vasil Kusej","Tomas Chory","Vaclav Cerny","Adam Hlozek","Patrik Schick"]},
    {"code":"NOR","es":"Noruega","en":"Norway","flag":"🇳🇴","color":"#ef2b2d","players_es":["Orjan Nyland","Mats Selnaes","Kristoffer Ajer","Leo Ostigard","Andreas Hanche-Olsen","Birger Meling","Vegar Hedenstad","Mathias Normann","Patrick Berg","Fredrik Aursnes","Sander Berge","Foto del Equipo","Martin Odegaard","Antonio Nusa","Mohamed Elyounoussi","Erling Haaland","Alexander Sorloth","Ola Solbakken","Jens Petter Hauge"],"players_en":["Orjan Nyland","Mats Selnaes","Kristoffer Ajer","Leo Ostigard","Andreas Hanche-Olsen","Birger Meling","Vegar Hedenstad","Mathias Normann","Patrick Berg","Fredrik Aursnes","Sander Berge","Team Photo","Martin Odegaard","Antonio Nusa","Mohamed Elyounoussi","Erling Haaland","Alexander Sorloth","Ola Solbakken","Jens Petter Hauge"]},
    {"code":"SWE","es":"Suecia","en":"Sweden","flag":"🇸🇪","color":"#006aa7","players_es":["Robin Olsen","Isak Pettersson","Carl Starfelt","Victor Lindelöf","Isak Hien","Marcus Danielson","Emil Krafth","Jens Cajuste","Viktor Claesson","Hugo Larsson","Viktor Johansson","Foto del Equipo","Dejan Kulusevski","Alexander Isak","Robin Quaison","Jordan Larsson","Kristoffer Zachrisson","Emil Forsberg","Pontus Almqvist"],"players_en":["Robin Olsen","Isak Pettersson","Carl Starfelt","Victor Lindelöf","Isak Hien","Marcus Danielson","Emil Krafth","Jens Cajuste","Viktor Claesson","Hugo Larsson","Viktor Johansson","Team Photo","Dejan Kulusevski","Alexander Isak","Robin Quaison","Jordan Larsson","Kristoffer Zachrisson","Emil Forsberg","Pontus Almqvist"]},
    {"code":"AUS","es":"Australia","en":"Australia","flag":"🇦🇺","color":"#00843d","players_es":["Mathew Ryan","Joe Gauci","Harry Souttar","Alessandro Circati","Jordan Bos","Aziz Behich","Cameron Burgess","Lewis Miller","Milos Degenek","Jackson Irvine","Riley McGree","Foto del Equipo","Aiden O'Neill","Connor Metcalfe","Patrick Yazbek","Craig Goodwin","Kusini Yengi","Nestory Irankunda","Mohamed Touré"],"players_en":["Mathew Ryan","Joe Gauci","Harry Souttar","Alessandro Circati","Jordan Bos","Aziz Behich","Cameron Burgess","Lewis Miller","Milos Degenek","Jackson Irvine","Riley McGree","Team Photo","Aiden O'Neill","Connor Metcalfe","Patrick Yazbek","Craig Goodwin","Kusini Yengi","Nestory Irankunda","Mohamed Touré"]},
    {"code":"RSA","es":"Sudáfrica","en":"South Africa","flag":"🇿🇦","color":"#007749","players_es":["Ronwen Williams","Sipho Chaine","Aubrey Modiba","Samukele Kabini","Mbekezeli Mbokazi","Khulumani Ndamane","Siyabonga Ngezana","Khuliso Mudau","Nkosinathi Sibisi","Teboho Mokoena","Thalente Mbatha","Foto del Equipo","Bathasi Aubaas","Yaya Sithole","Sipho Mbule","Lyle Foster","Iqraam Rayners","Mohau Nkota","Oswin Appollis"],"players_en":["Ronwen Williams","Sipho Chaine","Aubrey Modiba","Samukele Kabini","Mbekezeli Mbokazi","Khulumani Ndamane","Siyabonga Ngezana","Khuliso Mudau","Nkosinathi Sibisi","Teboho Mokoena","Thalente Mbatha","Team Photo","Bathasi Aubaas","Yaya Sithole","Sipho Mbule","Lyle Foster","Iqraam Rayners","Mohau Nkota","Oswin Appollis"]},
    {"code":"KOR","es":"Corea del Sur","en":"South Korea","flag":"🇰🇷","color":"#c60c30","players_es":["Hyeon-woo Jo","Seung-Gyu Kim","Min-jae Kim","Yu-min Cho","Young-woo Seol","Han-beom Lee","Tae-seok Lee","Myung-jae Lee","Jae-sung Lee","In-beom Hwang","Kang-in Lee","Foto del Equipo","Seung-ho Paik","Jens Castrop","Dong-yeong Lee","Gue-sung Cho","Heung-min Son","Hee-chan Hwang","Hyeon-Gyu Oh"],"players_en":["Hyeon-woo Jo","Seung-Gyu Kim","Min-jae Kim","Yu-min Cho","Young-woo Seol","Han-beom Lee","Tae-seok Lee","Myung-jae Lee","Jae-sung Lee","In-beom Hwang","Kang-in Lee","Team Photo","Seung-ho Paik","Jens Castrop","Dong-yeong Lee","Gue-sung Cho","Heung-min Son","Hee-chan Hwang","Hyeon-Gyu Oh"]},
    {"code":"JPN","es":"Japón","en":"Japan","flag":"🇯🇵","color":"#bc002d","players_es":["Shuichi Gonda","Daniel Schmidt","Takehiro Tomiyasu","Ko Itakura","Shogo Taniguchi","Yuto Nagatomo","Hiroki Ito","Wataru Endo","Ao Tanaka","Hidemasa Morita","Junya Ito","Foto del Equipo","Takumi Minamino","Kaoru Mitoma","Ritsu Doan","Ayase Ueda","Yukinari Sugawara","Daichi Kamada","Keito Nakamura"],"players_en":["Shuichi Gonda","Daniel Schmidt","Takehiro Tomiyasu","Ko Itakura","Shogo Taniguchi","Yuto Nagatomo","Hiroki Ito","Wataru Endo","Ao Tanaka","Hidemasa Morita","Junya Ito","Team Photo","Takumi Minamino","Kaoru Mitoma","Ritsu Doan","Ayase Ueda","Yukinari Sugawara","Daichi Kamada","Keito Nakamura"]},
    {"code":"EGY","es":"Egipto","en":"Egypt","flag":"🇪🇬","color":"#ce1126","players_es":["Mohamed Abou Gabal","Mohamed El-Shenawy","Ahmed Hegazy","Omar Kamal","Mohamed Abdelmonem","Akram Tawfik","Mahmoud El Wensh","Amr El Sulaya","Mohamed Elneny","Taher Mohamed Taher","Mohamed Hamdy","Foto del Equipo","Emam Ashour","Zizo","Omar Marmoush","Mostafa Mohamed","Hussein El Shahat","Marwan Attia","Trezeguet"],"players_en":["Mohamed Abou Gabal","Mohamed El-Shenawy","Ahmed Hegazy","Omar Kamal","Mohamed Abdelmonem","Akram Tawfik","Mahmoud El Wensh","Amr El Sulaya","Mohamed Elneny","Taher Mohamed Taher","Mohamed Hamdy","Team Photo","Emam Ashour","Zizo","Omar Marmoush","Mostafa Mohamed","Hussein El Shahat","Marwan Attia","Trezeguet"]},
    {"code":"IRN","es":"Irán","en":"Iran","flag":"🇮🇷","color":"#239f40","players_es":["Alireza Beiranvand","Amir Abedzadeh","Shoja Khalilzadeh","Majid Hosseini","Hossein Kanaanizadegan","Milad Mohammadi","Roozbeh Cheshmi","Saeid Ezatolahi","Ali Karimi","Mehdi Torabi","Ahmad Noorollahi","Foto del Equipo","Sardar Azmoun","Saman Ghoddos","Karim Ansarifard","Mehdi Taremi","Ali Gholizadeh","Allahyar Sayyadmanesh","Omid Noorafkan"],"players_en":["Alireza Beiranvand","Amir Abedzadeh","Shoja Khalilzadeh","Majid Hosseini","Hossein Kanaanizadegan","Milad Mohammadi","Roozbeh Cheshmi","Saeid Ezatolahi","Ali Karimi","Mehdi Torabi","Ahmad Noorollahi","Team Photo","Sardar Azmoun","Saman Ghoddos","Karim Ansarifard","Mehdi Taremi","Ali Gholizadeh","Allahyar Sayyadmanesh","Omid Noorafkan"]},
    {"code":"QAT","es":"Catar","en":"Qatar","flag":"🇶🇦","color":"#8d1b3d","players_es":["Meshaal Barsham","Sultan Albrake","Lucas Mendes","Homam Ahmed","Boualem Khoukhi","Pedro Miguel","Tarek Salman","Mohamed Al-Mannai","Karim Boudiaf","Assim Madibo","Ahmed Fatehi","Foto del Equipo","Mohammed Waad","Abdulaziz Hatem","Hassan Al-Haydos","Edmilson Junior","Akram Afif","Ahmed Al Ganehi","Almoez Ali"],"players_en":["Meshaal Barsham","Sultan Albrake","Lucas Mendes","Homam Ahmed","Boualem Khoukhi","Pedro Miguel","Tarek Salman","Mohamed Al-Mannai","Karim Boudiaf","Assim Madibo","Ahmed Fatehi","Team Photo","Mohammed Waad","Abdulaziz Hatem","Hassan Al-Haydos","Edmilson Junior","Akram Afif","Ahmed Al Ganehi","Almoez Ali"]},
    {"code":"SUI","es":"Suiza","en":"Switzerland","flag":"🇨🇭","color":"#d52b1e","players_es":["Gregor Kobel","Yvon Mvogo","Manuel Akanji","Ricardo Rodriguez","Nico Elvedi","Aurèle Amenda","Silvan Widmer","Granit Xhaka","Denis Zakaria","Remo Freuler","Fabian Rieder","Foto del Equipo","Ardon Jashari","Johan Manzambi","Michel Aebischer","Breel Embolo","Ruben Vargas","Dan Ndoye","Zeki Amdouni"],"players_en":["Gregor Kobel","Yvon Mvogo","Manuel Akanji","Ricardo Rodriguez","Nico Elvedi","Aurèle Amenda","Silvan Widmer","Granit Xhaka","Denis Zakaria","Remo Freuler","Fabian Rieder","Team Photo","Ardon Jashari","Johan Manzambi","Michel Aebischer","Breel Embolo","Ruben Vargas","Dan Ndoye","Zeki Amdouni"]},
    {"code":"MAR","es":"Marruecos","en":"Morocco","flag":"🇲🇦","color":"#c1272d","players_es":["Yassine Bounou","Munir El Kajoui","Achraf Hakimi","Noussair Mazraoui","Nayef Aguerd","Roman Saiss","Jawad El Yamiq","Adam Masina","Sofyan Amrabat","Azzedine Ounahi","Eliesse Ben Seghir","Foto del Equipo","Bilal El Khannouss","Ismael Saibari","Youssef En-Nesyri","Abde Ezzalzouli","Soufiane Rahimi","Brahim Diaz","Ayoub El Kaabi"],"players_en":["Yassine Bounou","Munir El Kajoui","Achraf Hakimi","Noussair Mazraoui","Nayef Aguerd","Roman Saiss","Jawad El Yamiq","Adam Masina","Sofyan Amrabat","Azzedine Ounahi","Eliesse Ben Seghir","Team Photo","Bilal El Khannouss","Ismael Saibari","Youssef En-Nesyri","Abde Ezzalzouli","Soufiane Rahimi","Brahim Diaz","Ayoub El Kaabi"]},
    {"code":"COL","es":"Colombia","en":"Colombia","flag":"🇨🇴","color":"#fcd116","players_es":["David Ospina","Camilo Vargas","Davinson Sánchez","Yerry Mina","Daniel Muñoz","Johan Mojica","Lerma","Wilmar Barrios","Mateus Uribe","Luis Díaz","James Rodríguez","Foto del Equipo","Rafael Santos Borré","Cucho Hernández","Falcao","Jhon Córdoba","Miguel Borja","Jhon Durán","Jhon Arias"],"players_en":["David Ospina","Camilo Vargas","Davinson Sánchez","Yerry Mina","Daniel Muñoz","Johan Mojica","Lerma","Wilmar Barrios","Mateus Uribe","Luis Díaz","James Rodríguez","Team Photo","Rafael Santos Borré","Cucho Hernández","Falcao","Jhon Córdoba","Miguel Borja","Jhon Durán","Jhon Arias"]},
    {"code":"URU","es":"Uruguay","en":"Uruguay","flag":"🇺🇾","color":"#5b9bd5","players_es":["Fernando Muslera","Sergio Rochet","Ronald Araújo","José María Giménez","Mathías Olivera","Nahitan Nández","Lucas Torreira","Federico Valverde","Rodrigo Bentancur","Giorgian De Arrascaeta","Facundo Pellistri","Foto del Equipo","Darwin Núñez","Luis Suárez","Edinson Cavani","Maxi Gómez","Brian Rodríguez","Agustín Canobbio","Ignacio De La Cruz"],"players_en":["Fernando Muslera","Sergio Rochet","Ronald Araújo","José María Giménez","Mathías Olivera","Nahitan Nández","Lucas Torreira","Federico Valverde","Rodrigo Bentancur","Giorgian De Arrascaeta","Facundo Pellistri","Team Photo","Darwin Núñez","Luis Suárez","Edinson Cavani","Maxi Gómez","Brian Rodríguez","Agustín Canobbio","Ignacio De La Cruz"]},
    {"code":"GHA","es":"Ghana","en":"Ghana","flag":"🇬🇭","color":"#006b3f","players_es":["Lawrence Ati-Zigi","Jojo Wollacott","Andy Yiadom","Alexander Djiku","Daniel Amartey","Alidu Seidu","Baba Rahman","Thomas Partey","Salis Abdul Samed","Mohammed Kudus","Emmanuel Gyasi","Foto del Equipo","Antoine Semenyo","Jordan Ayew","Andre Ayew","Felix Afena-Gyan","Gideon Mensah","Kamaldeen Sulemana","Inaki Williams"],"players_en":["Lawrence Ati-Zigi","Jojo Wollacott","Andy Yiadom","Alexander Djiku","Daniel Amartey","Alidu Seidu","Baba Rahman","Thomas Partey","Salis Abdul Samed","Mohammed Kudus","Emmanuel Gyasi","Team Photo","Antoine Semenyo","Jordan Ayew","Andre Ayew","Felix Afena-Gyan","Gideon Mensah","Kamaldeen Sulemana","Inaki Williams"]},
    {"code":"SEN","es":"Senegal","en":"Senegal","flag":"🇸🇳","color":"#00853f","players_es":["Edouard Mendy","Seny Dieng","Kalidou Koulibaly","Abdou Diallo","Ismail Jakobs","Formose Mendy","Pape Abou Cissé","Lamine Camara","Idrissa Gana Gueye","Nampalys Mendy","Krepin Diatta","Foto del Equipo","Iliman Ndiaye","Boulaye Dia","Sadio Mané","Nicolas Jackson","Ismaila Sarr","Habib Diallo","Yehvann Diouf"],"players_en":["Edouard Mendy","Seny Dieng","Kalidou Koulibaly","Abdou Diallo","Ismail Jakobs","Formose Mendy","Pape Abou Cissé","Lamine Camara","Idrissa Gana Gueye","Nampalys Mendy","Krepin Diatta","Team Photo","Iliman Ndiaye","Boulaye Dia","Sadio Mané","Nicolas Jackson","Ismaila Sarr","Habib Diallo","Yehvann Diouf"]},
    {"code":"NGA","es":"Nigeria","en":"Nigeria","flag":"🇳🇬","color":"#008751","players_es":["Francis Uzoho","Stanley Nwabali","Semi Ajayi","William Troost-Ekong","Zaidu Sanusi","Bright Osayi-Samuel","Ola Aina","Frank Onyeka","Alex Iwobi","Wilfred Ndidi","Kelechi Iheanacho","Foto del Equipo","Samuel Chukwueze","Ademola Lookman","Moses Simon","Victor Osimhen","Terem Moffi","Taiwo Awoniyi","Cyriel Dessers"],"players_en":["Francis Uzoho","Stanley Nwabali","Semi Ajayi","William Troost-Ekong","Zaidu Sanusi","Bright Osayi-Samuel","Ola Aina","Frank Onyeka","Alex Iwobi","Wilfred Ndidi","Kelechi Iheanacho","Team Photo","Samuel Chukwueze","Ademola Lookman","Moses Simon","Victor Osimhen","Terem Moffi","Taiwo Awoniyi","Cyriel Dessers"]},
    {"code":"CMR","es":"Camerún","en":"Cameroon","flag":"🇨🇲","color":"#007a5e","players_es":["André Onana","Fabrice Ondoa","Harold Moukoudi","Jean-Charles Castelletto","Collins Fai","Ambroise Oyongo","Nicolas Nkoulou","Samuel Oum Gouet","Frank Zambo Anguissa","Pierre Kunde","Martin Hongla","Foto del Equipo","Bryan Mbeumo","Karl Toko Ekambi","Vincent Aboubakar","Eric Choupo-Moting","Stéphane Bahoken","Georges-Kevin N'Koudou","Ignatius Ganago"],"players_en":["André Onana","Fabrice Ondoa","Harold Moukoudi","Jean-Charles Castelletto","Collins Fai","Ambroise Oyongo","Nicolas Nkoulou","Samuel Oum Gouet","Frank Zambo Anguissa","Pierre Kunde","Martin Hongla","Team Photo","Bryan Mbeumo","Karl Toko Ekambi","Vincent Aboubakar","Eric Choupo-Moting","Stéphane Bahoken","Georges-Kevin N'Koudou","Ignatius Ganago"]},
    {"code":"CIV","es":"Costa de Marfil","en":"Côte d'Ivoire","flag":"🇨🇮","color":"#f77f00","players_es":["Yahia Fofana","Badra Sangaré","Simon Deli","Willy Boly","Serge Aurier","Ghislain Konan","Wilfried Kanon","Ibrahim Sangaré","Jean-Michaël Seri","Franck Kessie","Sekou Sanogo","Foto del Equipo","Nicolas Pépé","Jonathan Bamba","Wilfried Zaha","Sébastien Haller","Simon Adingra","Oumar Diakité","Odilon Kossounou"],"players_en":["Yahia Fofana","Badra Sangaré","Simon Deli","Willy Boly","Serge Aurier","Ghislain Konan","Wilfried Kanon","Ibrahim Sangaré","Jean-Michaël Seri","Franck Kessie","Sekou Sanogo","Team Photo","Nicolas Pépé","Jonathan Bamba","Wilfried Zaha","Sébastien Haller","Simon Adingra","Oumar Diakité","Odilon Kossounou"]},
    {"code":"ALG","es":"Argelia","en":"Algeria","flag":"🇩🇿","color":"#006233","players_es":["Raïs M'Bolhi","Alexandre Oukidja","Ramy Bensebaini","Djamel Benlamri","Aissa Mandi","Youcef Atal","Lyès Chetti","Sofiane Feghouli","Ismaël Bennacer","Said Benrahma","Ramiz Zerrouki","Foto del Equipo","Youcef Belaïli","Adam Ounas","Islam Slimani","Baghdad Bounedjah","Riyad Mahrez","Andy Delort","Anis Ben Slimane"],"players_en":["Raïs M'Bolhi","Alexandre Oukidja","Ramy Bensebaini","Djamel Benlamri","Aissa Mandi","Youcef Atal","Lyès Chetti","Sofiane Feghouli","Ismaël Bennacer","Said Benrahma","Ramiz Zerrouki","Team Photo","Youcef Belaïli","Adam Ounas","Islam Slimani","Baghdad Bounedjah","Riyad Mahrez","Andy Delort","Anis Ben Slimane"]},
    {"code":"TUN","es":"Túnez","en":"Tunisia","flag":"🇹🇳","color":"#e70013","players_es":["Aymen Dahmen","Bechir Ben Said","Ali Maaloul","Montassar Talbi","Yassine Meriah","Mohamed Drager","Bilel Ifa","Ghailane Chaalali","Anis Ben Slimane","Mohamed Ben Romdhane","Hamza Mathlouthi","Foto del Equipo","Saîf-Eddine Khaoui","Seifeddine Jaziri","Naïm Sliti","Issam Jebali","Youssef Msakni","Taha Yassine Khenissi","Nizar Issaoui"],"players_en":["Aymen Dahmen","Bechir Ben Said","Ali Maaloul","Montassar Talbi","Yassine Meriah","Mohamed Drager","Bilel Ifa","Ghailane Chaalali","Anis Ben Slimane","Mohamed Ben Romdhane","Hamza Mathlouthi","Team Photo","Saîf-Eddine Khaoui","Seifeddine Jaziri","Naïm Sliti","Issam Jebali","Youssef Msakni","Taha Yassine Khenissi","Nizar Issaoui"]},
    {"code":"TUR","es":"Turquía","en":"Türkiye","flag":"🇹🇷","color":"#e30a17","players_es":["Ugurcan Cakir","Mert Gunok","Çaglar Söyüncü","Merih Demiral","Samet Akaydin","Ferdi Kadioglu","Zeki Celik","Hakan Calhanoglu","Kaan Ayhan","Orkun Kökcü","Kenan Yildiz","Foto del Equipo","Arda Güler","Yunus Akgun","Baris Alper Yilmaz","Efecan Karaca","Cenk Tosun","Umut Bozok","Serdar Dursun"],"players_en":["Ugurcan Cakir","Mert Gunok","Çaglar Söyüncü","Merih Demiral","Samet Akaydin","Ferdi Kadioglu","Zeki Celik","Hakan Calhanoglu","Kaan Ayhan","Orkun Kökcü","Kenan Yildiz","Team Photo","Arda Güler","Yunus Akgun","Baris Alper Yilmaz","Efecan Karaca","Cenk Tosun","Umut Bozok","Serdar Dursun"]},
    {"code":"AUT","es":"Austria","en":"Austria","flag":"🇦🇹","color":"#ed2939","players_es":["Patrick Pentz","Heinz Lindner","Stefan Posch","David Alaba","Gernot Trauner","Philipp Mwene","Maximilian Wöber","Nicolas Seiwald","Konrad Laimer","Marcel Sabitzer","Xaver Schlager","Foto del Equipo","Florian Kainz","Patrick Wimmer","Marko Arnautovic","Michael Gregoritsch","Christoph Baumgartner","Louis Schaub","Romano Schmid"],"players_en":["Patrick Pentz","Heinz Lindner","Stefan Posch","David Alaba","Gernot Trauner","Philipp Mwene","Maximilian Wöber","Nicolas Seiwald","Konrad Laimer","Marcel Sabitzer","Xaver Schlager","Team Photo","Florian Kainz","Patrick Wimmer","Marko Arnautovic","Michael Gregoritsch","Christoph Baumgartner","Louis Schaub","Romano Schmid"]},
    {"code":"BIH","es":"Bosnia y Herz.","en":"Bosnia & Herz.","flag":"🇧🇦","color":"#002395","players_es":["Nikola Vasilj","Amer Dedic","Sead Kolasinac","Tarik Muharemovic","Nihad Mujakic","Nikola Katic","Amir Hadziahmetovic","Benjamin Tahirovic","Armin Gigovic","Ivan Sunjic","Ivan Basic","Foto del Equipo","Dzenis Burnic","Esmir Bajraktarevic","Amar Memic","Ermedin Demirovic","Edin Dzeko","Samed Bazdar","Haris Tabakovic"],"players_en":["Nikola Vasilj","Amer Dedic","Sead Kolasinac","Tarik Muharemovic","Nihad Mujakic","Nikola Katic","Amir Hadziahmetovic","Benjamin Tahirovic","Armin Gigovic","Ivan Sunjic","Ivan Basic","Team Photo","Dzenis Burnic","Esmir Bajraktarevic","Amar Memic","Ermedin Demirovic","Edin Dzeko","Samed Bazdar","Haris Tabakovic"]},
    {"code":"UZB","es":"Uzbekistán","en":"Uzbekistan","flag":"🇺🇿","color":"#1eb53a","players_es":["Utkir Yusupov","Sherzod Nishonov","Sherzod Qoraboyev","Khurshid Tursunov","Akbar Bobojonov","Timur Jorayev","Oston Urunov","Jaloliddin Masharipov","Odil Akhmedov","Farrukh Tashkentov","Jamshid Iskanderov","Foto del Equipo","Eldor Shomurodov","Abbosbek Fayzullaev","Sherzod Nasrullaev","Bobur Abdixoliqov","Otabek Shukurov","Dostonbek Xolmatov","Khojiakbar Alijonov"],"players_en":["Utkir Yusupov","Sherzod Nishonov","Sherzod Qoraboyev","Khurshid Tursunov","Akbar Bobojonov","Timur Jorayev","Oston Urunov","Jaloliddin Masharipov","Odil Akhmedov","Farrukh Tashkentov","Jamshid Iskanderov","Team Photo","Eldor Shomurodov","Abbosbek Fayzullaev","Sherzod Nasrullaev","Bobur Abdixoliqov","Otabek Shukurov","Dostonbek Xolmatov","Khojiakbar Alijonov"]},
    {"code":"HAI","es":"Haití","en":"Haiti","flag":"🇭🇹","color":"#00209f","players_es":["Johny Placide","Carlens Arcus","Martin Expérience","Jean-Kevin Duverne","Ricardo Adé","Duke Lacroix","Garven Metusala","Hannes Delcroix","Leverton Pierre","Danley Jean Jacques","Jean-Ricner Bellegarde","Foto del Equipo","Christopher Attys","Derrick Etienne Jr","Josue Casimir","Ruben Providence","Duckens Nazon","Louicius Deedson","Frantzdy Pierrot"],"players_en":["Johny Placide","Carlens Arcus","Martin Expérience","Jean-Kevin Duverne","Ricardo Adé","Duke Lacroix","Garven Metusala","Hannes Delcroix","Leverton Pierre","Danley Jean Jacques","Jean-Ricner Bellegarde","Team Photo","Christopher Attys","Derrick Etienne Jr","Josue Casimir","Ruben Providence","Duckens Nazon","Louicius Deedson","Frantzdy Pierrot"]},
    {"code":"PAR","es":"Paraguay","en":"Paraguay","flag":"🇵🇾","color":"#0038a8","players_es":["Roberto Fernandez","Orlando Gill","Gustavo Gomez","Fabián Balbuena","Juan José Cáceres","Omar Alderete","Junior Alonso","Mathías Villasanti","Diego Gomez","Damián Bobadilla","Andres Cubas","Foto del Equipo","Matias Galarza","Julio Enciso","Alejandro Romero","Miguel Almirón","Ramon Sosa","Angel Romero","Antonio Sanabria"],"players_en":["Roberto Fernandez","Orlando Gill","Gustavo Gomez","Fabián Balbuena","Juan José Cáceres","Omar Alderete","Junior Alonso","Mathías Villasanti","Diego Gomez","Damián Bobadilla","Andres Cubas","Team Photo","Matias Galarza","Julio Enciso","Alejandro Romero","Miguel Almirón","Ramon Sosa","Angel Romero","Antonio Sanabria"]},
    {"code":"ECU","es":"Ecuador","en":"Ecuador","flag":"🇪🇨","color":"#ffda00","players_es":["Hernán Galíndez","Alexander Domínguez","Ángelo Preciado","Piero Hincapié","Jackson Porozo","Pervis Estupiñán","Diego Palacios","Carlos Gruezo","Jhegson Méndez","Moisés Caicedo","Jeremy Sarmiento","Foto del Equipo","Gonzalo Plata","Michael Estrada","Romario Ibarra","Enner Valencia","Ángel Mena","Jordy Caicedo","Leonardo Campana"],"players_en":["Hernán Galíndez","Alexander Domínguez","Ángelo Preciado","Piero Hincapié","Jackson Porozo","Pervis Estupiñán","Diego Palacios","Carlos Gruezo","Jhegson Méndez","Moisés Caicedo","Jeremy Sarmiento","Team Photo","Gonzalo Plata","Michael Estrada","Romario Ibarra","Enner Valencia","Ángel Mena","Jordy Caicedo","Leonardo Campana"]},
    {"code":"IRQ","es":"Irak","en":"Iraq","flag":"🇮🇶","color":"#007a3d","players_es":["Jalal Hassan","Fahad Tariq","Ali Adnan","Saad Natiq","Rebin Sulaka","Ahmed Ibrahim","Mustafa Nadhim","Hussein Ali","Amjad Attwan","Osama Rashid","Bashar Resan","Foto del Equipo","Mohanad Ali","Amir Al Ammari","Aymen Hussein","Ali Jasim","Ibrahim Bayesh","Alaa Abbas","Amir Al Saddah"],"players_en":["Jalal Hassan","Fahad Tariq","Ali Adnan","Saad Natiq","Rebin Sulaka","Ahmed Ibrahim","Mustafa Nadhim","Hussein Ali","Amjad Attwan","Osama Rashid","Bashar Resan","Team Photo","Mohanad Ali","Amir Al Ammari","Aymen Hussein","Ali Jasim","Ibrahim Bayesh","Alaa Abbas","Amir Al Saddah"]},
    {"code":"CHI","es":"Chile","en":"Chile","flag":"🇨🇱","color":"#d52b1e","players_es":["Brayan Cortés","Gabriel Arias","Paulo Díaz","Guillermo Maripán","Benjamín Kuscevic","Mauricio Isla","Gabriel Suazo","Arturo Vidal","Charles Aránguiz","Erick Pulgar","César Pinares","Foto del Equipo","Alexis Sánchez","Eduardo Vargas","Sebastián Driussi","Víctor Dávila","Marcos Bolados","Jean Meneses","Darío Osorio"],"players_en":["Brayan Cortés","Gabriel Arias","Paulo Díaz","Guillermo Maripán","Benjamín Kuscevic","Mauricio Isla","Gabriel Suazo","Arturo Vidal","Charles Aránguiz","Erick Pulgar","César Pinares","Team Photo","Alexis Sánchez","Eduardo Vargas","Sebastián Driussi","Víctor Dávila","Marcos Bolados","Jean Meneses","Darío Osorio"]},
    {"code":"PAN","es":"Panamá","en":"Panama","flag":"🇵🇦","color":"#db0000","players_es":["Luis Mejía","Orlando Mosquera","Harold Cummings","Eric Davis","Anibal Godoy","Fidel Escobar","Adalberto Carrasquilla","Roderick Miller","Édgar Bárcenas","Rolando Blackburn","Alberto Quintero","Foto del Equipo","Cecilio Waterman","Abdiel Ayarza","Ismael Díaz","Freddie Hall","José Fajardo","Blas Pérez","Giovanny Ramos"],"players_en":["Luis Mejía","Orlando Mosquera","Harold Cummings","Eric Davis","Anibal Godoy","Fidel Escobar","Adalberto Carrasquilla","Roderick Miller","Édgar Bárcenas","Rolando Blackburn","Alberto Quintero","Team Photo","Cecilio Waterman","Abdiel Ayarza","Ismael Díaz","Freddie Hall","José Fajardo","Blas Pérez","Giovanny Ramos"]},
    {"code":"CRC","es":"Costa Rica","en":"Costa Rica","flag":"🇨🇷","color":"#002b7f","players_es":["Keylor Navas","Esteban Alvarado","Keysher Fuller","Francisco Calvo","Juan Pablo Vargas","Bryan Oviedo","Kendall Waston","Yeltsin Tejeda","Douglas Sequeira","Celso Borges","Joel Campbell","Foto del Equipo","Brandon Aguilera","Jewison Bennette","Álvaro Zamora","Anthony Contreras","Alonso Martínez","Johan Venegas","Bryan Ruiz"],"players_en":["Keylor Navas","Esteban Alvarado","Keysher Fuller","Francisco Calvo","Juan Pablo Vargas","Bryan Oviedo","Kendall Waston","Yeltsin Tejeda","Douglas Sequeira","Celso Borges","Joel Campbell","Team Photo","Brandon Aguilera","Jewison Bennette","Álvaro Zamora","Anthony Contreras","Alonso Martínez","Johan Venegas","Bryan Ruiz"]},
    {"code":"HON","es":"Honduras","en":"Honduras","flag":"🇭🇳","color":"#0073cf","players_es":["Luis López","Edrick Menjívar","Denil Maldonado","Marcelo Pereira","Devron García","Kervin Arriaga","Maynor Figueroa","Alberth Elis","Romell Quioto","Rigoberto Rivas","Edwin Rodríguez","Foto del Equipo","Jorge Benguché","Andy Najar","Michaell Chirinos","Eddie Hernández","Alexander López","Deybi Flores","Joaquín Arias"],"players_en":["Luis López","Edrick Menjívar","Denil Maldonado","Marcelo Pereira","Devron García","Kervin Arriaga","Maynor Figueroa","Alberth Elis","Romell Quioto","Rigoberto Rivas","Edwin Rodríguez","Team Photo","Jorge Benguché","Andy Najar","Michaell Chirinos","Eddie Hernández","Alexander López","Deybi Flores","Joaquín Arias"]},
    {"code":"JAM","es":"Jamaica","en":"Jamaica","flag":"🇯🇲","color":"#ffd100","players_es":["Andre Blake","Dillon Barnes","Damion Lowe","Adrian Mariappa","Liam Moore","Greg Leigh","Javain Brown","Rolando Aarons","Daniel Johnson","Je-Vaughn Watson","Bobby Decordova-Reid","Foto del Equipo","Michail Antonio","Leon Bailey","Shamar Nicholson","Cory Burke","Oniel Fisher","Chedwyn Evans","Demarai Gray"],"players_en":["Andre Blake","Dillon Barnes","Damion Lowe","Adrian Mariappa","Liam Moore","Greg Leigh","Javain Brown","Rolando Aarons","Daniel Johnson","Je-Vaughn Watson","Bobby Decordova-Reid","Team Photo","Michail Antonio","Leon Bailey","Shamar Nicholson","Cory Burke","Oniel Fisher","Chedwyn Evans","Demarai Gray"]},
]

SPECIALS = [
    {"id":"00","es":"Logo Panini","en":"Panini Logo","rarity":"foil"},
    {"id":"FWC1","es":"Emblema Oficial","en":"Official Emblem","rarity":"foil"},
    {"id":"FWC2","es":"Emblema 2","en":"Emblem 2","rarity":"foil"},
    {"id":"FWC3","es":"Mascotas","en":"Mascots","rarity":"foil"},
    {"id":"FWC4","es":"Slogan","en":"Slogan","rarity":"foil"},
    {"id":"FWC5","es":"Balón Oficial","en":"Official Ball","rarity":"foil"},
    {"id":"FWC6","es":"Ciudades Canadá","en":"Canada Cities","rarity":"foil"},
    {"id":"FWC7","es":"Ciudades México","en":"Mexico Cities","rarity":"foil"},
    {"id":"FWC8","es":"Ciudades EUA","en":"USA Cities","rarity":"foil"},
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
            return spreadsheet.worksheet(tab_name)
        except:
            ws = spreadsheet.add_worksheet(title=tab_name, rows=1100, cols=3)
            ws.append_row(["sticker_id","owned","rarity"])
            return ws
    except Exception as e:
        st.sidebar.warning(f"Google Sheets: {e}")
        return None

def load_data(sheet):
    owned, rmap = set(), {}
    try:
        for row in sheet.get_all_records():
            sid = str(row.get("sticker_id","")).strip()
            if not sid: continue
            if str(row.get("owned","")).upper() == "TRUE":
                owned.add(sid)
            r = str(row.get("rarity","base")).lower()
            if r in RARITY_CONFIG:
                rmap[sid] = r
    except: pass
    return owned, rmap

def batch_save(sheet, owned, rmap, all_ids):
    try:
        rows = [["sticker_id","owned","rarity"]]
        for sid in all_ids:
            rows.append([sid, str(sid in owned), rmap.get(sid,"base")])
        sheet.clear()
        sheet.update("A1", rows)
    except Exception as e:
        st.warning(f"Save error: {e}")

# ── Build sticker list ─────────────────────────────────────────────────────────
def build_stickers():
    all_s = []
    for sp in SPECIALS:
        all_s.append({"id":sp["id"],"es":sp["es"],"en":sp["en"],
                       "team":"FWC","team_es":"FIFA Especial","team_en":"FIFA Special",
                       "flag":"🌍","color":"#6d28d9","rarity":sp["rarity"],"stype":"special"})
    for t in TEAMS:
        all_s.append({"id":f"{t['code']}1","es":"Escudo","en":"Badge",
                       "team":t["code"],"team_es":t["es"],"team_en":t["en"],
                       "flag":t["flag"],"color":t["color"],"rarity":"foil","stype":"badge"})
        for i,(p_es,p_en) in enumerate(zip(t["players_es"],t["players_en"])):
            num = i+2
            is_photo = "Foto" in p_es or "Photo" in p_en
            all_s.append({"id":f"{t['code']}{num}","es":p_es,"en":p_en,
                           "team":t["code"],"team_es":t["es"],"team_en":t["en"],
                           "flag":t["flag"],"color":t["color"],
                           "rarity":"foil" if is_photo else "base",
                           "stype":"team_photo" if is_photo else "player"})
    return all_s

ALL_STICKERS = build_stickers()
ALL_IDS = [s["id"] for s in ALL_STICKERS]

# ── Session state ──────────────────────────────────────────────────────────────
for k,dv in [("version","mx"),("mx_owned",set()),("mx_rarity",{}),
              ("usa_owned",set()),("usa_rarity",{}),
              ("mx_loaded",False),("usa_loaded",False),("dirty",False)]:
    if k not in st.session_state:
        st.session_state[k] = dv

ver      = st.session_state.version
lang     = "es" if ver=="mx" else "en"
tab_name = "mexico_tracker" if ver=="mx" else "usa_tracker"
sheet    = get_sheet(tab_name)

if ver=="mx" and not st.session_state.mx_loaded and sheet:
    o,r = load_data(sheet)
    st.session_state.mx_owned=o; st.session_state.mx_rarity=r; st.session_state.mx_loaded=True
elif ver=="usa" and not st.session_state.usa_loaded and sheet:
    o,r = load_data(sheet)
    st.session_state.usa_owned=o; st.session_state.usa_rarity=r; st.session_state.usa_loaded=True

owned    = st.session_state.mx_owned   if ver=="mx" else st.session_state.usa_owned
rmap     = st.session_state.mx_rarity  if ver=="mx" else st.session_state.usa_rarity
show_rar = (ver=="usa")

def get_r(sid, default): return rmap.get(sid, default)
def do_save():
    if sheet: batch_save(sheet, owned, rmap, ALL_IDS)
    st.session_state.dirty = False

# ── Version toggle ─────────────────────────────────────────────────────────────
_, mc, _ = st.columns([1,2,1])
with mc:
    c1,c2 = st.columns(2)
    with c1:
        if st.button("🇲🇽  Versión México", use_container_width=True,
                     type="primary" if ver=="mx" else "secondary"):
            if st.session_state.dirty: do_save()
            st.session_state.version="mx"; st.rerun()
    with c2:
        if st.button("🇺🇸  USA Version", use_container_width=True,
                     type="primary" if ver=="usa" else "secondary"):
            if st.session_state.dirty: do_save()
            st.session_state.version="usa"; st.rerun()
st.markdown("---")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"## ⚽ {'Álbum FIFA 2026' if lang=='es' else 'FIFA 2026 Tracker'}")
    total = len(ALL_STICKERS)
    own_n = len(owned)
    st.metric("Colección" if lang=="es" else "Collection", f"{own_n}/{total}", f"{round(own_n/total*100,1)}%")
    st.progress(own_n/total)
    if show_rar:
        c1s,c2s = st.columns(2)
        c1s.metric("🌟 Foil",   sum(1 for s in ALL_STICKERS if s["id"] in owned and get_r(s["id"],s["rarity"])=="foil"))
        c2s.metric("🟦 Blue",   sum(1 for s in ALL_STICKERS if s["id"] in owned and get_r(s["id"],s["rarity"])=="blue"))
        c1s.metric("🟣 Purple", sum(1 for s in ALL_STICKERS if s["id"] in owned and get_r(s["id"],s["rarity"])=="purple"))
        c2s.metric("🟥 Red",    sum(1 for s in ALL_STICKERS if s["id"] in owned and get_r(s["id"],s["rarity"])=="red"))
    st.markdown("---")
    search    = st.text_input("🔍 Buscar" if lang=="es" else "🔍 Search","")
    flt_owned = st.selectbox("Mostrar" if lang=="es" else "Show",
                              ["Todos","Solo tengo","Me faltan"] if lang=="es" else ["All","Owned only","Missing only"])
    all_t_names = (["Todos los equipos"] if lang=="es" else ["All teams"]) + \
                  [("FIFA Especial" if lang=="es" else "FIFA Special")] + \
                  [t["es" if lang=="es" else "en"] for t in TEAMS]
    sel_team = st.selectbox("Equipo" if lang=="es" else "Team", all_t_names)
    if show_rar:
        st.markdown("---")
        for k,rc in RARITY_CONFIG.items():
            st.markdown(f"{rc['star']} **{rc['en']}**")
    st.markdown("---")
    if st.button("💾 Guardar cambios" if lang=="es" else "💾 Save changes", use_container_width=True):
        do_save(); st.success("¡Guardado!" if lang=="es" else "Saved!")

# ── Render sticker card ────────────────────────────────────────────────────────

def make_card_html(s):
    sid      = s["id"]
    is_owned = sid in owned
    r        = get_r(sid, s["rarity"])
    rc       = RARITY_CONFIG[r]
    nm       = s["es"] if lang=="es" else s["en"]
    short    = (nm[:15] + "\u2026") if len(nm) > 15 else nm
    tc       = s["color"]
    border_c = rc["border"] if show_rar else tc
    bg_c     = rc["bg"]     if show_rar else "#1a1f2e"
    opacity  = "1.0" if is_owned else "0.3"
    gs       = "0%" if is_owned else "80%"
    img_url  = GITHUB_IMG + sid + ".jpg"
    emoji    = {"badge": "\U0001f6e1\ufe0f", "team_photo": "\U0001f465", "special": "\U0001f3c6"}.get(s["stype"], "\u26bd")
    ph_bg    = tc + "33"
    id_col   = rc["color"] if show_rar else tc
    chk      = "\u2713 " if is_owned else ""
    btn_txt  = (chk + "Tengo") if lang == "es" else (chk + "Owned")
    btn_bg   = "#16a34a33" if is_owned else "#ffffff11"
    btn_bdr  = "#16a34a" if is_owned else "#ffffff22"
    btn_col  = "#34d399" if is_owned else "#9ca3af"

    pills = ""
    if show_rar:
        parts = []
        for rk in RARITY_CONFIG:
            bg2 = RARITY_CONFIG[rk]["bg"]
            cl2 = RARITY_CONFIG[rk]["color"]
            bdr = RARITY_CONFIG[rk]["border"] if rk == r else "transparent"
            lbl = rk[0].upper()
            parts.append(
                '<span class="r-pill" style="background:' + bg2 +
                ';color:' + cl2 + ';border-color:' + bdr + ';">' + lbl + '</span>'
            )
        pills = '<div class="rarity-row">' + "".join(parts) + '</div>'

    img_tag = (
        '<img class="s-img" src="' + img_url + '" '
        'onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\';" '
        'style="display:block;"/>'
    )
    ph_tag = '<div class="s-ph" style="background:' + ph_bg + ';display:none;">' + emoji + '</div>'
    btn_tag = (
        '<div class="in-btn" style="background:' + btn_bg +
        ';border:1px solid ' + btn_bdr + ';color:' + btn_col + ';">' +
        btn_txt + '</div>'
    )

    return (
        '<div class="s-card" style="flex:1;min-width:0;border-color:' + border_c +
        ';background:' + bg_c + ';opacity:' + opacity +
        ';filter:grayscale(' + gs + ');">' +
        img_tag + ph_tag +
        '<div class="s-id" style="color:' + id_col + ';">' + sid + '</div>' +
        '<div class="s-name">' + short + '</div>' +
        pills + btn_tag +
        '</div>'
    )


# ── Main ───────────────────────────────────────────────────────────────────────
st.markdown("## " + ("\U0001f4cb Copa Mundial FIFA 2026 \u2014 Mi \u00c1lbum" if lang == "es" else "\U0001f4cb FIFA World Cup 2026 \u2014 Sticker Collection"))

SKIP = {"Todos los equipos", "All teams", "FIFA Especial", "FIFA Special"}
sections = (
    [("FIFA Especial" if lang == "es" else "FIFA Special", "FWC", "\U0001f30d", "#6d28d9")] +
    [(t["es" if lang == "es" else "en"], t["code"], t["flag"], t["color"]) for t in TEAMS]
)

COLS = 3

for sec_name, code, flag, color in sections:
    sec_s  = [s for s in ALL_STICKERS if s["team"] == code]
    show_s = []
    for s in sec_s:
        nm = s["es"] if lang == "es" else s["en"]
        if search and search.lower() not in nm.lower() and search.lower() not in sec_name.lower():
            continue
        is_owned = s["id"] in owned
        if flt_owned in ("Solo tengo", "Owned only") and not is_owned:
            continue
        if flt_owned in ("Me faltan", "Missing only") and is_owned:
            continue
        show_s.append(s)

    if sel_team not in SKIP and sec_name != sel_team:
        continue
    if not show_s:
        continue

    t_own = sum(1 for s in sec_s if s["id"] in owned)
    t_pct = round(t_own / len(sec_s) * 100)

    with st.expander(
        flag + "  **" + sec_name + "** \u2014 " + str(t_own) + "/" + str(len(sec_s)) + " (" + str(t_pct) + "%)",
        expanded=(sel_team not in SKIP)
    ):
        st.markdown(
            '<div class="prog-bg"><div class="prog-fill" style="width:' + str(t_pct) + '%;background:' + color + ';"></div></div>',
            unsafe_allow_html=True
        )

        for row_start in range(0, len(show_s), COLS):
            row = show_s[row_start:row_start + COLS]
            html_cards = "".join(make_card_html(s) for s in row)
            padded = list(row)
            while len(padded) < COLS:
                html_cards += '<div style="flex:1;min-width:0;"></div>'
                padded.append(None)

            st.markdown(
                '<div style="display:flex;gap:8px;margin-bottom:4px;">' + html_cards + '</div>',
                unsafe_allow_html=True
            )

            btn_cols = st.columns(COLS)
            for i, s in enumerate(padded):
                if s is None:
                    continue
                sid      = s["id"]
                is_owned = sid in owned
                r        = get_r(sid, s["rarity"])
                with btn_cols[i]:
                    lbl = ("\u2713 Tengo" if is_owned else "+ Tengo") if lang == "es" else ("\u2713 Owned" if is_owned else "+ Own")
                    if st.button(lbl, key=ver + "_" + sid, use_container_width=True):
                        if is_owned:
                            owned.discard(sid)
                        else:
                            owned.add(sid)
                        st.session_state.dirty = True
                        st.rerun()
                    if show_rar:
                        keys  = list(RARITY_CONFIG.keys())
                        new_r = st.selectbox(
                            "", keys, index=keys.index(r),
                            format_func=lambda x: RARITY_CONFIG[x]["star"] + " " + RARITY_CONFIG[x]["en"],
                            key="r_" + ver + "_" + sid,
                            label_visibility="collapsed"
                        )
                        if new_r != r:
                            rmap[sid] = new_r
                            st.session_state.dirty = True
                            st.rerun()
