from cmath import asin
from itertools import product

import streamlit as st  
from src.oxylabs_client import scrape_product_details, search_competitors
from src.db import Database
from src.services import fetch_and_store_competitors,  scrape_and_store_product , generate_competitor_summary

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


# def render_product_card(product,idx):
#         with st.container(border=True):
#             cols = st.columns([1,2])
#             # Display product image in the first column
#             try:
#                 images = product.get('images', [])
#                 if images and len(images) >0:
#                     cols[0].image(images[0], width=150)
#                 else:
#                     cols[0].write("No image available")
#             except Exception as e:
#                 cols[0].write("Error loading image")

#             # Display product information in the second column
#             with cols[1]:
#                 st.subheader(product.get('title', 'No title available') or product["asin"])
#                 info_cols = st.columns(3)
#                 currency = product.get('currency', '')
#                 price = product.get('price', "-")
#                 info_cols[0].metric("price", f"{price} {currency}" if currency else price)
#                 info_cols[1].write(f"Brand: {product.get('brand', 'N/A')}")
#                 info_cols[2].write(f"Product: {product.get('product_overview', 'N/A')}")
#                 # st.write(f"URL: {product.get('url', 'N/A')}")   
#                 domain_info = f"amazon.{product.get('domain', 'N/A')}" if product.get('domain') else "N/A"
#                 geo_info = product.get('geo', 'N/A')
#                 st.caption(f"Domain: {domain_info} | Geo: {geo_info}")
#                 st.write(product.get("url", "N/A"))

#                 if st.button("start analyzing competitors", key=f"analyze_{product.get('asin', 'unknown')}_{idx}"):
#                     st.session_state["analyzing_asin"] = product.get("asin")
#                     st.write("Analyzing competitors... (This is a placeholder for the actual competitor analysis logic)")
def render_product_card(product, idx):
    with st.container(border=True):
        cols = st.columns([1, 2])

        images = product.get("images", [])
        if images:
            cols[0].image(images[0], width=150)
        else:
            cols[0].write("No image available")

        with cols[1]:
            title = product.get("title") or product.get("asin", "No title available")
            st.subheader(title)

            info_cols = st.columns(3)
            currency = product.get("currency", "")
            price = product.get("price", "-")
            info_cols[0].metric("Price", f"{price} {currency}" if currency else price)
            info_cols[1].write(f"Brand: {product.get('brand', 'N/A')}")
            info_cols[2].write(f"Product: {product.get('product_overview', 'N/A')}")

            domain_value = product.get("amazon_domain") or product.get("domain") or "N/A"
            geo_value = product.get("geo_location") or product.get("geo") or "N/A"
            st.caption(f"Domain: {domain_value} | Geo: {geo_value}")

            if product.get("url"):
                st.write(product["url"])

            if st.button(
                "start analyzing competitors",
                key=f"analyze_{product.get('asin', 'unknown')}_{idx}"
            ):
                st.session_state["analyzing_asin"] = product.get("asin")


def main():
    st.set_page_config(page_title="Amazon Price Competitor", page_icon=":money_with_wings:", layout="centered")
    render_header()
    asin, geo, domain = render_inputs()
    # Here you can add the logic to fetch and display price information based on the ASIN, Geo location, and domain provided by the user.
    if not asin:
            st.error("Please enter a valid ASIN to fetch price information.")
            return
      # Scrape button
    if st.button("Scrape Product..."):
        if not asin:
            st.error("Please enter a valid ASIN to fetch price information.")
            return

        with st.spinner("Fetching price information..."):
            scrape_and_store_product(asin, geo, None)

    db = Database()

    if asin:
        products = db.search_products({"asin": asin})
    else:
        products = db.get_all_products()

    products = sorted(
        products,
        key=lambda p: p.get("timestamp", ""),
        reverse=True
    )

    if products:
        st.divider()
        st.subheader("Products Scraped:")

        items_per_page = 10
        total_pages = (len(products) + items_per_page - 1) // items_per_page

        col1, col2, col3 = st.columns([2,3,2])

        with col2:
            page = st.number_input(
                "Page",
                min_value=1,
                max_value=total_pages,
                value=1
            ) - 1

        start_index = page * items_per_page
        end_index = min(start_index + items_per_page, len(products))

        st.write(f"Showing products {start_index + 1} to {end_index} of {len(products)}")

        for idx, product in enumerate(products[start_index:end_index], start=start_index):
            render_product_card(product, idx)
        # else:
        #     st.error("Failed to fetch product details. Please check the ASIN and try again.")
    # elif st.button("scrape product") and not asin:
    #     st.error("Please enter a valid ASIN to fetch price information.")
    selected_asin = st.session_state.get("analyzing_asin")
    if selected_asin:
        st.divider()
        st.subheader(f"Analyzing competitors for ASIN: {selected_asin}")
        db = Database()
        existing_competitors = db.search_products({"parent_asin": selected_asin})
        if not existing_competitors:
            with st.spinner("Fetching and analyzing competitors..."):
                competitors = fetch_and_store_competitors(selected_asin, geo, domain)  # This function will fetch and store competitor information in the database, and return the list of competitors that were fetched and stored.
            st.success(f"Found {len(competitors)} competitors for ASIN: {selected_asin} successfully!")
        else:
            st.info(f"Found {len(existing_competitors)} competitors for ASIN: {selected_asin} in the database. Displaying existing competitors.")
        
        col1, col2 = st.columns([3,1])
        with col2:
            if st.button("Refresh Competitors"):
                with st.spinner("Refreshing competitors..."):
                    competitors = fetch_and_store_competitors(selected_asin, geo, domain)  # This function will fetch and store competitor information in the database, and return the list of competitors that were fetched and stored.
                st.success(f"Refreshed competitors for ASIN: {selected_asin} successfully!")
                existing_competitors = db.search_products({"parent_asin": selected_asin})  # Fetch the updated list of competitors from the database after refreshing.
        with col1:
            if st.button("Analyze with LLM", type="primary"):
                with st.spinner("Analyzing competitors with LLM..."):
                    competitors = db.search_products({"parent_asin": selected_asin})

                    summary = generate_competitor_summary(competitors)

                    st.subheader("Competitor Insights")

                    for line in summary:
                        st.markdown(line)
                    
                    # ----------------------------------
                    # SHOW COMPETITOR LIST
                    # ----------------------------------

                    st.subheader("Competitor Products")

                    for comp in competitors:
                        title = comp.get("title", "Unknown product")
                        price = comp.get("price", "-")
                        brand = comp.get("brand", "Unknown")
                        asin = comp.get("asin")

                        st.markdown(f"""
                    • **{title}**  
                    - Brand: {brand}  
                    - Price: {price}  
                    - ASIN: {asin}
                    """)
                    # Here you can add the logic to analyze the competitors using a language model (LLM) or any other analysis method you prefer.
                    st.write("Analyzing competitors... (This is a placeholder for the actual competitor analysis logic)")
                    # For example, you could call a function like analyze_competitors_with_llm(existing_competitors) and display the results.
        
if __name__ == "__main__":
    main()