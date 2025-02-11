from typing import Dict, List, Optional
import json
from dataclasses import asdict
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

def format_ingredients_list(ingredients: List[Dict]) -> str:
    """Format ingredients into a readable shopping list."""
    formatted = []
    for item in ingredients:
        quantity = item.get('quantity', '')
        unit = item.get('unit', '')
        name = item.get('name', '')
        formatted.append(f"- {quantity} {unit} {name}".strip())
    return "\n".join(formatted)

def format_store_recommendations(stores: List[Dict]) -> str:
    """Format store recommendations into readable text."""
    formatted = []
    for store in stores:
        name = store.get('name', '')
        address = store.get('address', '')
        specialty_items = store.get('specialty_items', [])
        
        store_info = f"* {name} - {address}"
        if specialty_items:
            store_info += f"\n  Recommended for: {', '.join(specialty_items)}"
        formatted.append(store_info)
    
    return "\n".join(formatted)

def generate_final_report(state: Dict) -> str:
    """Generate the final formatted report."""
    from meal_prompts import FINAL_REPORT_TEMPLATE
    
    return FINAL_REPORT_TEMPLATE.format(
        recipe_name=state['recipe_name'],
        store_recommendations=format_store_recommendations(state['store_recommendations']),
        ingredients=format_ingredients_list(state['ingredients']),
        instructions="\n".join(f"{i+1}. {step}" for i, step in enumerate(state['instructions']))
    ) 