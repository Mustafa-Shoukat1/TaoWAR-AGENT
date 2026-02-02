def report_prompt() -> str:
    return """
Write a professional, insight-driven summary **for one cryptocurrency category only**, using *only* the supplied posts.
## Hyperlinks rule:
- You must include hyperlinks in the summary. Every handle that you add must have a hyperlink.
- Each material claim must link to its original post.
- Integrate links naturally. Embed the URL on the key noun or phrase—never use “click here,” “this tweet,” or similar filler.
- There should atleast be two hyperlinks in the summary.
- You must abide by these rules. Summary should not be without links.
- Hyperlinks work as refrences to support our summary.
- You must add two hyperlinks even if they are not exactly relevant to the summary. Just remeber that hyperlinks are very necessary in the summary.

## Important – Reference & Link Guidelines
- It is very important to have hyper links in the summary. You must abide by this rule. Summary should not be without links.
- This is a rule that there would be hyperlinks in the summary.
-Every handle that you add must have a hyperlink.
-Remeber the links are must, summary should have adequate amount of hyperlinks in form of refrences to support our summary
-Cite every material claim. Each fact, quote, or data-point must link to its original post.
-Integrate links naturally. Embed the URL on the key noun or phrase—never use “click here,” “this tweet,” or similar filler.
-Anchor to names. When referencing a person, place the hyperlink on their handle or name (e.g., as @vitalikbuterin noted).
-Use only supplied URLs. Do not invent or substitute external sources.
-Maintain narrative flow. Links should fit smoothly within sentences; avoid breaking rhythm with parentheses or footnotes.
-Link frequency matches substance. Include enough links to back your analysis, but don’t over-link trivial points.
-No duplicate linking. Reference a specific post once per summary unless a second citation is essential for clarity.
• Every @handle or organisation name must be hyper-linked to its post at first mention.
• No naked handles (text without link) are allowed.
Link-balance rule
At the end of Evidence-Based Analysis:
• Any quantitative claim (numbers, percentages, yields) must carry a link unless it is already common public data (e.g., BTC block reward).

==================================================
⚠️  CORE OUTPUT RULES
==================================================
• **Heading:** A single plain-text title (e.g. “Market Trends”) on its own line — **no Markdown # symbols**.  
• **Length:** **150 – 200 words**, one paragraph only (hard line-breaks allowed).  
• **Flow:** Hook with the single most trade-relevant stat/event → weave supporting points → close with a forward-looking line.  
• **Watch-list:** Finish with **bold** “What to watch for:” followed by 2-3 catalysts, separated by semicolons and **no final period**.  
• **No duplication across sections:** Do not reuse a stat that will appear in another category summary.

==================================================
🔗  LINK & ATTRIBUTION RULES
==================================================
• Every material claim must cite an *exact* source from the posts.  
• Embed links naturally on the noun/phrase (e.g. “BlackRock’s [ETF inflows](link)”).  
• Always name the author/handle in the sentence.  
• Use **only** the links provided; never invent new ones.
• Using links are must, use from the links provided in the posts.  
• No bare URLs, “click here”, or “this post” phrasing.

==================================================
🖋️  STYLE & VOICE
==================================================
• Seasoned-analyst, newsletter tone: brisk, punchy, concrete.  
• Start with data (“Bitcoin is holding above $105 K…”) or similar according to the category and data provided to you..  
• Vary sentence length; avoid filler such as “recent developments”, “underscores”, “furthermore”, “meanwhile”, “broader implications”.  
• Prefer verbs like *surges*, *slides*, *allocates*, *signals*.  
• Quantify whenever possible (prices, %, TVL, inflows).  
• If the category is **not** "Macro Economics", limit macro chatter to ≤ 50 words.
• Hyperlinks are also necessary in "Macro Economics" category, so use them in the summary. and also in other categories.
• Its a rule that you must use hyperlinks in the summary.
• Make hyper links like this: [handle](link of post) or [company](link) or [protocol](link of post) etc.
• Do not let handle mentions go without hyperlinks.

==================================================
🚫  FORBIDDEN → REPLACEMENTS
==================================================
• cautiously optimistic → guardedly bullish  
• points towards → indicates  
• market dynamics → market behaviour  
• suggests a potential → may trigger  
• underscores the importance → shows why  
• significant momentum → accelerating interest  
“ongoing vulnerabilities” → “continuing risks”
“in light of” → “given”
“underscores” → “shows”
“as highlighted by” → “as noted by”
(Add any new filler detected to this list.)
“ongoing challenges”, “underscore”, “as noted by”, “amid global shifts”	Swap for leaner language: continuing risks, shows, per, as demand shifts. etc

==================================================
📐  STRUCTURE & FORMATTING (ENFORCED)
==================================================
1️⃣  Single line heading (plain text)  
2️⃣  One paragraph (150-200 words)  
3️⃣  • Watch-list syntax: (this is sperate small paragraph just use one /n) End with bold text **What to watch for:** then 2–3 catalysts separated by semicolons and no trailing period.

==================================================
🔬  CONTENT DEVELOPMENT GUIDANCE
==================================================
• This should be exact heading of the summary, only this heading: {category}  
• **Hyperlinks**: Adding hyperlinks is a must, every handle that you add must have a hyperlink.
• **Hyperlinks**: You may add hyperlinks to the summary, with the flow of summary.
• **Hook first:** Lead with the hard number or decisive policy action.  
• **Synthesis over sequence:** Don’t recap post-by-post; blend them into one arc.  
• **Cause-and-effect:** Explicitly link events (“ETF inflows lifted BTC above… which, in turn, …”).  
• **Contrarian angles:** Flag disagreements when posts diverge.  
• **Evidence-based:** Use concrete data, protocol upgrades, policy moves.  
• **No speculation beyond the sources.**
• Whenever you try to mention infleuncer regarding doing reference, you will add the post link to it which you are refereing to.

==================================================
📝  INPUT FIELDS (FROM CALLER)
==================================================
Category: {category}  
Description: {category_desp}  
These things are provided to you, as content, and post link and the influencer name.
Use the links of posts given in the posts to make hyperlinks in the summary.
Posts: 
{posts}

==================================================
📤  OUTPUT SAMPLE SKELETON
==================================================
## Example Output (only for example, you have to make similar structure summary with the context provided)

### DeFi (Decentralized Finance)

Ethereum staking continues to dominate DeFi discourse, with over [35 million ETH now locked](https://defillama.com/staking). The anticipation of a U.S.-approved ETH staking ETF is bringing traditional institutions closer to on-chain yield strategies. Bit Digital recently pivoted from mining to ETH staking, converting its BTC reserves to capitalize on this trend.
Decentralized lending protocols are also evolving. A new [independent risk rating site](https://exponential.fi/risk) for BTC-collateral platforms is helping users evaluate lending safety. These systems may become essential if institutions are to take DeFi seriously.
DEX volume has dropped 20%, but activity on Solana remains strong. Its on-chain perpetual contracts outpaced centralized exchanges by 96% in liquidation volume—a sign that users are hunting for capital-efficient trades amid volatility.
Synaptogenix’s $100M move into Bittensor's TAO reinforces a growing bridge between DeFi and decentralized AI infrastructure.
**What to watch for:** Finalization of ETH staking ETF proposals, adoption of risk scoring platforms, and whether Solana's DeFi momentum holds through macro uncertainty.
"""
