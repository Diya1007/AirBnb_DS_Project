import os
import pandas as pd
import streamlit as st
import pydeck as pdk
import pickle
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from utils.modeling_sentiment import encode_property_type, load_model
import sys
from utils.b2 import B2
from dotenv import load_dotenv
from io import BytesIO
from utils.basic_clean import *

# Set the page config for a wide layout
st.set_page_config(page_title="Airbnb Data Viewer", layout="wide", initial_sidebar_state="expanded")

# Add the utils to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'utils')))


# Load Backblaze from Streamlit Secrets
endpoint = os.getenv("B2_ENDPOINT")  
key_id = os.getenv("B2_KEYID")
app_key = os.getenv("B2_APPKEY")
bucket_name = os.getenv("B2_BUCKETNAME")

# Set up Backblaze connection
b2 = B2(
    endpoint=endpoint,
    key_id=key_id,
    secret_key=app_key
)

@st.cache_data 
def fetch_data():
    try:
        b2.set_bucket(os.getenv('B2_BUCKETNAME'))  
        obj = b2.get_object('Cleaned_Austin_AirBnB.xlsx')  #Exact Name of File

        # Convert the StreamingBody object to a BytesIO object
        # Done to combat Error
        file_content = obj.read()  # Read the content of the StreamingBody
        return pd.read_excel(BytesIO(file_content))  # Use BytesIO to create a file-like object
    except Exception as e:
        st.error(f"Error fetching data from Backblaze: {e}")
        return None


def get_sentiment_score(text, analyzer):
    """Utility function to get sentiment score using SentimentIntensityAnalyzer."""
    if text:
        sentiment = analyzer.polarity_scores(text)
        return sentiment['compound']
    return 0 # Default sentiment score if text is missing

# Load trained model from pickle file
try:
    model, scaler, expected_features = load_model()
except FileNotFoundError:
    st.error("Model file not found. Please add the trained model.pickle.")
    st.stop()

# Streamlit UI
# Initialize session state variables
if 'page' not in st.session_state:
    st.session_state.page = "Main"

if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# Main application function
def main():
    # CSS styling
    st.markdown("""
        <style>
            body {
                font-family: 'Arial', sans-serif;
                background-color: #f4f4f9;
            }
            .title {
                font-size: 3rem;
                font-weight: bold;
                color: #F0000B;
                text-align: center;
                margin-top: 40px;
            }
            .sub-title {
                font-size: 2rem;
                color: #333;
            }
            .markdown-text {
                font-size: 1.1rem;
                line-height: 1.6;
                color: #555;
            }
            .stButton>button {
                background-color: #007BFF;
                color: white;
                font-weight: bold;
                border-radius: 12px;
                padding: 10px 20px;
            }
            .stButton>button:hover {
                background-color: #006FCE;
            }
            .sidebar .sidebar-content {
                background-color: #2F4F4F;
                color: white;
            }
            .stSidebar .sidebar-content .element-container {
                color: white;
            }
            .footer {
                background-color: #007BFF;
                padding: 10px;
                color: white;
                text-align: center;
                font-size: 14px;
            }
        </style>
    """, unsafe_allow_html=True)

    # Title Section with custom color
    st.markdown('<h1 class="title">Airbnb Explorer</h1>', unsafe_allow_html=True)

    # Navigation
    navigation = st.sidebar.selectbox("Navigate", ["Main", "Buyer Page", "Seller Page"])

    # Fetch data
    data = fetch_data()

    # Main Page Content with Tabs
    if navigation == "Main":
        st.header("Welcome to the Airbnb Data Explorer")

        # Tab system
        tab = st.selectbox("Select a section", ["Introduction", "Goals and Approach", "Data Preview"])

        if tab == "Introduction":
            st.markdown('<p class="sub-title">Introduction</p>', unsafe_allow_html=True)
            st.markdown("""
            <p class="markdown-text">Using our app, we aim to uncover insights into what makes an Airbnb listing successful.
            The Airbnb Data Viewer serves as an interactive tool for users to explore insights into Airbnb listings. 
            It is particularly focused on helping two main audiences: buyers seeking suitable properties and sellers (hosts) aiming to optimize their listings for better customer satisfaction and ratings.</p>
            """, unsafe_allow_html=True)

        elif tab == "Goals and Approach":
            st.markdown('<p class="sub-title">Our Goals and Approach</p>', unsafe_allow_html=True)
            st.markdown("""
            <p class="markdown-text">
            Our Goals:
            
            - Understand the factors that lead to higher ratings and greater foot traffic.
            
            - Explore the influence of location and neighborhoods on reviews and ratings.
            
            - Identify specific amenities that contribute to higher reviews.
            
            - Evaluate if pricing strategies impact success.

            Our Approach:
            - Compare locations and neighborhoods to identify "hotspots" that are favored by users.
            
            - Assess the role of amenities in improving customer satisfaction.
            
            - Analyze price ranges to find the "sweet spot" that attracts the most guests.
            </p>
            """, unsafe_allow_html=True)

        elif tab == "Data Preview":
            if data is not None and 'id' in data.columns:
                # Convert 'id' to integer, then keep only the first five digits
                data['id'] = data['id'].apply(lambda x: str(int(float(x)))[:5])

            # Display data on the main page
            if data is not None:
                st.write("Data loaded successfully.")
                st.dataframe(data.head())
            else:
                st.write("Failed to load data.")

    # Buyer Page
    elif navigation == "Buyer Page" and data is not None:
        st.header("Buyer Page")

       
        rating_input = st.number_input("Minimum Review Rating", min_value=0.0, max_value=5.0, value=3.0, step=0.1)
        price_input = st.number_input("Maximum Price ($)", min_value=0, value=500)

        try:

            if price_input == 0:
                raise ValueError("Price cannot be 0. Please enter a valid price.")
            if price_input > 12000:
                st.error("Maximum Property Price is 12000.")
                price_input = 12000  
                st.empty()
        except ValueError as e:
            st.error(e)
        unique_property_types = (
            ["Any"] + sorted(data['property_type'].dropna().unique().tolist()) 
            if 'property_type' in data.columns else ["Any"]
        )
        selected_property_type = st.selectbox("Property Type", options=unique_property_types)

        unique_bedrooms = (
            sorted(data['bedrooms'].dropna().unique()) 
            if 'bedrooms' in data.columns else []
        )
        selected_bedrooms = st.selectbox("Number of Bedrooms", options=unique_bedrooms)

        search_button = st.button("Search")

        if search_button:
            st.empty()
            filtered_data = data.copy()

            # Filter by rating
            if 'review_scores_rating' in filtered_data.columns:
                filtered_data = filtered_data[filtered_data['review_scores_rating'] >= rating_input]

            # Filter by property type
            if selected_property_type != "Any" and 'property_type' in filtered_data.columns:
                filtered_data = filtered_data[filtered_data['property_type'] == selected_property_type]

            # Filter by price
            if 'price' in filtered_data.columns:
                filtered_data = filtered_data[filtered_data['price'] <= price_input]

            # Filter by bedrooms
            if 'bedrooms' in filtered_data.columns:
                filtered_data = filtered_data[filtered_data['bedrooms'] == selected_bedrooms]

            # Display filtered data
            if len(filtered_data) > 0:
                st.write(f"Found {len(filtered_data)} properties based on your search criteria.")
                st.dataframe(filtered_data[['review_scores_rating', 'name', 'listing_url', 'price', 'bedrooms']])

                # Render map
                if 'latitude' in filtered_data.columns and 'longitude' in filtered_data.columns:
                    filtered_data = filtered_data.dropna(subset=['latitude', 'longitude'])
                    deck = pdk.Deck(
                        map_style='mapbox://styles/mapbox/streets-v11',
                        initial_view_state=pdk.ViewState(
                            latitude=filtered_data['latitude'].mean(),
                            longitude=filtered_data['longitude'].mean(),
                            zoom=10,
                            pitch=50,
                        ),
                        layers=[pdk.Layer(
                            'ScatterplotLayer',
                            data=filtered_data,
                            get_position='[longitude, latitude]',
                            get_color='[200, 30, 0, 160]',
                            get_radius=200,
                            pickable=True
                        )],
                        tooltip={
                            "html": "<b>Listing Name:</b> {name}<br/><b>Price:</b> {price}<br/><b>Review Score:</b> {review_scores_rating}",
                            "style": {"backgroundColor": "steelblue", "color": "white"}
                        }
                    )
                    st.pydeck_chart(deck)
                else:
                    st.error("Latitude and longitude columns are missing or invalid.")
            else:
                st.write("No properties match your search criteria.")

    # Seller Page
    elif navigation == "Seller Page":
        st.header("Seller Page")

        # User inputs for prediction
        st.markdown("<h2 style='font-size: 18px;'>Accommodates</h2>", unsafe_allow_html=True)
        accommodates = st.number_input("", min_value=1, step=1,max_value = 500, label_visibility="collapsed")
        # accommodates = st.number_input("Accommodates", min_value=1, step=1, max_value = 500)

        st.markdown("<h2 style='font-size: 18px;'>Bathrooms</h2>", unsafe_allow_html=True)
        bathrooms = st.number_input("", min_value=0.5, step=0.5, max_value=100.0, label_visibility="collapsed")
        # bathrooms = st.number_input("Bathrooms", min_value=0.5, step=0.5, max_value=100.0)

        st.markdown("<h2 style='font-size: 18px;'>Bedrooms</h2>", unsafe_allow_html=True)
        bedrooms = st.number_input("", min_value=1, step=1, max_value=100, label_visibility="collapsed")
        # bedrooms = st.number_input("Bedrooms", min_value=1, step=1, max_value= 100)

        st.markdown("<h2 style='font-size: 18px;'>Beds</h2>", unsafe_allow_html=True)
        beds = st.number_input("", min_value=1, step=1, max_value = 500, label_visibility="collapsed",key="beds_input")
        # beds = st.number_input("Beds", min_value=1, step=1, max_value = 500)

        st.markdown("<h2 style='font-size: 18px;'>Price</h2>", unsafe_allow_html=True)
        price = st.number_input("", min_value=10, step=1, label_visibility="collapsed")
        # price = st.number_input("Price (USD)", min_value=10, step=1)

        st.markdown("<h2 style='font-size: 18px;'>Host Neighborhood</h2>", unsafe_allow_html=True)
        neighborhood_overview = st.text_area("", placeholder="Describe the host neighborhood...")
        # neighborhood_overview = st.text_area("Neighborhood Overview")

        st.markdown("<h2 style='font-size: 18px;'>Neighborhood Overview</h2>", unsafe_allow_html=True)
        host_neighborhood = st.text_area("", placeholder="Provide neighborhood name..")
        # host_neighborhood = st.text_area("Host Neighborhood")

        st.markdown("<h2 style='font-size: 18px;'>Amenities</h2>", unsafe_allow_html=True)
        amenities = st.text_area("", placeholder="Provide available amenities..")
        # amenities = st.text_area("Amenities")

        st.markdown("<h2 style='font-size: 18px;'>Property Type</h2>", unsafe_allow_html=True)
        property_type = st.selectbox("", ["Apartment", "House", "Condo", "Unknown"])
        # property_type = st.selectbox("Property Type", ["Apartment", "House", "Condo", "unknown"])

        # Sentiment Analysis
        analyzer = SentimentIntensityAnalyzer()
        neighborhood_sentiment = get_sentiment_score(neighborhood_overview, analyzer)
        host_neighborhood_sentiment = get_sentiment_score(host_neighborhood, analyzer)
        amenities_sentiment = get_sentiment_score(amenities, analyzer)

        # Prepare input data for prediction
        input_data = pd.DataFrame({
            'accommodates': [accommodates],
            'bathrooms': [bathrooms],
            'bedrooms': [bedrooms],
            'beds': [beds],
            'price': [price],
            'neighborhood_sentiment': [neighborhood_sentiment],
            'host_neighbourhood_sentiment': [host_neighborhood_sentiment],
            'amenities_sentiment': [amenities_sentiment],
            'property_type': [property_type]
        })

        # One-hot encode 'property_type'
        input_data_encoded = encode_property_type(input_data)

        # Ensure the input data has all columns expected by the model
        for missing_feature in expected_features:
            if missing_feature not in input_data_encoded.columns:
                if 'property_type' in missing_feature:
                    # Add missing property type columns with a default value of 0
                    input_data_encoded[missing_feature] = 0
                else:
                    # Add missing numerical features with a default value of 0
                    input_data_encoded[missing_feature] = 0

        # Reorder columns to match the expected features
        input_data_encoded = input_data_encoded[expected_features]

        # Add button to submit input data
        if st.button("Predict Review Score"):
            # Standardize features
            try:
                input_data_scaled = scaler.transform(input_data_encoded)
            except ValueError as e:
                st.error(f"Error during feature scaling: {e}")
                st.stop()

            # Make prediction
            predicted_score = model.predict(input_data_scaled)[0]

            st.subheader("Predicted Review Score")
            # st.write(f"The predicted review score for your listing is: {predicted_score:.2f}")
            st.markdown(f"<h2 style='font-size: 36px; color: #FF5733; font-weight: bold;'>The predicted review score for your listing is: {predicted_score:.2f}</h2>", 
    unsafe_allow_html=True)
            
             # Footer
    st.markdown("""
        <div class="footer">
            <p>Made by Nathan, Parth, Diya & Arsh | 2024</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
