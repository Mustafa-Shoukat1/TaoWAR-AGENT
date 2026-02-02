import sqlite3

# 1. Raw category data
raw_categories = """
•   DeFi (Decentralized Finance): Posts about decentralized finance protocols, yield farming, staking, or DeFi projects.
•   Crypto Market Trends: General market updates, price movements, or predictions for cryptocurrencies like Bitcoin, Ethereum, etc.
•   Commodities: Posts discussing traditional commodities (e.g., gold, oil) in relation to crypto or finance, often from influencers like PeterSchiff or Ole_S_Hansen.
•   Blockchain Technology: Technical updates or discussions about blockchain development, scaling solutions, or new protocols.
•   Regulation & Policy: News or opinions on crypto regulations, government policies, or legal developments.
•   NFTs (Non-Fungible Tokens): Posts about NFT projects, marketplaces, or trends.
•   Macro Economics: Broader economic trends, inflation, interest rates, or global financial markets, often from influencers like RayDalio or RaoulGMI.
•   Crypto Adoption: News or opinions on mainstream adoption of crypto, such as companies accepting Bitcoin or new payment systems.
•   Security & Scams: Warnings about hacks, scams, or security practices in the crypto space.
•   Trading & Investment Strategies: Tips, strategies, or insights on trading or investing in crypto or financial markets.
•   Web3 & Metaverse: For posts about Web3 projects, the metaverse, or decentralized internet.
•   Stablecoins: Discussions about stablecoins like USDT, USDC, or new developments in the space.
•   Crypto Gaming: Posts about play-to-earn games, blockchain gaming, or related tokens.
"""

# 2. Parse out (name, description) pairs
categories = []
for line in raw_categories.splitlines():
    line = line.strip().lstrip("•").strip()
    if not line or ':' not in line:
        continue
    name, desc = line.split(':', 1)
    categories.append((name.strip(), desc.strip()))

# 3. Persist to SQLite
conn = sqlite3.connect('TaoWar-X.db')
cursor = conn.cursor()

# Create categories table if needed
cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Insert each category (ignore duplicates)
for name, desc in categories:
    cursor.execute(
        'INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)',
        (name, desc)
    )

conn.commit()
conn.close()

print(f"Imported {len(categories)} categories into influencers.db")
