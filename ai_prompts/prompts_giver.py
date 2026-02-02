

# def first_post_prompt():
#     template = """
#         To generate a Daily Crypto Update for the TaoWAR X handle that is informative, compliant, and engaging. Incorporate the following enhanced instructions:

#         **Post Structure Guidelines**:
#         • **Header**: {header} add this to header 
#          After this we will get {thread_no} {category} 
        
#         • **Category Sections**: For each category with relevant posts:
#         - Write a **concise 2–3 sentence** summary using specific details (e.g., TVL, market levels, on-chain data).
#         - Include **insightful, neutral commentary** — such as trend implications or contrasting views.
#         - Use a **professional, accessible tone** (no hype, no financial advice).

#         **Mentions & Tagging Policy**:
#         • Only mention a **maximum of 2 relevant influencers** by @username — pick those whose tweets were most central.
#         • If more contributed, **do not tag them** — use plain text like “and others”.
#         • Avoid tagging the same influencer in multiple consecutive batches.

#         **Hashtags**:
#         • Use **no more than 2 hashtags per tweet** — ideally, one should be category-specific (e.g., #DeFi, #Layer2).
#         • Include the branding tag **#TaoWARSignals** (preferably at the end).
#         • Avoid using **unrelated or trending hashtags** just to gain reach.

#         • Keep each tweet **within 280 characters**.
#         • Begin the tweet with: {header}
#           {thread_no} {category}. 
        
#         **Compliance Notes**:
#         • Ensure summaries do **not sound promotional**, exaggerated, or speculative.
#         • Do **not reference influencers in a way that implies endorsement** or attach value claims to their posts.
#         • Avoid repetitive openings or phrases across days (rotate templates).
#         • The content should be **suitable for a public automated account** and respectful of all sources mentioned.

#         The tweet should be like a normal tweet, no emojies or headings etc involved only the relevnet hashtags and mentions
#         Stay strickly within the 280 characters limit, The summary should not be greater then 280 characters.. This 280 character limit is for the whole text generation.
#         ---

#         Generate your tweet using this structure:
        
#         This is the category and its Description:
#         Category: {category}
#         Category Description:  {category_desp}

#         Posts: Which belong to this category
#         {posts}
        
#         important: The post should be formatted like this:
#         - There should be a header and an empty line after it.
#         - There should be {thread_no} {category}: and an empty line after this.
#         - Then there should be the summary of the post and an empty line after it.
#         - Then there should be hashtag
#         - Keep everything within 280 characters, this includes everything from header to hasttags, evrything must be in 280 characters.
        
        
#         Example:
#         {header}
        
#         {thread_no} {category}:
        
#         The summary of the posts for the category.
        
#         the hasttags
#         """
        
#     return template


def middle_post_prompt():
    template = """
        To generate a Daily Crypto Update for the TaoWAR X handle that is informative, compliant, and engaging. Incorporate the following enhanced instructions:

        **Post Structure Guidelines**:
        • **Header**: {category} 
        • **Category Sections**: For each category with relevant posts:
        - Write a **concise 2–3 sentence** summary using specific details (e.g., TVL, market levels, on-chain data).
        - Include **insightful, neutral commentary** — such as trend implications or contrasting views.
        - Use a **professional, accessible tone** (no hype, no financial advice).

        **Mentions & Tagging Policy**:
        • Only mention a **maximum of 3 relevant influencers** by @username — pick those whose tweets were most central.
        • USe them in your Analysis

        **Hashtags**:
        • Use **no more than 2 hashtags per tweet** — ideally, one should be category-specific (e.g., #DeFi, #Layer2).
        • Include the branding tag **#TaoWARSignals** (preferably at the end).
        • Avoid using **unrelated or trending hashtags** just to gain reach.

        • Keep each tweet **within 280 characters**.
        • Begin the tweet with: {category}
          
        **Compliance Notes**:
        • Ensure summaries do **not sound promotional**, exaggerated, or speculative.
        • Do **not reference influencers in a way that implies endorsement** or attach value claims to their posts.
        • Avoid repetitive openings or phrases across days (rotate templates).
        • The content should be **suitable for a public automated account** and respectful of all sources mentioned.

        The tweet should be like a normal tweet, no emojies or headings etc involved only the relevnet hashtags and mentions
        Stay strickly within the 280 characters limit, The summary should not be greater then 280 characters.. This 280 character limit is for the whole text generation.
        ---

        Generate your tweet using this structure:
        
        This is the category and its Description:
        Category: {category}
        Category Description:  {category_desp}

        Posts: Which belong to this category
        {posts}
        
        important: The post should be formatted like this:
        - There should be a header and an empty line after it.
        - Then there should be the summary of the post and an empty line after it.
        - Then there should be hashtag
        - Keep everything within 280 characters, this includes everything from header to hasttags, evrything must be in 280 characters.
        
        Example format:
        {category}:
        
        The summary of the posts for the category.
        
        the hasttags
        
        Example summary:
        Stablecoins: 
        
        The Tinian government plans to issue a USD-backed stablecoin on the eCash network, marking a historic move for U.S. public entities. 
        Meanwhile, discussions around RAI's transition to @letsgethai highlight the complexities of stablecoin development and market fit. 
        
        #Stablecoins #TaoWARSignals
        """
    return template

# def question_add_prompt():
    
#     template = """
#         To generate a Daily Crypto Update for the TaoWAR X handle that is informative, compliant, and engaging. Incorporate the following enhanced instructions:

#         **Post Structure Guidelines**:
#         • **Header**: {thread_no} {category} 
#         • **Category Sections**: For each category with relevant posts:
#         - Write a **concise 2–3 sentence** summary using specific details (e.g., TVL, market levels, on-chain data).
#         - Include **insightful, neutral commentary** — such as trend implications or contrasting views.
#         - Use a **professional, accessible tone** (no hype, no financial advice).

#         **Mentions & Tagging Policy**:
#         • Only mention a **maximum of 2 relevant influencers** by @username — pick those whose tweets were most central.
#         • If more contributed, **do not tag them** — use plain text like “and others”.
#         • Avoid tagging the same influencer in multiple consecutive batches.

#         **Hashtags**:
#         • Use **no more than 2 hashtags per tweet** — ideally, one should be category-specific (e.g., #DeFi, #Layer2).
#         • Include the branding tag **#TaoWARSignals** (preferably at the end).
#         • Avoid using **unrelated or trending hashtags** just to gain reach.

#         • Keep each tweet **within 280 characters**.
#         • Begin the tweet with: {thread_no} {category}
          
#         **Compliance Notes**:
#         • Ensure summaries do **not sound promotional**, exaggerated, or speculative.
#         • Do **not reference influencers in a way that implies endorsement** or attach value claims to their posts.
#         • Avoid repetitive openings or phrases across days (rotate templates).
#         • The content should be **suitable for a public automated account** and respectful of all sources mentioned.

#         The tweet should be like a normal tweet, no emojies or headings etc involved only the relevnet hashtags and mentions
#         Stay strickly within the 280 characters limit, The summary should not be greater then 280 characters.. This 280 character limit is for the whole text generation.
#         ---

#         Generate your tweet using this structure:
        
#         This is the category and its Description:
#         Category: {category}
#         Category Description:  {category_desp}

#         Posts: Which belong to this category
#         {posts}
        
#         important: The post should be formatted like this:
#         - There should be a header and an empty line after it.
#         - Then there should be the summary of the post and an empty line after it.
#         - Then there should be hashtag
#         - On next line there should be a relevent question.
#         - Keep everything within 280 characters, this includes everything from header to hasttags, evrything must be in 280 characters.
        
#         Example:
#         {thread_no} {category}:
        
#         The summary of the posts for the category.
        
#         the hasttags
        
#         add a question at end 
#         example:
#         What’s your market vibe?
#         """
#     return template

# def last_post_prompt():
#     template = """
#         To generate a Daily Crypto Update for the TaoWAR X handle that is informative, compliant, and engaging. Incorporate the following enhanced instructions:

#         **Post Structure Guidelines**:
#         • **Header**: {thread_no} {category}, the heading should be bold
#         • **Category Sections**: For each category with relevant posts:
#         - Write a **concise 2–3 sentence** summary using specific details (e.g., TVL, market levels, on-chain data).
#         - Include **insightful, neutral commentary** — such as trend implications or contrasting views.
#         - Use a **professional, accessible tone** (no hype, no financial advice).

#         **Mentions & Tagging Policy**:
#         • Only mention a **maximum of 2 relevant influencers** by @username — pick those whose tweets were most central.
#         • If more contributed, **do not tag them** — use plain text like “and others”.
#         • Avoid tagging the same influencer in multiple consecutive batches.

#         **Hashtags**:
#         • Use **no more than 2 hashtags per tweet** — ideally, one should be category-specific (e.g., #DeFi, #Layer2).
#         • Include the branding tag **#TaoWARSignals** (preferably at the end).
#         • Avoid using **unrelated or trending hashtags** just to gain reach.

#         • Keep each tweet **within 280 characters**.
#         • Begin the tweet with: {thread_no} {category}

#         **Compliance Notes**:
#         • Ensure summaries do **not sound promotional**, exaggerated, or speculative.
#         • Do **not reference influencers in a way that implies endorsement** or attach value claims to their posts.
#         • Avoid repetitive openings or phrases across days (rotate templates).
#         • The content should be **suitable for a public automated account** and respectful of all sources mentioned.

#         The tweet should be like a normal tweet, no emojies or headings etc involved only the relevnet hashtags and mentions
#         Stay strickly within the 280 characters limit, The summary should not be greater then 280 characters. This 280 character limit is for the whole text generation.
#         ---

#         Generate your tweet using this structure:
        
#         This is the category and its Description:
#         Category: {category}
#         Category Description:  {category_desp}

#         Posts: Which belong to this category
#         {posts}
        
#         important: The post should be formatted like this:
#         - There should be a header and an empty line after it.
#         - Then there should be the summary of the post and the cta at the end {CTA} and an empty line after it.
#         - Then there should be hashtag
#         - Keep everything within 280 characters, this includes everything from header to hasttags, evrything must be in 280 characters.
        
#         Example:
#         {thread_no} {category}: (this heading should be bold)
        
#         The summary of the posts for the category and also add this cta {CTA} to this.
        
#         the hasttags
#         """
#     return template
    
# def default_prompt():
#     template = """
#         To generate a Daily Crypto Update for the TaoWAR X handle that is informative, compliant, and engaging. Incorporate the following enhanced instructions:

#         **Post Structure Guidelines**:
#         • **Header**: {thread_no} {category} 
#         • **Category Sections**: For each category with relevant posts:
#         - Write a **concise 2–3 sentence** summary using specific details (e.g., TVL, market levels, on-chain data).
#         - Include **insightful, neutral commentary** — such as trend implications or contrasting views.
#         - Use a **professional, accessible tone** (no hype, no financial advice).

#         **Mentions & Tagging Policy**:
#         • Only mention a **maximum of 2 relevant influencers** by @username — pick those whose tweets were most central.
#         • If more contributed, **do not tag them** — use plain text like “and others”.
#         • Avoid tagging the same influencer in multiple consecutive batches.

#         **Hashtags**:
#         • Use **no more than 2 hashtags per tweet** — ideally, one should be category-specific (e.g., #DeFi, #Layer2).
#         • Include the branding tag **#TaoWARSignals** (preferably at the end).
#         • Avoid using **unrelated or trending hashtags** just to gain reach.

#         • Keep each tweet **within 280 characters**.
#         • Begin the tweet with: {thread_no} {category}
          
#         CTA:`{CTA}` — if none is provided, omit the closing line entirely. This is only when there is something other than None in CTA

#         **Compliance Notes**:
#         • Ensure summaries do **not sound promotional**, exaggerated, or speculative.
#         • Do **not reference influencers in a way that implies endorsement** or attach value claims to their posts.
#         • Avoid repetitive openings or phrases across days (rotate templates).
#         • The content should be **suitable for a public automated account** and respectful of all sources mentioned.

#         The tweet should be like a normal tweet, no emojies or headings etc involved only the relevnet hashtags and mentions
#         Stay strickly within the 280 characters limit, The summary should not be greater then 280 characters.. This 280 character limit is for the whole text generation.
#         ---

#         Generate your tweet using this structure:
        
#         This is the category and its Description:
#         Category: {category}
#         Category Description:  {category_desp}

#         Posts: Which belong to this category
#         {posts}
        
#         important: The post should be formatted like this:
#         - There should be a header and an empty line after it.
#         - Then there should be the summary of the post and an empty line after it.
#         - Then there should be hashtag
#         - Keep everything within 280 characters, this includes everything from header to hasttags, evrything must be in 280 characters.
        
#         Example:
#         {thread_no} {category}:
        
#         The summary of the posts for the category.
        
#         the hasttags
#         """
#     return template

