RECIPE_SEARCH_INSTRUCTIONS = """Generate a web search query to find recipes that match the user's preferences.

<USER_PREFERENCES>
Location: {location}
Cuisine: {cuisine}
Dietary Restrictions: {restrictions}
Flavor Profile: {flavor}
</USER_PREFERENCES>

Format your response as a JSON object with these keys:
- "query": The search query string
- "rationale": Brief explanation of why this query matches preferences

Example:
{{
    "query": "healthy vegetarian thai curry recipe spicy",
    "rationale": "Matches user's Thai cuisine preference and vegetarian restriction"
}}
"""

STORE_SEARCH_INSTRUCTIONS = """Generate a web search query to find grocery stores near the user that likely stock the needed ingredients.

<LOCATION>
{location}
</LOCATION>

<INGREDIENTS>
{ingredients}
</INGREDIENTS>

Format your response as a JSON object with these keys:
- "query": The search query string
- "specialty_items": List of ingredients that might need specialty stores

Example:
{{
    "query": "asian grocery stores near downtown seattle",
    "specialty_items": ["kaffir lime leaves", "galangal"]
}}
"""

FINAL_REPORT_TEMPLATE = """# Meal Planning Report

## Recipe: {recipe_name}

### Recommended Stores:
{store_recommendations}

### Shopping List:
{ingredients}

### Cooking Instructions:
{instructions}

*All store recommendations and prices are approximate. Please call ahead to confirm availability.*
""" 