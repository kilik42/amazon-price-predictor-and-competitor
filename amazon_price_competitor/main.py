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
    geo = st.text_input("Enter the Geo location (optional):", placeholder="e.g., US, UK, DE")
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

        
if __name__ == "__main__":
    main()