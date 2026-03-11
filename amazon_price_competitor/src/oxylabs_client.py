import json
import os
import time
from urllib import response  
import requests
import streamlit as st

from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file
OXYLABS_BASE_URL = "https://realtime.oxylabs.io/v1/queries"
 # Base URL for Oxylabs API

def extract_content(payload):
    # Extract the content from the API response, handling different possible structures of the response
    if isinstance(payload, dict): # Check if the response is a dictionary, which is the expected structure for the API response. a payload can be a dictionary or a list, depending on the API response structure. We need to handle both cases to ensure that we can extract the content correctly regardless of how the API returns the data.
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
    return payload 

def scrape_product_details(asin, geo=None, domain=None):
    payload = {
        "source": "amazon_product",
        "query": asin,
        "parse": True
    }

    if geo:
        payload["geo_location"] = geo
    if domain:
        payload["domain"] = domain

    raw = post_query(payload)
    if not raw:
        return None

    content = extract_content(raw)
    normalized = normalize_product(content)

    normalized["asin"] = normalized.get("asin") or asin
    normalized["geo_location"] = geo
    normalized["amazon_domain"] = domain

    return normalized


def clean_product_name(title):
    # Clean the product name by removing any extra information after certain delimiters like "-" or "|", which are commonly used in product titles to separate the main title from additional details. This helps to standardize the product names and make them more consistent for comparison and analysis.
    if "-" in title:
        # If the title contains a "-", we can split the title at the first occurrence of "-" and take the part before it as the main product name. This is done to remove any additional information that may be included in the title after the "-", which is often used to separate the main product name from other details such as size, color, or other attributes. By taking only the part before the "-", we can focus on the core product name for comparison and analysis
        title = title.split("-")[0]
    if "|" in title:
        # If the title contains a "|", we can split the title at the first occurrence of "|" and take the part before it as the main product name. Similar to the previous case with "-", this is done to remove any additional information that may be included in the title after the "|", which is often used to separate the main product name from other details such as size, color, or other attributes. By taking only the part before the "|", we can focus on the core product name for comparison and analysis.
        title = title.split("|")[0]
    return title.strip()



def extract_search_results(content):
    items = []
    if not isinstance(content, dict):
        return items  # Return an empty list if the content is not a dictionary, as we expect the content to be a dictionary containing the search results. If the content is not in the expected format, we cannot extract the search results, so we return an empty list to indicate that there are no valid search results to process.
    if "results" in content:
        results = content["results"] # Extract the search results from the content, which is expected to be a dictionary containing a "results" key that holds the search results data. The structure of the search results can vary, so we need to handle different possible formats to ensure that we can extract the relevant information correctly.
        if isinstance(results, dict): # Check if the results are in a dictionary format, which is one of the expected formats for the search results. If the results are in a dictionary format, we can check for specific keys such as "organic" and "paid" to extract the relevant search result items. isinstance(results, dict) is used to ensure that we are working with a dictionary structure before trying to access specific keys, which helps to prevent errors and allows us to handle different response formats gracefully.
            if "organic" in results: # If the results contain an "organic" key, we can extend our items list with the organic search results, which are typically the non-sponsored search results that appear in the main search results section on Amazon. These results are important for competitor analysis as they represent the products that are ranking organically for the given search query.
                items.extend(results["organic"]) # Extend the items list with the organic search results from the results dictionary, which allows us to gather all the relevant search result items for further processing and analysis in our application. By extending the items list with the organic search results, we can ensure that we have a comprehensive set of search results to work with when performing competitor analysis and other operations on the product data.
            if "paid" in results: # If the results contain a "paid" key, we can extend our items list with the paid search results, which are typically the sponsored search results that appear in the main search results section on Amazon. These results are important for competitor analysis as they represent the products that are being promoted through advertising for the given search query.
                items.extend(results["paid"])
    elif "products" in content and isinstance(content["products"], list):
        items.extend(content["products"])

    return items 


def normalize_search_results(item):
    # Normalize the search results to ensure consistent structure and to extract the necessary information for competitor analysis. This function takes a raw search result item from the API response and extracts the ASIN, title, price, rating, and other relevant information, while also ensuring that the data is structured in a consistent way for further processing in the application. If the item does not contain either an ASIN or a title, it returns None to indicate that this item should be skipped in the search results, as we need at least one of these pieces of information to identify the product and perform competitor analysis effectively.
    asin = item.get("asin") or item.get("product_asin")
    title = item.get("title")

    if not (asin or title):
        return None  # If either ASIN or title is missing, we cannot normalize this item, so we return None to indicate that this item should be skipped in the search results.

    return {
        "asin": asin,
        "title": title,
        # "brand": item.get("brand"),
        "price": item.get("price"),
        # "currency": item.get("currency"),
        "rating": item.get("rating"),
        # "url": item.get("url"),
        # "images": item.get("images", []),
        "category": item.get("category", []),
        # "category_path": item.get("category_path", []),
    }

# gathering competitors amazon search
def search_competitors(query_title, domain, categories, pages, geo=None):
    st.write(f"Searching for competitors with query: {query_title}, domain: {domain}, categories: {categories}, pages: {pages}, geo: {geo}")

    search_title = clean_product_name(query_title)
    results = []
    seen_asins = set()  # To track seen ASINs and avoid duplicates

    strategies = [
        "featured",  # Search for featured products
        "price_asc",  # Search for products sorted by price in ascending order
        "price_desc",  # Search for products sorted by price in descending order
        "avg_rating" # Search for products sorted by average rating
    ]
    for sort_by in strategies:
        for page in range(1, max(1,pages) + 1): # Loop through the specified number of pages for each search strategy, starting from page 1 up to the maximum number of pages specified by the user. This allows us to gather a comprehensive set of search results for competitor analysis across different sorting strategies and multiple pages of results.
            payload = {
            "source": "amazon_search",
            "query": search_title,
            "categories": categories,
            "page": page,
            "sort_by": sort_by,
            "geo_location": geo,
            "parse": True
            }

            if domain:
                payload["domain"] = domain
            if categories and categories[0]:  # Only include categories in the payload if they are provided and not empty
                payload["refinements"] = {" category": categories[0]}  # Add the first category as a refinement to the search query to narrow down the search results to products that belong to the specified category, which can help improve the relevance of the search results for competitor analysis.
            content = extract_content(post_query(payload))
            items = extract_search_results(content)
            for item in items:
                result = normalize_search_results(item)
                if result and result["asin"] not in seen_asins:  # Only add the result to the results list if it is valid and its ASIN has not been seen before, which helps to avoid duplicates in the search results and ensures that we have a unique set of competitors for analysis.
                    
                    seen_asins.add(result["asin"])  # Add the ASIN of the current result to the seen_asins set to track it and prevent future duplicates in the search results.
                    results.append(result)  # Add the normalized search result to the results list for further processing and analysis in the application.
            time.sleep(0.1)  # Sleep for a short time between requests to avoid hitting API rate limits and to be respectful of the API provider's resources. This helps to ensure that our application can continue to function smoothly without being blocked or throttled by the API provider due to excessive requests in a short period of time.

    st.write(f"Found {len(results)} unique competitors for the product '{query_title}' across {pages} pages of search results with different sorting strategies.")
    return results

def scrape_multiple_products(asins, geo=None, domain=None):
    st.write(f"Scraping product details for ASINs: {asins} with geo: {geo} and domain: {domain}")
    products = []
    progress_text = st.empty()  # Create an empty placeholder for the progress text
    progress_bar = st.progress(0)  # Create a progress bar initialized to 0%
    total = len(asins)  # Get the total number of ASINs to scrape for progress tracking
    for idx, a in enumerate(asins, 1):
        try:
            progress_text.text(f"processing competitor {idx}/{total} with ASIN: {a}")  # Update the progress text to show the current ASIN being processed and the overall progress in terms of number of ASINs scraped out of the total.
            progress_bar.progress(idx / total)  # Update the progress bar based on the current index of the ASIN being processed relative to the total number of ASINs, which provides a visual representation of the scraping progress for the user.
            product = scrape_product_details(a, geo, domain)  # Scrape the product details for the current ASIN using the scrape_product_details function, which will return the normalized product data for that ASIN.
            products.append(product)  # Add the scraped product details to the products list for further processing and analysis in the application.
            progress_text.write(f"Successfully scraped product details for ASIN: {a}. Found: {product.get('title',a)}")  # Update the progress text to indicate that the product details for the current ASIN have been successfully scraped, and display the title of the product if available, or the ASIN if the title is not available, to provide feedback to the user about the progress of the scraping process.
        except Exception as e:
            progress_text.write(f"Error scraping product details for ASIN: {a}. Error: {e}")  # If an error occurs while scraping the product details for the current ASIN, update the progress text to indicate that there was an error, and display the error message to provide feedback to the user about any issues encountered during the scraping process.

    progress_text.empty()  # Clear the progress text once all ASINs have been processed to clean up the user interface after the scraping process is complete.
    progress_bar.empty()  # Clear the progress bar once all ASINs have been processed to clean up the user interface after the scraping process is complete.
    st.write(f"Finished scraping product details for {len(products)} products out of {total} competitors.")  # Display a message indicating that the scraping process is finished and show the total number of products for which details were successfully scraped, providing feedback to the user about the completion of the scraping process.
    return products  # Return the list of scraped product details for further processing and analysis in the application.






# def scrape_product_details(asin, geo=None, domain=None):
#     # This function is responsible for scraping the product details from the Oxylabs API based on the provided ASIN, Geo location, and domain. It constructs the payload for the API request, sends the request, and processes the response to extract and normalize the product information.
#     payload = {
#         "source": "amazon_product",  # Source identifier for the API request, can be used for tracking and analytics purposes on the Oxylabs side
#         "query": asin,
#         "geo_location": geo,
#         "domain": domain,
#         "parse": True
#     }
#     raw = post_query(payload)  # Send the API request with the constructed payload and get the raw response
#     if not raw:
#       return None 
#     content = extract_content(raw)  # Extract the content from the API response
#     normalized = normalize_product(content)  # Normalize the product data to ensure consistent structure  
#     normalized["asin"] = normalized.get("asin") or asin
#     normalized["amazon_domain"] = domain
#     normalized["geo_location"] = geo     
#     response = post_query(payload)  # Send the API request with the constructed payload
#     if not normalized.get("asin"): # If the normalized product data does not contain an ASIN, we can set it to the ASIN that was used in the query to ensure that we have a reference to the product being scraped, even if the API response did not include the ASIN in the content. This is important for maintaining a consistent structure in the product data and ensuring that we can identify the product correctly in our database and application logic.
#         normalized["asin"] = asin  # Ensure that the ASIN is included in the normalized product data, even if it was not provided in the API response
#     # normalized["amazon_domain"] = domain  # Add the Amazon domain to the normalized product data for reference
#     # normalized["geo_location"] = geo  # Add the Geo location to the normalized product data for reference

#     return normalized  # Return the normalized product data




def post_query(payload):
    username = os.getenv("OXYLABS_USERNAME")
    password = os.getenv("OXYLABS_PASSWORD")
    api_key = os.getenv("OXYLABS_API_KEY")
    
    response = requests.post(
        OXYLABS_BASE_URL,
        json=payload,
        auth=(username, password),
        timeout=30,
    )
    # if response.status_code == 200:
    #     print("Price information fetched successfully!")
    #     response.raise_for_status()  # Raise an exception for HTTP errors
    #     return response.json()
    # else:
    #     st.error(f"Error fetching price information: {response.status_code} - {response.text}")
    #     return None
    try:
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError:
        st.error(f"Error fetching price information: {response.status_code}")
        st.code(response.text)
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
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

def scrape_price(asin, geo=None, domain=None):
    payload = {
        "source": "amazon_product",
        "query": asin,
        # "domain": domain,
        "geo_location": geo,
        "parse": True
    }

    return post_query(payload)



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