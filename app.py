import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import requests
from PIL import Image
from io import BytesIO
import json
import time

st.set_page_config(
    page_title="FIFA 2026 Sticker Tracker",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Styling ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.sticker-card {
    border-radius: 10px;
    padding: 8px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    margin: 4px;
    min-height: 130px;
}
.rarity-base  { border: 2px solid #cbd5e1; background: #f8fafc; }
.rarity-blue  { border: 2px solid #3b82f6; background: #eff6ff; }
.rarity-purple{ border: 2px solid #a855f7; background: #faf5ff; }
.rarity-red   { border: 2px solid #ef4444; background: #fff1f2; }
.rarity-foil  { border: 2px solid #f59e0b; background: #fffbeb; }
.owned-card   { opacity: 1.0; }
.missing-card { opacity: 0.4; }
.sticker-id   { font-size: 11px; font-weight: 600; color: #64748b; }
.sticker-name { font-size: 10px; color: #94a3b8; margin-top: 2px; }
.progress-text{ font-size: 13px; color: #64748b; }
div[data-testid="stHorizontalBlock"] { gap: 6px !important; }
</style>
""", unsafe_allow_html=True)

# ── Rarity config ─────────────────────────────────────────────────────────────
RARITY_COLORS = {
    "base":   {"star": "⬜", "label": "Base",   "color": "#94a3b8"},
    "blue":   {"star": "🟦", "label": "Blue",   "color": "#3b82f6"},
    "purple": {"star": "🟣", "label": "Purple", "color": "#a855f7"},
    "red":    {"star": "🟥", "label": "Red",    "color": "#ef4444"},
    "foil":   {"star": "🌟", "label": "Foil",   "color": "#f59e0b"},
}

# ── Full checklist ────────────────────────────────────────────────────────────
TEAMS = [
    {"code": "MEX", "name": "Mexico",        "flag": "🇲🇽", "players": ["Luis Malagón","Johan Vasquez","Jorge Sánchez","Cesar Montes","Jesus Gallardo","Israel Reyes","Diego Lainez","Carlos Rodriguez","Edson Alvarez","Orbelin Pineda","Marcel Ruiz","Team Photo","Érick Sánchez","Hirving Lozano","Santiago Giménez","Raúl Jiménez","Alexis Vega","Roberto Alvarado","Cesar Huerta"]},
    {"code": "USA", "name": "USA",            "flag": "🇺🇸", "players": ["Matt Freese","Chris Richards","Tim Ream","Mark McKenzie","Alex Freeman","Antonee Robinson","Tyler Adams","Tanner Tessmann","Weston McKennie","Christian Roldan","Timothy Weah","Team Photo","Diego Luna","Malik Tillman","Christian Pulisic","Brenden Aaronson","Ricardo Pepi","Haji Wright","Folarin Balogun"]},
    {"code": "CAN", "name": "Canada",         "flag": "🇨🇦", "players": ["Dayne St.Clair","Alphonso Davies","Alistair Johnston","Samuel Adekugbe","Riche Larvea","Derek Cornelius","Moïse Bombito","Kamal Miller","Stephen Eustáquio","Ismaël Koné","Jonathan Osorio","Team Photo","Jacob Shaffelburg","Mathieu Choinière","Niko Sigur","Tajon Buchanan","Liam Millar","Cyle Larin","Jonathan David"]},
    {"code": "BRA", "name": "Brazil",         "flag": "🇧🇷", "players": ["Alisson","Bento","Marquinhos","Éder Militão","Gabriel Magalhães","Danilo","Wesley","Lucas Paquetá","Casemiro","Bruno Guimarães","Luiz Henrique","Team Photo","Vinicius Júnior","Rodrygo","João Pedro","Matheus Cunha","Gabriel Martinelli","Raphinha","Estévão"]},
    {"code": "ARG", "name": "Argentina",      "flag": "🇦🇷", "players": ["Franco Armani","Emiliano Martínez","Nahuel Molina","Cristian Romero","Lisandro Martínez","Nicolás Otamendi","Marcos Acuña","Rodrigo De Paul","Leandro Paredes","Giovani Lo Celso","Ángel Di María","Team Photo","Alexis Mac Allister","Nicolás González","Lautaro Martínez","Julián Álvarez","Paulo Dybala","Thiago Almada","Valentin Carboni"]},
    {"code": "ENG", "name": "England",        "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "players": ["Jordan Pickford","Dean Henderson","Reece James","John Stones","Harry Maguire","Luke Shaw","Kieran Trippier","Declan Rice","Jude Bellingham","Phil Foden","Bukayo Saka","Team Photo","Morgan Rogers","Marcus Rashford","Harry Kane","Ollie Watkins","Cole Palmer","Anthony Gordon","Jarrod Bowen"]},
    {"code": "GER", "name": "Germany",        "flag": "🇩🇪", "players": ["Manuel Neuer","Marc ter Stegen","Jonathan Tah","Nico Schlotterbeck","David Raum","Max Mittelstädt","Robert Andrich","Joshua Kimmich","Florian Wirtz","Ilkay Gündogan","Leon Goretzka","Team Photo","Leroy Sané","Jamal Musiala","Thomas Müller","Serge Gnabry","Kai Havertz","Niclas Füllkrug","Deniz Undav"]},
    {"code": "FRA", "name": "France",         "flag": "🇫🇷", "players": ["Mike Maignan","Alphonse Areola","Jules Koundé","Dayot Upamecano","William Saliba","Theo Hernandez","Lucas Hernandez","Aurélien Tchouaméni","Eduardo Camavinga","Mattéo Guendouzi","Adrien Rabiot","Team Photo","Antoine Griezmann","Ousmane Dembélé","Kylian Mbappé","Marcus Thuram","Randal Kolo Muani","Jonathan Clauss","Bradley Barcola"]},
    {"code": "ESP", "name": "Spain",          "flag": "🇪🇸", "players": ["Unai Simón","David Raya","Dani Carvajal","Aymeric Laporte","Robin Le Normand","Alejandro Grimaldo","Jesús Navas","Rodri","Pedri","Fabián Ruiz","Dani Olmo","Team Photo","Ferrán Torres","Nico Williams","Álvaro Morata","Joselu","Mikel Oyarzabal","Lamine Yamal","Yeremy Pino"]},
    {"code": "POR", "name": "Portugal",       "flag": "🇵🇹", "players": ["Rui Patrício","Diogo Costa","João Cancelo","Rúben Dias","Pepe","Nuno Mendes","Danilo Pereira","Bruno Fernandes","Bernardo Silva","João Palhinha","Vitinha","Team Photo","Rafael Leão","Diogo Jota","Cristiano Ronaldo","Gonçalo Ramos","Pedro Neto","João Félix","Francisco Conceição"]},
    {"code": "NED", "name": "Netherlands",    "flag": "🇳🇱", "players": ["Bart Verbruggen","Mark Flekken","Denzel Dumfries","Virgil van Dijk","Stefan de Vrij","Nathan Aké","Tyrell Malacia","Ryan Gravenberch","Tijjani Reijnders","Teun Koopmeiners","Davy Klaassen","Team Photo","Steven Bergwijn","Cody Gakpo","Memphis Depay","Wout Weghorst","Donyell Malen","Xavi Simons","Brian Brobbey"]},
    {"code": "ITA", "name": "Italy",          "flag": "🇮🇹", "players": ["Gianluigi Donnarumma","Alex Meret","Giovanni Di Lorenzo","Alessandro Bastoni","Federico Gatti","Federico Dimarco","Davide Frattesi","Sandro Tonali","Nicolò Barella","Lorenzo Pellegrini","Nicolò Fagioli","Team Photo","Federico Chiesa","Matteo Politano","Gianluca Scamacca","Lorenzo Lucca","Giacomo Raspadori","Mateo Retegui","Wilfried Gnonto"]},
    {"code": "SCO", "name": "Scotland",       "flag": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "players": ["Angus Gunn","Jack Hendry","Kieran Tierney","Aaron Hickey","Andrew Robertson","Scott McKenna","John Souttar","Anthony Ralston","Grant Hanley","Scott McTominay","Billy Gilmour","Team Photo","Lewis Ferguson","Ryan Christie","Kenny McLean","John McGinn","Lyndon Dykes","Che Adams","Ben Doak"]},
    {"code": "CZE", "name": "Czechia",        "flag": "🇨🇿", "players": ["Matej Kovar","Jindrich Stanek","Ladislav Krejci","Vladimir Coufal","Jaroslav Zeleny","Tomas Holes","David Zima","Michal Sadilek","Lukas Provod","Lukas Cerv","Tomas Soucek","Team Photo","Pavel Sulc","Matej Vydra","Vasil Kusej","Tomas Chory","Vaclav Cerny","Adam Hlozek","Patrik Schick"]},
    {"code": "NOR", "name": "Norway",         "flag": "🇳🇴", "players": ["Orjan Nyland","Mats Selnaes","Kristoffer Ajer","Leo Ostigard","Andreas Hanche-Olsen","Birger Meling","Vegar Hedenstad","Mathias Normann","Patrick Berg","Fredrik Aursnes","Sander Berge","Team Photo","Martin Odegaard","Antonio Nusa","Mohamed Elyounoussi","Erling Haaland","Alexander Sorloth","Ola Solbakken","Jens Petter Hauge"]},
    {"code": "SWE", "name": "Sweden",         "flag": "🇸🇪", "players": ["Robin Olsen","Isak Pettersson","Carl Starfelt","Victor Lindelöf","Isak Hien","Marcus Danielson","Emil Krafth","Jens Cajuste","Viktor Claesson","Hugo Larsson","Viktor Johansson","Team Photo","Dejan Kulusevski","Alexander Isak","Robin Quaison","Jordan Larsson","Kristoffer Zachrisson","Emil Forsberg","Pontus Almqvist"]},
    {"code": "AUS", "name": "Australia",      "flag": "🇦🇺", "players": ["Mathew Ryan","Joe Gauci","Harry Souttar","Alessandro Circati","Jordan Bos","Aziz Behich","Cameron Burgess","Lewis Miller","Milos Degenek","Jackson Irvine","Riley McGree","Team Photo","Aiden O'Neill","Connor Metcalfe","Patrick Yazbek","Craig Goodwin","Kusini Yengi","Nestory Irankunda","Mohamed Touré"]},
    {"code": "RSA", "name": "South Africa",   "flag": "🇿🇦", "players": ["Ronwen Williams","Sipho Chaine","Aubrey Modiba","Samukele Kabini","Mbekezeli Mbokazi","Khulumani Ndamane","Siyabonga Ngezana","Khuliso Mudau","Nkosinathi Sibisi","Teboho Mokoena","Thalente Mbatha","Team Photo","Bathasi Aubaas","Yaya Sithole","Sipho Mbule","Lyle Foster","Iqraam Rayners","Mohau Nkota","Oswin Appollis"]},
    {"code": "KOR", "name": "South Korea",    "flag": "🇰🇷", "players": ["Hyeon-woo Jo","Seung-Gyu Kim","Min-jae Kim","Yu-min Cho","Young-woo Seol","Han-beom Lee","Tae-seok Lee","Myung-jae Lee","Jae-sung Lee","In-beom Hwang","Kang-in Lee","Team Photo","Seung-ho Paik","Jens Castrop","Dong-yeong Lee","Gue-sung Cho","Heung-min Son","Hee-chan Hwang","Hyeon-Gyu Oh"]},
    {"code": "JPN", "name": "Japan",          "flag": "🇯🇵", "players": ["Shuichi Gonda","Daniel Schmidt","Takehiro Tomiyasu","Ko Itakura","Shogo Taniguchi","Yuto Nagatomo","Hiroki Ito","Wataru Endo","Ao Tanaka","Hidemasa Morita","Junya Ito","Team Photo","Takumi Minamino","Kaoru Mitoma","Ritsu Doan","Ayase Ueda","Yukinari Sugawara","Daichi Kamada","Keito Nakamura"]},
    {"code": "EGY", "name": "Egypt",          "flag": "🇪🇬", "players": ["Mohamed Abou Gabal","Mohamed El-Shenawy","Ahmed Hegazy","Omar Kamal","Mohamed Abdelmonem","Akram Tawfik","Mahmoud El Wensh","Amr El Sulaya","Mohamed Elneny","Taher Mohamed Taher","Mohamed Hamdy","Team Photo","Emam Ashour","Zizo","Omar Marmoush","Mostafa Mohamed","Hussein El Shahat","Marwan Attia","Trezeguet"]},
    {"code": "IRN", "name": "Iran",           "flag": "🇮🇷", "players": ["Alireza Beiranvand","Amir Abedzadeh","Shoja Khalilzadeh","Majid Hosseini","Hossein Kanaanizadegan","Milad Mohammadi","Roozbeh Cheshmi","Saeid Ezatolahi","Ali Karimi","Mehdi Torabi","Ahmad Noorollahi","Team Photo","Sardar Azmoun","Saman Ghoddos","Karim Ansarifard","Mehdi Taremi","Ali Gholizadeh","Allahyar Sayyadmanesh","Omid Noorafkan"]},
    {"code": "IRQ", "name": "Iraq",           "flag": "🇮🇶", "players": ["Jalal Hassan","Fahad Tariq","Ali Adnan","Saad Natiq","Rebin Sulaka","Ahmed Ibrahim","Mustafa Nadhim","Hussein Ali","Amjad Attwan","Osama Rashid","Bashar Resan","Team Photo","Mohanad Ali","Amir Al Ammari","Aymen Hussein","Ali Jasim","Ibrahim Bayesh","Alaa Abbas","Amir Al Saddah"]},
    {"code": "QAT", "name": "Qatar",          "flag": "🇶🇦", "players": ["Meshaal Barsham","Sultan Albrake","Lucas Mendes","Homam Ahmed","Boualem Khoukhi","Pedro Miguel","Tarek Salman","Mohamed Al-Mannai","Karim Boudiaf","Assim Madibo","Ahmed Fatehi","Team Photo","Mohammed Waad","Abdulaziz Hatem","Hassan Al-Haydos","Edmilson Junior","Akram Afif","Ahmed Al Ganehi","Almoez Ali"]},
    {"code": "SUI", "name": "Switzerland",   "flag": "🇨🇭", "players": ["Gregor Kobel","Yvon Mvogo","Manuel Akanji","Ricardo Rodriguez","Nico Elvedi","Aurèle Amenda","Silvan Widmer","Granit Xhaka","Denis Zakaria","Remo Freuler","Fabian Rieder","Team Photo","Ardon Jashari","Johan Manzambi","Michel Aebischer","Breel Embolo","Ruben Vargas","Dan Ndoye","Zeki Amdouni"]},
    {"code": "MAR", "name": "Morocco",        "flag": "🇲🇦", "players": ["Yassine Bounou","Munir El Kajoui","Achraf Hakimi","Noussair Mazraoui","Nayef Aguerd","Roman Saiss","Jawad El Yamiq","Adam Masina","Sofyan Amrabat","Azzedine Ounahi","Eliesse Ben Seghir","Team Photo","Bilal El Khannouss","Ismael Saibari","Youssef En-Nesyri","Abde Ezzalzouli","Soufiane Rahimi","Brahim Diaz","Ayoub El Kaabi"]},
    {"code": "HAI", "name": "Haiti",          "flag": "🇭🇹", "players": ["Johny Placide","Carlens Arcus","Martin Expérience","Jean-Kevin Duverne","Ricardo Adé","Duke Lacroix","Garven Metusala","Hannes Delcroix","Leverton Pierre","Danley Jean Jacques","Jean-Ricner Bellegarde","Team Photo","Christopher Attys","Derrick Etienne Jr","Josue Casimir","Ruben Providence","Duckens Nazon","Louicius Deedson","Frantzdy Pierrot"]},
    {"code": "PAR", "name": "Paraguay",       "flag": "🇵🇾", "players": ["Roberto Fernandez","Orlando Gill","Gustavo Gomez","Fabián Balbuena","Juan José Cáceres","Omar Alderete","Junior Alonso","Mathías Villasanti","Diego Gomez","Damián Bobadilla","Andres Cubas","Team Photo","Matias Galarza","Julio Enciso","Alejandro Romero","Miguel Almirón","Ramon Sosa","Angel Romero","Antonio Sanabria"]},
    {"code": "URU", "name": "Uruguay",        "flag": "🇺🇾", "players": ["Fernando Muslera","Sergio Rochet","Ronald Araújo","José María Giménez","Mathías Olivera","Nahitan Nández","Lucas Torreira","Federico Valverde","Rodrigo Bentancur","Giorgian De Arrascaeta","Facundo Pellistri","Team Photo","Darwin Núñez","Luis Suárez","Edinson Cavani","Maxi Gómez","Brian Rodríguez","Agustín Canobbio","Ignacio De La Cruz"]},
    {"code": "GHA", "name": "Ghana",          "flag": "🇬🇭", "players": ["Lawrence Ati-Zigi","Jojo Wollacott","Andy Yiadom","Alexander Djiku","Daniel Amartey","Alidu Seidu","Baba Rahman","Thomas Partey","Salis Abdul Samed","Mohammed Kudus","Emmanuel Gyasi","Team Photo","Antoine Semenyo","Jordan Ayew","Andre Ayew","Felix Afena-Gyan","Gideon Mensah","Kamaldeen Sulemana","Inaki Williams"]},
    {"code": "SEN", "name": "Senegal",        "flag": "🇸🇳", "players": ["Edouard Mendy","Seny Dieng","Kalidou Koulibaly","Abdou Diallo","Ismail Jakobs","Formose Mendy","Pape Abou Cissé","Lamine Camara","Idrissa Gana Gueye","Nampalys Mendy","Krepin Diatta","Team Photo","Iliman Ndiaye","Boulaye Dia","Sadio Mané","Nicolas Jackson","Ismaila Sarr","Habib Diallo","Yehvann Diouf"]},
    {"code": "CMR", "name": "Cameroon",       "flag": "🇨🇲", "players": ["André Onana","Fabrice Ondoa","Harold Moukoudi","Jean-Charles Castelletto","Collins Fai","Ambroise Oyongo","Nicolas Nkoulou","Samuel Oum Gouet","Frank Zambo Anguissa","Pierre Kunde","Martin Hongla","Team Photo","Bryan Mbeumo","Karl Toko Ekambi","Vincent Aboubakar","Eric Choupo-Moting","Stéphane Bahoken","Georges-Kevin N'Koudou","Ignatius Ganago"]},
    {"code": "NGA", "name": "Nigeria",        "flag": "🇳🇬", "players": ["Francis Uzoho","Stanley Nwabali","Semi Ajayi","William Troost-Ekong","Zaidu Sanusi","Bright Osayi-Samuel","Ola Aina","Frank Onyeka","Alex Iwobi","Wilfred Ndidi","Kelechi Iheanacho","Team Photo","Samuel Chukwueze","Ademola Lookman","Moses Simon","Victor Osimhen","Terem Moffi","Taiwo Awoniyi","Cyriel Dessers"]},
    {"code": "COL", "name": "Colombia",       "flag": "🇨🇴", "players": ["David Ospina","Camilo Vargas","Davinson Sánchez","Yerry Mina","Daniel Muñoz","Johan Mojica","Lerma","Wilmar Barrios","Mateus Uribe","Luis Díaz","James Rodríguez","Team Photo","Rafael Santos Borré","Cucho Hernández","Falcao","Jhon Córdoba","Miguel Borja","Jhon Durán","Jhon Arias"]},
    {"code": "ECU", "name": "Ecuador",        "flag": "🇪🇨", "players": ["Hernán Galíndez","Alexander Domínguez","Ángelo Preciado","Piero Hincapié","Jackson Porozo","Pervis Estupiñán","Diego Palacios","Carlos Gruezo","Jhegson Méndez","Moisés Caicedo","Jeremy Sarmiento","Team Photo","Gonzalo Plata","Michael Estrada","Romario Ibarra","Enner Valencia","Ángel Mena","Jordy Caicedo","Leonardo Campana"]},
    {"code": "TUR", "name": "Türkiye",        "flag": "🇹🇷", "players": ["Ugurcan Cakir","Mert Gunok","Çaglar Söyüncü","Merih Demiral","Samet Akaydin","Ferdi Kadioglu","Zeki Celik","Hakan Calhanoglu","Kaan Ayhan","Orkun Kökcü","Kenan Yildiz","Team Photo","Arda Güler","Yunus Akgun","Baris Alper Yilmaz","Efecan Karaca","Cenk Tosun","Umut Bozok","Serdar Dursun"]},
    {"code": "AUT", "name": "Austria",        "flag": "🇦🇹", "players": ["Patrick Pentz","Heinz Lindner","Stefan Posch","David Alaba","Gernot Trauner","Philipp Mwene","Maximilian Wöber","Nicolas Seiwald","Konrad Laimer","Marcel Sabitzer","Xaver Schlager","Team Photo","Florian Kainz","Patrick Wimmer","Marko Arnautovic","Michael Gregoritsch","Christoph Baumgartner","Louis Schaub","Romano Schmid"]},
    {"code": "BIH", "name": "Bosnia & Herz.", "flag": "🇧🇦", "players": ["Nikola Vasilj","Amer Dedic","Sead Kolasinac","Tarik Muharemovic","Nihad Mujakic","Nikola Katic","Amir Hadziahmetovic","Benjamin Tahirovic","Armin Gigovic","Ivan Sunjic","Ivan Basic","Team Photo","Dzenis Burnic","Esmir Bajraktarevic","Amar Memic","Ermedin Demirovic","Edin Dzeko","Samed Bazdar","Haris Tabakovic"]},
    {"code": "UZB", "name": "Uzbekistan",     "flag": "🇺🇿", "players": ["Utkir Yusupov","Sherzod Nishonov","Sherzod Qoraboyev","Khurshid Tursunov","Akbar Bobojonov","Timur Jorayev","Oston Urunov","Jaloliddin Masharipov","Odil Akhmedov","Farrukh Tashkentov","Jamshid Iskanderov","Team Photo","Eldor Shomurodov","Abbosbek Fayzullaev","Sherzod Nasrullaev","Bobur Abdixoliqov","Otabek Shukurov","Dostonbek Xolmatov","Khojiakbar Alijonov"]},
    {"code": "CIV", "name": "Côte d'Ivoire", "flag": "🇨🇮", "players": ["Yahia Fofana","Badra Sangaré","Simon Deli","Willy Boly","Serge Aurier","Ghislain Konan","Wilfried Kanon","Ibrahim Sangaré","Jean-Michaël Seri","Franck Kessie","Sekou Sanogo","Team Photo","Nicolas Pépé","Jonathan Bamba","Wilfried Zaha","Sébastien Haller","Simon Adingra","Oumar Diakité","Odilon Kossounou"]},
]

SPECIAL_STICKERS = [
    {"id": "00",   "name": "Panini Logo",      "rarity": "foil"},
    {"id": "FWC1", "name": "Official Emblem",  "rarity": "foil"},
    {"id": "FWC2", "name": "Official Emblem 2","rarity": "foil"},
    {"id": "FWC3", "name": "Mascots",          "rarity": "foil"},
    {"id": "FWC4", "name": "Official Slogan",  "rarity": "foil"},
    {"id": "FWC5", "name": "Official Ball",    "rarity": "foil"},
    {"id": "FWC6", "name": "Canada Cities",    "rarity": "foil"},
    {"id": "FWC7", "name": "Mexico Cities",    "rarity": "foil"},
    {"id": "FWC8", "name": "USA Cities",       "rarity": "foil"},
]

# ── Google Sheets ─────────────────────────────────────────────────────────────
@st.cache_resource
def get_sheet():
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open("fifa2026_tracker").sheet1
        return sheet
    except Exception as e:
        st.error(f"Google Sheets connection failed: {e}")
        return None

def load_data(sheet):
    """Load owned + rarity data from sheet into dicts."""
    owned = set()
    rarity_map = {}
    try:
        rows = sheet.get_all_records()
        for row in rows:
            sid = str(row.get("sticker_id", "")).strip()
            if not sid:
                continue
            if str(row.get("owned", "")).strip().upper() == "TRUE":
                owned.add(sid)
            r = str(row.get("rarity", "base")).strip().lower()
            if r in RARITY_COLORS:
                rarity_map[sid] = r
    except Exception as e:
        st.warning(f"Could not load data: {e}")
    return owned, rarity_map

def save_sticker(sheet, sticker_id, owned: bool, rarity: str):
    """Upsert a single sticker row."""
    try:
        cell = sheet.find(sticker_id, in_column=1)
        if cell:
            sheet.update(f"A{cell.row}:C{cell.row}", [[sticker_id, str(owned), rarity]])
        else:
            sheet.append_row([sticker_id, str(owned), rarity])
    except Exception as e:
        st.warning(f"Save failed: {e}")

def ensure_header(sheet):
    try:
        header = sheet.row_values(1)
        if not header or header[0] != "sticker_id":
            sheet.insert_row(["sticker_id", "owned", "rarity"], 1)
    except:
        pass

# ── Wikipedia photo fetch ─────────────────────────────────────────────────────
@st.cache_data(ttl=86400)
def get_wiki_photo(player_name: str):
    """Try to fetch a Wikipedia thumbnail for the player."""
    try:
        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query", "format": "json", "prop": "pageimages",
            "titles": player_name, "pithumbsize": 200, "pilimit": 1,
        }
        resp = requests.get(search_url, params=params, timeout=5)
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            thumb = page.get("thumbnail", {}).get("source")
            if thumb:
                return thumb
    except:
        pass
    return None

# ── Build full sticker list ───────────────────────────────────────────────────
def build_all_stickers():
    all_s = []
    for s in SPECIAL_STICKERS:
        all_s.append({"id": s["id"], "name": s["name"], "team": "FWC",
                       "team_name": "FIFA Special", "default_rarity": s["rarity"]})
    for t in TEAMS:
        all_s.append({"id": f"{t['code']}1", "name": "Team Logo",
                       "team": t["code"], "team_name": t["name"], "default_rarity": "foil"})
        for i, p in enumerate(t["players"]):
            num = i + 2
            dr = "foil" if p == "Team Photo" else "base"
            all_s.append({"id": f"{t['code']}{num}", "name": p,
                           "team": t["code"], "team_name": t["name"], "default_rarity": dr})
    return all_s

ALL_STICKERS = build_all_stickers()

# ── Session state init ────────────────────────────────────────────────────────
if "owned" not in st.session_state:
    st.session_state.owned = set()
if "rarity_map" not in st.session_state:
    st.session_state.rarity_map = {}
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False
if "selected_sticker" not in st.session_state:
    st.session_state.selected_sticker = None

# ── Load data once ────────────────────────────────────────────────────────────
sheet = get_sheet()
if sheet and not st.session_state.data_loaded:
    ensure_header(sheet)
    owned, rarity_map = load_data(sheet)
    st.session_state.owned = owned
    st.session_state.rarity_map = rarity_map
    st.session_state.data_loaded = True

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚽ FIFA 2026 Tracker")
    st.markdown("---")

    total = len(ALL_STICKERS)
    owned_count = len(st.session_state.owned)
    pct = round(owned_count / total * 100, 1)
    st.metric("Collection", f"{owned_count} / {total}", f"{pct}%")

    foil_count   = sum(1 for s in ALL_STICKERS if s["id"] in st.session_state.owned and st.session_state.rarity_map.get(s["id"], s["default_rarity"]) == "foil")
    blue_count   = sum(1 for s in ALL_STICKERS if s["id"] in st.session_state.owned and st.session_state.rarity_map.get(s["id"], s["default_rarity"]) == "blue")
    purple_count = sum(1 for s in ALL_STICKERS if s["id"] in st.session_state.owned and st.session_state.rarity_map.get(s["id"], s["default_rarity"]) == "purple")
    red_count    = sum(1 for s in ALL_STICKERS if s["id"] in st.session_state.owned and st.session_state.rarity_map.get(s["id"], s["default_rarity"]) == "red")

    col1, col2 = st.columns(2)
    col1.metric("🌟 Foil",   foil_count)
    col2.metric("🟦 Blue",   blue_count)
    col1.metric("🟣 Purple", purple_count)
    col2.metric("🟥 Red",    red_count)

    st.markdown("---")
    st.markdown("**Filters**")
    search = st.text_input("Search player / team", "")
    filter_owned = st.selectbox("Show", ["All", "Owned only", "Missing only"])
    filter_rarity = st.selectbox("Rarity", ["All"] + [v["label"] for v in RARITY_COLORS.values()])
    selected_team = st.selectbox("Team", ["All teams"] + [t["name"] for t in TEAMS])

    st.markdown("---")
    st.markdown("**Legend**")
    for k, v in RARITY_COLORS.items():
        st.markdown(f"{v['star']} **{v['label']}**")

# ── Sticker detail panel ──────────────────────────────────────────────────────
def show_sticker_detail(s):
    rarity = st.session_state.rarity_map.get(s["id"], s["default_rarity"])
    rc = RARITY_COLORS[rarity]
    is_owned = s["id"] in st.session_state.owned

    st.markdown(f"### {rc['star']} {s['id']} — {s['name']}")
    st.markdown(f"**Team:** {s['team_name']}  |  **Rarity:** {rc['label']}")

    # Photo
    if s["name"] not in ("Team Logo", "Team Photo") and not s["id"].startswith("FWC"):
        with st.spinner("Loading photo..."):
            photo_url = get_wiki_photo(s["name"])
        if photo_url:
            try:
                resp = requests.get(photo_url, timeout=5)
                img = Image.open(BytesIO(resp.content))
                st.image(img, width=160, caption=s["name"])
            except:
                st.info("Photo not available")
        else:
            st.info("No Wikipedia photo found for this player")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if is_owned:
            if st.button("❌ Mark as Missing", use_container_width=True):
                st.session_state.owned.discard(s["id"])
                if sheet:
                    save_sticker(sheet, s["id"], False, rarity)
                st.session_state.selected_sticker = None
                st.rerun()
        else:
            if st.button("✅ Mark as Owned", use_container_width=True):
                st.session_state.owned.add(s["id"])
                if sheet:
                    save_sticker(sheet, s["id"], True, rarity)
                st.session_state.selected_sticker = None
                st.rerun()

    with col2:
        new_rarity = st.selectbox("Set rarity", list(RARITY_COLORS.keys()),
                                   index=list(RARITY_COLORS.keys()).index(rarity),
                                   format_func=lambda x: f"{RARITY_COLORS[x]['star']} {RARITY_COLORS[x]['label']}")
        if new_rarity != rarity:
            st.session_state.rarity_map[s["id"]] = new_rarity
            if sheet:
                save_sticker(sheet, s["id"], is_owned, new_rarity)
            st.rerun()

    if st.button("← Back to collection", use_container_width=True):
        st.session_state.selected_sticker = None
        st.rerun()

# ── Main view ─────────────────────────────────────────────────────────────────
if st.session_state.selected_sticker:
    sid = st.session_state.selected_sticker
    match = next((s for s in ALL_STICKERS if s["id"] == sid), None)
    if match:
        show_sticker_detail(match)
    else:
        st.session_state.selected_sticker = None
        st.rerun()
else:
    st.markdown("## 📋 FIFA World Cup 2026 — Sticker Collection")

    # Filter stickers
    filtered = []
    for s in ALL_STICKERS:
        r = st.session_state.rarity_map.get(s["id"], s["default_rarity"])
        is_owned = s["id"] in st.session_state.owned

        if search and search.lower() not in s["name"].lower() and search.lower() not in s["team_name"].lower():
            continue
        if filter_owned == "Owned only" and not is_owned:
            continue
        if filter_owned == "Missing only" and is_owned:
            continue
        if filter_rarity != "All" and RARITY_COLORS[r]["label"] != filter_rarity:
            continue
        if selected_team != "All teams" and s["team_name"] != selected_team:
            continue
        filtered.append(s)

    # Group by team
    teams_shown = {}
    for s in filtered:
        teams_shown.setdefault(s["team"], []).append(s)

    if not teams_shown:
        st.info("No stickers match your filters.")
    else:
        for team_code, stickers in teams_shown.items():
            team_info = next((t for t in TEAMS if t["code"] == team_code), None)
            team_name = team_info["name"] if team_info else "FIFA Special"
            team_flag = team_info["flag"] if team_info else "🌍"

            team_owned = sum(1 for s in stickers if s["id"] in st.session_state.owned)
            team_total = len(stickers)
            pct = round(team_owned / team_total * 100)

            with st.expander(f"{team_flag} **{team_name}** — {team_owned}/{team_total} ({pct}%)", expanded=(selected_team != "All teams")):
                st.progress(pct / 100)
                cols = st.columns(5)
                for i, s in enumerate(stickers):
                    r = st.session_state.rarity_map.get(s["id"], s["default_rarity"])
                    rc = RARITY_COLORS[r]
                    is_owned = s["id"] in st.session_state.owned
                    opacity_class = "owned-card" if is_owned else "missing-card"
                    border_class = f"rarity-{r}"
                    short_name = s["name"][:14] + "…" if len(s["name"]) > 14 else s["name"]

                    with cols[i % 5]:
                        st.markdown(f"""
                        <div class="sticker-card {border_class} {opacity_class}">
                            <div style="font-size:16px;">{rc['star']}</div>
                            <div class="sticker-id">{s['id']}</div>
                            <div class="sticker-name">{short_name}</div>
                            {'<div style="font-size:10px;color:#16a34a;font-weight:600;">✓ owned</div>' if is_owned else ''}
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("Open", key=f"btn_{s['id']}", use_container_width=True):
                            st.session_state.selected_sticker = s["id"]
                            st.rerun()
