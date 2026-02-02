import sqlite3

# 1. Raw data
raw = """
100TRILLIONUSD: https://x.com/100TRILLIONUSD
APompiliano: https://x.com/APompiliano
Ashcryptoreal: https://x.com/Ashcryptoreal
BarrySilbert: https://x.com/BarrySilbert
BeinCrypto: https://x.com/BeinCrypto
BLOCKCHAINCHICK: https://x.com/BLOCKCHAINCHICK
BitcoinMagazine: https://x.com/BitcoinMagazine
Blockworks_: https://x.com/Blockworks_
BobElliott88: https://x.com/BobElliott88
CathieDWood: https://x.com/CathieDWood
CoinDesk: https://x.com/CoinDesk
CoinMarketCap: https://x.com/CoinMarketCap
Cointelegraph: https://x.com/Cointelegraph
CryptoCobain: https://x.com/CryptoCobain
CryptoDo_app: https://x.com/CryptoDo_app
CryptoGodJohn: https://x.com/CryptoGodJohn
CryptoHawk: https://x.com/CryptoHawk
CryptoJack: https://x.com/CryptoJack
CryptoVet: https://x.com/CryptoVet
CryptoWendyO: https://x.com/CryptoWendyO
CryptoYodaY: https://x.com/CryptoYodaY
DecryptMedia: https://x.com/DecryptMedia
DefiIgnas: https://x.com/DefiIgnas
DylanLeClair_: https://x.com/DylanLeClair_
Dynamo_Patrick: https://x.com/Dynamo_Patrick
ErikVoorhees: https://x.com/ErikVoorhees
EvanLuthra: https://x.com/EvanLuthra
Goxillion: https://x.com/Goxillion
ivanOnTech: https://x.com/ivanOnTech
JAN3Gold_: https://x.com/JAN3Gold_
JavierBlas: https://x.com/JavierBlas
JihanWu: https://x.com/JihanWu
Jihoz_Axie: https://x.com/Jihoz_Axie
MartiniGuyYT: https://x.com/MartiniGuyYT
NischalShetty: https://x.com/NischalShetty
Ole_S_Hansen: https://x.com/Ole_S_Hansen
PeterSchiff: https://x.com/PeterSchiff
RaoulGMI: https://x.com/RaoulGMI
RayDalio: https://x.com/RayDalio
TO: https://x.com/TO
TheBlock__: https://x.com/TheBlock__
TheCryptoLark: https://x.com/TheCryptoLark
TheStreet: https://x.com/TheStreet
TimDraper: https://x.com/TimDraper
Unchained_pod: https://x.com/Unchained_pod
VitalikButerin: https://x.com/VitalikButerin
Vivek4real_: https://x.com/Vivek4real_
WatcherGuru: https://x.com/WatcherGuru
aantonop: https://x.com/aantonop
arjunsethi: https://x.com/arjunsethi
balajis: https://x.com/balajis
brian_armstrong: https://x.com/brian_armstrong
cameron: https://x.com/cameron
cdixon: https://x.com/cdixon
chrisleao: https://x.com/chrisleao
cryptoheem: https://x.com/cryptoheem
cryptomaran: https://x.com/cryptomaran
cz_binance: https://x.com/cz_binance
dahongfei: https://x.com/dahongfei
dannield: https://x.com/dannield
jack: https://x.com/jack
jeffpulver: https://x.com/jeffpulver
justinsuntron: https://x.com/justinsuntron
kamiotv: https://x.com/kamiotv
laurashin: https://x.com/laurashin
lopp: https://x.com/lopp
maxkeiser: https://x.com/maxkeiser
ninjadao: https://x.com/ninjadao
paulg: https://x.com/paulg
pmarca: https://x.com/pmarca
rogerkver: https://x.com/rogerkver
saylor: https://x.com/saylor
scottmelker: https://x.com/scottmelker
sumitgupta_: https://x.com/sumitgupta_
tyler: https://x.com/tyler
wacy_time1: https://x.com/wacy_time1
whale_alert: https://x.com/whale_alert
woonomic: https://x.com/woonomic
yozawa_ts: https://x.com/yozawa_ts
yutamisaki: https://x.com/yutamisaki
zerohedge: https://x.com/zerohedge
zhusu: https://x.com/zhusu
"""

# 2. Extract usernames
usernames = []
for line in raw.splitlines():
    line = line.strip()
    if not line or ':' not in line:
        continue
    username = line.split(':', 1)[0].strip()
    usernames.append(username)

# 3. Persist to SQLite
conn = sqlite3.connect('TaoWar-X.db')
cursor = conn.cursor()

# Create table if not exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS influencers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Insert each username (ignore duplicates)
for u in usernames:
    cursor.execute(
        'INSERT OR IGNORE INTO influencers (username) VALUES (?)',
        (u,)
    )

conn.commit()
conn.close()

print(f"Imported {len(usernames)} usernames into influencers.db")
