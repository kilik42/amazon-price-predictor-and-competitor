from tinydb import TinyDB, Query
from datetime import datetime
import os

class Database:
    def __init__(self, db_path='data.json'):
        dir_path = os.path.dirname(db_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        self.db = TinyDB(db_path)
        self.products_table = self.db.table('products')

    def add_product(self, product_data):
        #product data should be a dictionary with keys: asin, geo, domain, price
        product_data['created_at'] = datetime.now().isoformat()
        self.products_table.insert({
            'asin': product_data['asin'],
            'geo': product_data['geo'],
            'domain': product_data['domain'],
            'price': product_data['price'],
            'timestamp': datetime.now().isoformat()
        })
        return self.db.table('products').all() # Return all products after adding a new one
    
    def get_product(self, asin):
        # Get the latest price information for a product based on its ASIN
        Product = Query() # Create a query object to search for the product by ASIN

        # Assuming that ASIN is unique, we can return the first match. If there are multiple entries for the same ASIN, you may want to implement additional logic to return the most recent one.
        return self.products_table.get(Product.asin == asin)

    def get_all_products(self):
        # Get all products from the database
        return self.products_table.all()
    
    def search_products(self, search_criteria):
        # Search for products based on ASIN, Geo location, and domain
        Product = Query()
        query = None # Initialize query to None, we will build it based on the provided search criteria

        for key, value in search_criteria.items():
            if value:  # Only add to the query if the value is not empty
                if query is None: # If this is the first condition, initialize the query
                    query = (Product[key] == value)
                else: # For subsequent conditions, we need to combine them with the existing query using the & operator
                    query = query & (Product[key] == value)
        
        return self.products_table.search(query) if query is not None else self.get_all_products() or [] # Return all products if no search criteria provided, or an empty list if there are no products in the database

        # # Build the query based on the provided search criteria
        # if asin:
        #     query = (Product.asin == asin) if query is None else (query & (Product.asin == asin))
        # if geo:
        #     query = (Product.geo == geo) if query is None else (query & (Product.geo == geo))
        # if domain:
        #     query = (Product.domain == domain) if query is None else (query & (Product.domain == domain))

        # if query is not None:
        #     return self.products_table.search(query)
        # else:
        #     return self.get_all_products()  # Return all products if no search criteria provided
        
    def update_product_price(self, asin, new_price):
        # Update the price of a product based on its ASIN
        Product = Query()
        self.products_table.update({'price': new_price}, Product.asin == asin)

    def delete_product(self, asin):
        # Delete a product from the database based on its ASIN
        Product = Query()
        self.products_table.remove(Product.asin == asin)