from itertools import product

import streamlit as st  
from src.oxylabs_client import scrape_product_details
from src.db import Database

def render_header():
    st.title("Amazon Price Competitor")
    st.write("Welcome to the Amazon Price Competitor app! This application allows you to track and compare prices of products on Amazon. You can enter the product ASIN and our app will fetch the current price and compare it with historical data to help you make informed purchasing decisions.")
    st.caption("Please enter the Amazon product ASIN # to get started.")


def render_inputs():
    asin = st.text_input("Enter the Amazon product ASIN #:", placeholder="B08N5WRWNW")
    if asin:
        st.write(f"You entered: {asin}")
        # Here you can add the logic to fetch and display the price information based on the ASIN or URL provided.
    geo = st.text_input("Enter the zip code  (optional):", placeholder="e.g., 60601 or leave blank")
    if geo:
        st.write(f"You entered Geo location: {geo}")
        # Here you can add the logic to fetch and display price information based on the Geo location provided.
    domain  = st.selectbox("Select the Amazon domain:", options=["amazon.com", "amazon.co.uk", "amazon.de", "amazon.fr", "amazon.it"])
    st.write(f"You selected domain: {domain}")
    # Here you can add the logic to fetch and display price information based on the selected domain
    return asin.strip() if asin else "", geo.strip() if geo else "", domain.strip() if domain else ""

def main():
    st.set_page_config(page_title="Amazon Price Competitor", page_icon=":money_with_wings:", layout="centered")
    render_header()
    asin, geo, domain = render_inputs()
    # Here you can add the logic to fetch and display price information based on the ASIN, Geo location, and domain provided by the user.
    if not asin:
            st.error("Please enter a valid ASIN to fetch price information.")
            return
    if st.button("scrape product"):
        if not asin:
            st.error("Please enter a valid ASIN to fetch price information.")
            return

        with st.spinner("Fetching price information..."):
            product_details = scrape_product_details(asin, geo, domain)

        if product_details:
            st.success("Product details fetched successfully!")
            st.json(product_details)

            db = Database()
            db.add_product(product_details)
        else:
            st.error("Failed to fetch product details. Please check the ASIN and try again.")
    # elif st.button("scrape product") and not asin:
    #     st.error("Please enter a valid ASIN to fetch price information.")
def render_product_card(self, product):
        with st.container(border=True, padding=10):
            cols = st.columns([1,2])
            # Display product image in the first column
            try:
                images = product.get('images', [])
                if images and len(images) >0:
                    cols[0].image(images[0], width=150)
                else:
                    cols[0].write("No image available")
            except Exception as e:
                cols[0].write("Error loading image")

            # Display product information in the second column
            with cols[1]:
                st.subheader(product.get('title', 'No title available') or product["asin"])
                info_cols = st.columns(3)
                currency = product.get('currency', '')
                price = product.get('price', "-")
                info_cols[0].metric("price", f"{price} {currency}" if currency else price)
                info_cols[1].write(f"Brand: {product.get('brand', 'N/A')}")
                info_cols[2].write(f"Product: {product.get('product_overview', 'N/A')}")
                # st.write(f"URL: {product.get('url', 'N/A')}")   
                domain_info = f"amazon.{product.get('domain', 'N/A')}" if product.get('domain') else "N/A"
                geo_info = product.get('geo', 'N/A')
                st.caption(f"Domain: {domain_info} | Geo: {geo_info}")
                st.write(product.get("url", "N/A"))

                if st.button("start analyzing competitors", key=f"analyze_{product['asin']}"):
                    st.session_state["analyzing_asin"] = product['asin']
                    st.write("Analyzing competitors... (This is a placeholder for the actual competitor analysis logic)")
                

        
if __name__ == "__main__":
    main()