from flask import Flask, jsonify
import requests
from nltk.sentiment import SentimentIntensityAnalyzer

app = Flask(__name__)

NEWS_API_KEY = 'E_S4rUOyq3qjk_V-ZNKilvdYEWKNx5FkD-IlyJa3cZNZaIuK'
WEATHER_API_KEY = '7f40d40f66b7851cd4534b53c191eb0f'
AQI_API_KEY = '86c94aa5-a854-4562-955a-3383c0860892'
ALPHA_VANTAGE_API_KEY = '4TN33OOWCHJ4GL6H'

# Function to fetch the latest news from Currents API
def fetch_latest_news(api_key):
    url = f'https://api.currentsapi.services/v1/latest-news?language=en&apiKey={api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('news', [])
    else:
        print(f"Error fetching news: {response.status_code}, {response.text}")
        return None

# Function to fetch weather data from Weatherstack API
def fetch_weather(api_key):
    url = f'https://api.weatherstack.com/current?access_key={api_key}&query=fetch:ip'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('current', {})
    else:
        print(f"Error fetching weather: {response.status_code}, {response.text}")
        return None

# Function to fetch AQI data from AirVisual API
def fetch_aqi(api_key):
    url = f'https://api.airvisual.com/v2/nearest_city?key={api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('data', {}).get('current', {}).get('pollution', {})
    else:
        print(f"Error fetching AQI: {response.status_code}, {response.text}")
        return None

# Function to fetch MSCI stock market data using Alpha Vantage API
def fetch_stock_market_data(api_key):
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=MSCI&apikey={api_key}'
    response = requests.get(url)
    
    sentiments = {}
    
    if response.status_code == 200:
        data = response.json().get('Global Quote', {})
        if data:
            change_percent_str = data.get('10. change percent', '0%').rstrip('%')
            try:
                change_percent = float(change_percent_str)
            except ValueError:
                change_percent = 0  # Fallback if conversion fails

            if change_percent > 0:
                sentiments = 'POSITIVE'
            elif change_percent < 0:
                sentiments = 'NEGATIVE'
            else:
                sentiments = 'NEUTRAL'
        else:
            sentiments = 'UNKNOWN'
    else:
        print(f"Error fetching MSCI data: {response.status_code}, {response.text}")
        sentiments['MSCI'] = 'UNKNOWN'

    return sentiments

# Sentiment analysis for news using VADER
def analyze_sentiment_vader(text):
    sia = SentimentIntensityAnalyzer()
    scores = sia.polarity_scores(text)
    compound_score = scores['compound']
    if compound_score > 0.05:
        return "POSITIVE"
    elif compound_score < -0.05:
        return "NEGATIVE"
    else:
        return "NEUTRAL"

# Sentiment analysis for weather based on weather code
def analyze_weather_sentiment(weather_code):
    if weather_code > 116:
        return "NEGATIVE"
    else:
        return "POSITIVE"

# Sentiment analysis for AQI based on AQIUS
def analyze_aqi_sentiment(aqi_us):
    if aqi_us < 51:
        return "POSITIVE"
    elif 51 <= aqi_us <= 100:
        return "NEUTRAL"
    else:
        return "NEGATIVE"

# Determine overall sentiment
def determine_overall_sentiment(sentiments):
    sentiment_count = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0, "UNKNOWN": 0}
    if isinstance(sentiments, list):
        for sentiment in sentiments:
            if sentiment != 'UNKNOWN':
                sentiment_count[sentiment] += 1
    else:
        print("Sentiments should be a list.")
    overall_sentiment = max(sentiment_count, key=sentiment_count.get)
    return overall_sentiment

@app.route('/api/analyze', methods=['GET'])
def analyze():
    # Fetch the latest news
    news = fetch_latest_news(NEWS_API_KEY)
    if not news:
        return jsonify({'error': 'Unable to fetch news'}), 500
    
    # Analyze sentiment for each news title
    news_results = []
    news_sentiments = []
    for article in news:
        title = article.get('title')
        if title:
            sentiment = analyze_sentiment_vader(title)
            news_sentiments.append(sentiment)
            news_results.append({'title': title, 'sentiment': sentiment})
    
    # Determine overall news sentiment
    overall_news_sentiment = determine_overall_sentiment(news_sentiments)

    # Fetch and analyze weather sentiment
    weather = fetch_weather(WEATHER_API_KEY)
    if weather:
        weather_code = weather.get('weather_code', 0)
        weather_sentiment = analyze_weather_sentiment(weather_code)
    else:
        weather_sentiment = 'UNKNOWN'
    
    # Fetch and analyze AQI sentiment
    aqi = fetch_aqi(AQI_API_KEY)
    if aqi:
        aqi_us = aqi.get('aqius', 0)
        aqi_sentiment = analyze_aqi_sentiment(aqi_us)
    else:
        aqi_sentiment = 'UNKNOWN'

    # Fetch and analyze stock market sentiment for MSCI
    stock_sentiments = fetch_stock_market_data(ALPHA_VANTAGE_API_KEY)
    
    # Calculate the MASTER_SENTIMENT using determine_overall_sentiment
    all_sentiments = [overall_news_sentiment, stock_sentiments, weather_sentiment, aqi_sentiment]
    master_sentiment = determine_overall_sentiment(all_sentiments)

    # Prepare response in the desired order
    response = jsonify({
        'news_results': news_results,
        'overall_news_sentiment': overall_news_sentiment,
        'stock_sentiments': stock_sentiments,
        'weather_sentiment': weather_sentiment,
        'aqi_sentiment': aqi_sentiment,
        'master_sentiment': master_sentiment
    })

    return response

# Handler for Vercel
if __name__ == '__main__':
    app.run(debug=True, port=5001)
