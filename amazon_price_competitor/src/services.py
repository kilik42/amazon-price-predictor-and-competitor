#connect to database

import streamlit as st

from src.db import Database
from src.oxylabs_client import scrape_product_details

def scrape_and_store_product(asin, geo=None, domain=None):
    # This function is responsible for scraping the product details using the scrape_product_details function and then storing the scraped data in the database using the Database class. It takes the ASIN, Geo location, and domain as input parameters, scrapes the product details, and then adds the product data to the database.
    data = scrape_product_details(asin, geo, domain)  # Scrape the product details using the provided ASIN, Geo location, and domaind
    db = Database()  # Create an instance of the Database class to interact with the database
    db.add_product(data)  # Insert the scraped product data into the database using the add_product method of the Database class
    st.success("Product details scraped and stored successfully!")  # Display a success message to the user indicating that the product details have been scraped and stored successfully in the database
    return data # Return all products from the database after adding the new product, this allows us to see the updated list of products in the database after the new product has been added.

