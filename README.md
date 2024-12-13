AirBnB Explorer
App Link https://airbnb-final.streamlit.app

Introduction to the App

The Airbnb Data Viewer serves as an interactive tool for users to explore insights into Airbnb listings. It is particularly focused on helping two main audiences: buyers seeking suitable properties and sellers (hosts) aiming to optimize their listings for better customer satisfaction and ratings.

The app offers the following features:

Data Exploration: Users can explore Airbnb data to identify trends in ratings, prices, locations, and property types. It includes visualization features, such as interactive maps, to highlight the geographic distribution of properties.

Buyer-Focused Insights: Buyers can filter properties based on criteria such as minimum review ratings, price limits, property type, and the number of bedrooms. Results are presented in an easy-to-understand table format and plotted on an interactive map.

Seller-Focused Predictions: Hosts can input property details, such as accommodations, amenities, and neighborhood descriptions, to predict a potential review score for their listings. The prediction leverages a trained linear regression model that uses features such as the sentiment of the neighborhood overview and property details to estimate the likely review score.

Tools Used:

1. Streamlit: For building an interactive web application with UI elements and navigation.

2. Pandas: For data manipulation and analysis, including loading CSV data.

3. Pydeck: For creating interactive map visualizations.

4. VADER Sentiment Analysis: To analyze textual sentiments for review-related features.

5. Scikit-learn: For machine learning, including Linear Regression modeling and feature scaling.

6. Pickle: To load pre-trained models and scalers.

7. Backblaze B2 SDK: For fetching data stored in a cloud bucket.

8. Dotenv: For securely managing environment variables like API keys.

9. OS and Sys Modules: For handling file paths and modifying the Python path.

10. Streamlit Cache: For optimizing performance by caching fetched data.

Data Description: Our app runs based on the dataset we got from InsideAirbnb: https://insideairbnb.com/get-the-data
We focused listing data only in Austin, TX.
The dataset includes columns like neighborhood overview, latitude and longitude, property type, room type, price, rating scores, etc. For more detailed description on columns, please refer to the link provided and choose Austin, TX.
For app's buyer page, we used rating scores, price, property types, bedrooms, lat and long columns for users to explore listings.
On the other hand, users looking to sell/rent properties in the area can use inputs like accommodates, neighborhood overview, price, amenities offered, etc. to get a predicted rating score for their property.

Algorithm Description:

1.) Loading Data The data is first fetched via the fetch_data function, this retrieves the data from a Backblaze Bucket. Within app.py, the fetch_data function uses credentials (stored in streamlit secrets) to connect to backblaze via the B2 class in the utils folder. The file is retrieved from backblaze, and pandas are used to load it into a data frame.

2.) Cleaning and Processing Data In modeling_sentiment, the load_and_preprocess_data function removes rows with missing values. It also performs sentiment analysis on the text within the neighborhood_overview, host_neighborhood, and amenities columns, sentiment scores are then made into their own column. The other features (accommodates, bathrooms, bedrooms, beds, and price) are then prepped for modeling. The property type column is one-hot encoded so that the model can view property types as a binary indicator and not raw text.

3.) Model Training and Loading The train_and_save model function facilitates the model building process. This function will load the processed data and separate it into features (X) and the target (Y), which is review_scores_rating. This function will scale the features using standard scalar to ensure variables with different scales do not disproportionately affect the model. The model is then trained using a LinearRegression model on the scaled features to predict a user’s potential review_scores_rating. After the training, the model is then saved into model.pickle so that we can load a pre-trained and ready to use model into our app.

The app.py file, upon running, will invoke load_model from modeling_sentiment.py. The load_model function will do two things, one, check whether model.pickle exists and, two, load the stored model, scalar, and expected feature list into memory.

4.) Predicting Review Scores In the seller page, we will find the predictive functionality of our app. A potential AirBnB seller will input information about their potential listing into out app, these things include numeric features like accommodates, bathrooms, bedrooms, beds, and price. It will also include text descriptions of the neighborhood and amenities, there will also be a categorical entry for property type. Texts fields are passed through the SentimentIntensityAnalyzer again to produce new sentiment scores for the user’s inputs. These scores as well as all the other features are combined into a single data record and scaled before using it to predict. With the processed, scaled data the app calls the trained model’s predict method to calculate the estimated review score for the user.

Ethical Concerns

Reinforcing Inequality

If our model tends to predict higher scores for listings already likely to perform well, well-off neighborhoods, it might guide hosts towards conforming to certain market norms. This could discourage diversity in listings and possibly exaggerate existing negative sentiment towards certain neighborhoods and places.

Misuse of Insights

Hosts could use our predicted scores to manipulate their descriptions into being more sentiment favorable but misleading to get a higher review rating on their listing. Given this model is accurate, larger companies can use these predictions to dominate certain areas, leading to higher prices and less diversity
