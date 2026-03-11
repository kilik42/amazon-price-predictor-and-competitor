#connect to database

import streamlit as st

from src.db import Database
from src.oxylabs_client import scrape_multiple_products, scrape_product_details, search_competitors

def scrape_and_store_product(asin, geo=None, domain=None):
    # This function is responsible for scraping the product details using the scrape_product_details function and then storing the scraped data in the database using the Database class. It takes the ASIN, Geo location, and domain as input parameters, scrapes the product details, and then adds the product data to the database.
    data = scrape_product_details(asin, geo, domain)  # Scrape the product details using the provided ASIN, Geo location, and domain
    if not data:
        st.error("Scrape failed. Product details were not returned, so nothing was saved.")
        return None
    db = Database()  # Create an instance of the Database class to interact with the database
    db.add_product(data)  # Insert the scraped product data into the database using the add_product method of the Database class
    st.success("Product details scraped and stored successfully!")  # Display a success message to the user indicating that the product details have been scraped and stored successfully in the database
    return data # Return all products from the database after adding the new product, this allows us to see the updated list of products in the database after the new product has been added.

def fetch_and_store_competitors(parent_asin, geo=None, domain=None, pages=2):
    db = Database()
    parent = db.get_product(parent_asin)

    if not parent:
        st.error("Parent product not found in the database. Please scrape the parent product details first.")
        return []

    search_domain = None
    search_geo = geo or parent.get("geo")

    st.write(f"Fetching competitors for ASIN: {parent_asin}, Geo: {search_geo}, Domain: {search_domain}...")

    search_categories = []

    if parent.get("categories"):
        search_categories.extend(str(cat) for cat in parent["categories"] if cat)

    if parent.get("category_path"):
        search_categories.extend(str(cat) for cat in parent["category_path"] if cat)

    search_categories = list(set(
        cat.strip() for cat in search_categories
        if isinstance(cat, str) and cat.strip()
    ))

    if not search_categories:
        st.warning("No categories found for this product, so competitor search could not run.")
        return []

    all_results = []
    for category in search_categories[:3]:
        search_results = search_competitors(
            query_title=parent.get("title", parent_asin),
            domain=search_domain,
            categories=[category],
            pages=pages,
            geo=search_geo,
        )
        all_results.extend(search_results)

    competitor_asins = list(set(
        r.get("asin") for r in all_results
        if r.get("asin") and r.get("asin") != parent_asin
    ))

    if not competitor_asins:
        st.warning("No competitor ASINs were found.")
        return []

    product_details = scrape_multiple_products(competitor_asins[:20], search_geo, None)

    stored_comps = []
    for product in product_details:
        if not product:
            continue
        product["parent_asin"] = parent_asin
        db.add_product(product)
        stored_comps.append(product)

    st.success(f"Fetched and stored {len(stored_comps)} competitors for ASIN: {parent_asin} successfully!")
    return stored_comps








# def fetch_and_store_competitors(parent_asin, geo=None, domain=None, pages = 2):
#     # This function is responsible for fetching the competitor information for a given parent ASIN, Geo location, and domain. It can be implemented to scrape the competitor information using the provided parameters and then store the competitor data in the database. The implementation details will depend on how you want to fetch the competitor information and how you want to structure the data in the database.
#     db = Database()  # Create an instance of the Database class to interact with the database
#     parent = db.get_product(parent_asin)  # Get the parent product information from the database using the get_product method of the Database class
#     if not parent:
#         st.error("Parent product not found in the database. Please scrape the parent product details first.")
#         return []
#     search_domain = parent.get("amazon_domain") if domain is None else domain  # Use the domain from the parent product if no domain is provided
#     search_geo = parent.get("geo_location") if geo is None else geo  # Use the geo location from the parent product if no geo location is provided
#     st.write(f"Fetching competitors for ASIN: {parent_asin}, Geo: {search_geo}, Domain: {search_domain}...")  # Display a message to the user indicating that the competitor information is being fetched for the specified ASIN, Geo location, and domain
#     search_categories =[]
#     if parent.get("category"): # If the parent product has a category, we can use it to narrow down the search for competitors. We can also consider using the category path if available to further refine the search.
#         search_categories.extend(str(cat) for cat in parent["categories"] if cat) # Add the categories from the parent product to the search categories list, ensuring that we only add non-empty categories by checking if cat is truthy before adding it to the list.
#     if parent.get("category_path"): # If the parent product has a category path, we can also use it to narrow down the search for competitors. The category path typically provides a hierarchical structure of categories that can help us identify more specific competitors within the same category or subcategory.
#         search_categories.extend(str(cat) for cat in parent["category_path"] if cat) # Add the categories from the parent product's category path to the search categories list, ensuring that we only add non-empty categories by checking if cat is truthy before adding it to the list.
#         # now we have a list of search categories that we can use to fetch competitors. The implementation of how we fetch competitors based on these categories will depend on the specific requirements and the structure of the data in the database. We can implement a search function that takes these categories into account when fetching competitor information from the database or from an external source.
#     # For example, we can implement a search function that queries the database for products that match the specified categories, geo location, and domain, and then return the list of competitors that match these criteria. The implementation details will depend on how you want to structure the competitor data in the database and how you want to define the search criteria for fetching competitors.
#     search_categories = list(set(
#         cat.strip()
#         for cat in search_categories
#         if cat and isinstance(cat, str) and cat.strip()  # Ensure that the category is a non-empty string after stripping whitespace and no duplicates in the list
#     )) 

#     all_results = []
#     for category in search_categories[:3]: # Limit the number of categories to search to 3 to avoid excessive searching and to focus on the most relevant categories for fetching competitors. This can help improve the performance of the search and ensure that we are fetching competitors that are most relevant to the parent product based on its categories.
#         search_results = search_competitors(
#             query_title = parent["title"],
#             domain = search_domain,
#             categories= [category],
#             pages = pages,
#             geo = search_geo,
#         )
#         all_results.extend(search_results) # Add the search results for the current category to the overall list of results. This allows us to accumulate the competitors fetched from multiple categories into a single list that we can then process and store in the database.
        
#     competitor_asins = list(set(
#         r.get("asin", "") for r in all_results
#         if r.get("asin", "") and r.get("asin")  != parent_asin  # Ensure that the ASIN is a non-empty string and not the same as the parent ASIN
#     ))
    
#     product_details = scrape_multiple_products(competitor_asins[:20], search_geo, search_domain) # Scrape the product details for the competitor ASINs using the scrape_multiple_products function, which can be implemented to take a list of ASINs and fetch their details in bulk. This can help improve the efficiency of fetching competitor information by reducing the number of individual requests needed to fetch details for each competitor ASIN.
#     stored_comps = []
#     for product in product_details:
#         product["parent_asin"] = parent_asin  # Add the parent ASIN to the competitor product data to establish a relationship between the competitor and the parent product in the database. This can help us easily query and analyze competitors based on their relationship to the parent product.
#         db.add_product(product)  # Store the competitor product data in the database using
#         stored_comps.append(product)  # Add the stored competitor product data to the list of stored competitors, which we can then return at the end of the function to provide a list of competitors that were fetched and stored in the database.
#     st.success(f"Fetched and stored {len(stored_comps)} competitors for ASIN: {parent_asin} successfully!")  # Display a success message to the user indicating how many competitors were fetched and stored in the database for the specified parent ASIN.
#     st.write("Competitors summary ")  

#     for comp in stored_comps:
#         price = comp.get("price", "-")
#         currency = comp.get("currency", "-")
#         if isinstance(price, (int, float)) and currency:
#             price_info = f"{price:,.2f} {currency}" if currency else f"{price:,.2f}"
#         else:
#             price_str = str(price) if price is not None else "-"
#             price_info = f"{price_str} {currency}" if currency else price_str
#         st.write(f"ASIN: {comp.get('asin', 'N/A')} | Title: {comp.get('title', 'N/A')} | Price: {price_info} | Domain: amazon.{comp.get('domain', 'N/A')} | Geo: {comp.get('geo', 'N/A')}")
#     st.write("Competitors summary end")
#     st.write("------------------------------------")

        
#     return stored_comps # Return the list of competitors that were fetched and stored in the database for the specified parent ASIN. This allows us to see the competitors that were added to the database as a result of this function call, and we can use this information for further analysis or display in the user interface.