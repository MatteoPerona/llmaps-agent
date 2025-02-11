import json
from typing_extensions import Literal
from dataclasses import asdict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph

from configuration import Configuration, SearchAPI
from utils import tavily_search, format_sources, perplexity_search
from state import MealPlanState, MealPlanStateInput, MealPlanStateOutput
from meal_prompts import (
    RECIPE_SEARCH_INSTRUCTIONS,
    STORE_SEARCH_INSTRUCTIONS,
    FINAL_REPORT_TEMPLATE
)
from meal_utils import generate_final_report

def search_recipes(state: MealPlanState, config: RunnableConfig):
    """Search for recipes matching user preferences"""
    
    try:
        # Format the prompt with proper string formatting
        search_prompt = RECIPE_SEARCH_INSTRUCTIONS.format(
            location=state.location,
            cuisine=state.cuisine_preference or "any",
            restrictions=", ".join(state.dietary_restrictions) or "none",
            flavor=state.flavor_preference or "any"
        )
        
        # Generate search query
        configurable = Configuration.from_runnable_config(config)
        llm = ChatOpenAI(
            model=configurable.model_name,
            temperature=0
        )
        result = llm.invoke(
            [SystemMessage(content=search_prompt),
            HumanMessage(content="Generate a recipe search query:")]
        )
        query = json.loads(result.content)
        
        if not isinstance(query, dict) or 'query' not in query:
            raise ValueError("Invalid query format from LLM")
        
        # Perform web search
        if configurable.search_api == SearchAPI.TAVILY:
            search_results = tavily_search(query['query'])
        else:
            search_results = perplexity_search(query['query'], 0)
            
        if not search_results:
            raise ValueError("No search results found")
            
        return {
            "web_research_results": [search_results],
            "sources_gathered": [format_sources(search_results)]
        }
        
    except (json.JSONDecodeError, ValueError, Exception) as e:
        print(f"Error in recipe search: {str(e)}")
        # Return a minimal valid state update
        return {
            "web_research_results": [{
                "results": [{
                    "title": "Error in search",
                    "content": f"Failed to search for recipes: {str(e)}",
                    "url": ""
                }]
            }],
            "sources_gathered": ["Search failed"]
        }

def parse_recipe(state: MealPlanState, config: RunnableConfig):
    """Extract recipe information from search results"""
    
    # Use LLM to parse recipe details
    configurable = Configuration.from_runnable_config(config)
    llm = ChatOpenAI(
        model=configurable.model_name,
        temperature=0
    )
    
    parse_prompt = """Extract recipe information from the search results and format it as a valid JSON object.

<SEARCH_RESULTS>
{search_results}
</SEARCH_RESULTS>

Return a JSON object with exactly these keys:
{{
    "recipe_name": "Name of the recipe",
    "ingredients": [
        {{
            "quantity": "numeric amount",
            "unit": "measurement unit (e.g., cup, tablespoon, etc.)",
            "name": "ingredient name"
        }}
    ],
    "instructions": [
        "Step 1 instruction",
        "Step 2 instruction",
        "etc."
    ]
}}

If no clear recipe is found in the search results, return a basic recipe structure with placeholder values.

Example response:
{{
    "recipe_name": "Spicy Vegetarian Pasta",
    "ingredients": [
        {{
            "quantity": "16",
            "unit": "oz",
            "name": "penne pasta"
        }},
        {{
            "quantity": "2",
            "unit": "tablespoons",
            "name": "olive oil"
        }}
    ],
    "instructions": [
        "Boil water in a large pot",
        "Cook pasta according to package directions",
        "Heat olive oil in a pan"
    ]
}}"""
    
    # Get the most recent search results and format them
    most_recent_results = state.web_research_results[-1]
    if isinstance(most_recent_results, dict) and 'results' in most_recent_results:
        # Format Tavily results
        search_content = "\n\n".join([
            f"Title: {result.get('title', '')}\n"
            f"Content: {result.get('content', '')}\n"
            f"URL: {result.get('url', '')}"
            for result in most_recent_results['results']
        ])
    else:
        # Handle raw text or other formats
        search_content = str(most_recent_results)
    
    # Get recipe information from LLM
    result = llm.invoke(
        [
            SystemMessage(content=parse_prompt.format(search_results=search_content)),
            HumanMessage(content="Extract and format the recipe information as JSON:")
        ]
    )
    
    try:
        recipe_data = json.loads(result.content)
        
        # Validate the structure
        required_keys = {'recipe_name', 'ingredients', 'instructions'}
        if not all(key in recipe_data for key in required_keys):
            raise ValueError("Missing required keys in recipe data")
            
        return {
            "recipe_name": recipe_data['recipe_name'],
            "ingredients": recipe_data['ingredients'],
            "instructions": recipe_data['instructions']
        }
        
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error parsing recipe: {str(e)}")
        # Return a fallback recipe structure
        return {
            "recipe_name": "Basic Recipe (Error in parsing)",
            "ingredients": [
                {"quantity": "1", "unit": "serving", "name": "ingredients not found"}
            ],
            "instructions": ["Recipe instructions could not be parsed"]
        }

def find_stores(state: MealPlanState, config: RunnableConfig):
    """Search for grocery stores and generate recommendations"""
    
    # Format the store search prompt
    search_prompt = STORE_SEARCH_INSTRUCTIONS.format(
        location=state.location,
        ingredients="\n".join(f"- {i['name']}" for i in state.ingredients)
    )
    
    # Generate store search query
    configurable = Configuration.from_runnable_config(config)
    llm = ChatOpenAI(
        model=configurable.model_name,
        temperature=0
    )
    result = llm.invoke(
        [SystemMessage(content=search_prompt),
        HumanMessage(content="Generate a store search query:")]
    )
    query = json.loads(result.content)
    
    # Search for stores
    if configurable.search_api == SearchAPI.TAVILY:
        search_results = tavily_search(query['query'])
    else:
        search_results = perplexity_search(query['query'], 0)
    
    # Format search results for the LLM
    if isinstance(search_results, dict) and 'results' in search_results:
        search_content = "\n\n".join([
            f"Title: {result.get('title', '')}\n"
            f"Content: {result.get('content', '')}\n"
            f"URL: {result.get('url', '')}"
            for result in search_results['results']
        ])
    else:
        search_content = str(search_results)
    
    # Parse store information with better prompt and error handling
    store_prompt = """Extract grocery store information from the search results.

<SEARCH_RESULTS>
{search_content}
</SEARCH_RESULTS>

Return a JSON array of stores in this exact format:
{{
    "stores": [
        {{
            "name": "Store name",
            "address": "Store address",
            "specialty_items": ["item1", "item2"]
        }}
    ]
}}

Example response:
{{
    "stores": [
        {{
            "name": "Whole Foods Market",
            "address": "123 Main St, San Diego, CA 92101",
            "specialty_items": ["organic produce", "vegan options"]
        }},
        {{
            "name": "Trader Joe's",
            "address": "456 Market St, San Diego, CA 92102",
            "specialty_items": ["specialty pasta", "vegetarian items"]
        }}
    ]
}}"""
    
    try:
        # Get store information from LLM
        result = llm.invoke(
            [
                SystemMessage(content=store_prompt.format(search_content=search_content)),
                HumanMessage(content="Extract and format the store information as JSON:")
            ]
        )
        
        # Parse the response
        store_data = json.loads(result.content)
        
        # Validate the structure
        if not isinstance(store_data, dict) or 'stores' not in store_data:
            raise ValueError("Invalid store data format")
        
        stores = store_data['stores']
        if not isinstance(stores, list):
            raise ValueError("Stores must be a list")
            
        # Validate each store
        for store in stores:
            required_keys = {'name', 'address', 'specialty_items'}
            if not all(key in store for key in required_keys):
                raise ValueError(f"Store missing required keys: {store}")
        
        return {"store_recommendations": stores[:configurable.max_store_recommendations]}
        
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error parsing store data: {str(e)}")
        # Return a fallback store recommendation
        return {
            "store_recommendations": [{
                "name": "Local Grocery Store",
                "address": f"Search for grocery stores near {state.location}",
                "specialty_items": ["Unable to parse store data"]
            }]
        }

def create_report(state: MealPlanState):
    """Generate the final meal planning report"""
    return {"final_report": generate_final_report(asdict(state))}

# Build the graph
builder = StateGraph(MealPlanState, input=MealPlanStateInput, output=MealPlanStateOutput, config_schema=Configuration)

# Add nodes
builder.add_node("search_recipes", search_recipes)
builder.add_node("parse_recipe", parse_recipe)
builder.add_node("find_stores", find_stores)
builder.add_node("create_report", create_report)

# Add edges
builder.add_edge(START, "search_recipes")
builder.add_edge("search_recipes", "parse_recipe")
builder.add_edge("parse_recipe", "find_stores")
builder.add_edge("find_stores", "create_report")
builder.add_edge("create_report", END)

graph = builder.compile()