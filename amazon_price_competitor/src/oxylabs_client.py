import json
import os
import time
from urllib import response  
import requests
import streamlit as st

from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file
OXYLABS_BASE_URL = "https://api.oxylabs.io/v1/amazon/price" # Base URL for Oxylabs API

def extract_content(payload):
    # Extract the content from the API response, handling different possible structures of the response
    if isinstance(payload, dict): # Check if the response is a dictionary, which is the expected structure for the API response
        # If the response is a dictionary, we can directly access the 'content' key
        if "results" in payload and isinstance(payload["results"], list) and len(payload["results"]) > 0:
            first = payload["results"][0] # Get the first result from the results list
            if isinstance(first, dict) and "content" in first: # Check if the first result is a dictionary and contains the 'content' key
                return first["content"] or {}  # Return the content of the first result if it exists
            return payload["results"][0].get("content", {})  # Return the content of the first result if it exists
        if "content" in payload:
            return payload["content"] or {}  # Return the content if it exists in the dictionary
        
    elif isinstance(payload, list) and len(payload) > 0:
        # If the response is a list, we can take the first item and access its 'content' key
        return payload[0].get("content", {})
    else:
        # If the response structure is unexpected, return an empty dictionary
        return {}

def post_query(payload):
    username = os.getenv("OXYLABS_USERNAME")
    password = os.getenv("OXYLABS_PASSWORD")
    api_key = os.getenv("OXYLABS_API_KEY")
    
    response = requests.post(
        OXYLABS_BASE_URL,
        json=payload,
        auth=(username, password),
        headers={"Authorization": f"Bearer {api_key}"}
    )
    if response.status_code == 200:
        print("Price information fetched successfully!")
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    else:
        st.error(f"Error fetching price information: {response.status_code} - {response.text}")
        return None

# This function is used to normalize the product data received from the API to ensure that it has a consistent structure, making it easier to work with in the rest of the application. It takes the raw product data as input and returns a normalized version of that data, ensuring that all expected fields are present and properly formatted.   
def normalize_product(content):
    # Normalize the product data to ensure consistent structure
    category_path = []
    if content.get("category_path"):
        # Remove any leading/trailing whitespace from category names and filter out empty categories
        # This ensures that the category path is clean and does not contain any empty or whitespace-only entries
        category_path = [cat.strip() for cat in content["category_path"] if cat]
        #using list comprehension to iterate over each category in the category_path, stripping any leading or trailing whitespace from the category name using the strip() method, and then filtering out any categories that are empty after stripping (i.e., categories that were originally just whitespace). The resulting list will contain only valid category names without any extra whitespace or empty entries.
    return {
        # Ensure that all expected fields are present in the normalized product data, even if they are missing from the original content
        "asin": content.get("asin"),
        "url": content.get("url"),
        "brand": content.get("brand"),
        "price": content.get("price"),
        "stock": content.get("stock"),
        "title": content.get("title"),
        "rating": content.get("rating"),
        "images": content.get("images", []),
        "categories": content.get("category", []) or content.get("categories", []),
        "category_path": category_path,
        "currency": content.get("currency"),
        "buybox": content.get("buybox", []),
        "product_overview": content.get("product_overview", []),
    }



# I can try this later

# class OxylabsClient:
#     def __init__(self):
#         self.api_key = os.getenv("OXYLABS_API_KEY")
#         self.base_url = OXYLABS_BASE_URL

#     def fetch_price(self, asin, geo=None, domain=None):
#         params = {
#             "asin": asin,
#             "geo": geo,
#             "domain": domain
#         }
#         headers = {
#             "Authorization": f"Bearer {self.api_key}"
#         }
#         try:
#             response = requests.get(self.base_url, params=params, headers=headers)
#             response.raise_for_status()  # Raise an exception for HTTP errors
#             return response.json()  # Return the JSON response from the API
#         except requests.exceptions.RequestException as e:
#             st.error(f"An error occurred while fetching price information: {e}")
#             return None