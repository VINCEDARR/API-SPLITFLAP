import requests
from nltk.sentiment import SentimentIntensityAnalyzer

# API keys (set these in your Vercel dashboard as environment variables)
NEWS_API_KEY = 'E_S4rUOyq3qjk_V-ZNKilvdYEWKNx5FkD-IlyJa3cZNZaIuK'
WEATHER_API_KEY = '7f40d40f66b7851cd4534b53c191eb0f'
AQI_API_KEY = '86c94aa5-a854-4562-955a-3383c0860892'
ALPHA_VANTAGE_API_KEY = '4TN33OOWCHJ4GL6H'

def fetch_latest_news(api_key):
    url = f'https://api.currentsapi.services/v1/latest-news?language=en&apiKey={api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('news', [])
    else:
        return None

def fetch_weather(api_key):
    url = f'https://api.weatherstack.com/current?access_key={api_key}&query=fetch:ip'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('current', {})
    else:
        return None

def fetch_aqi(api_key):
    url = f'https://api.airvisual.com/v2/nearest_city?key={api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('data', {}).get('current', {}).get('pollution', {})
    else:
        return None

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
                change_percent = 0

            if change_percent > 0:
                sentiments = 'POSITIVE'
            elif change_percent < 0:
                sentiments = 'NEGATIVE'
            else:
                sentiments = 'NEUTRAL'
        else:
            sentiments = 'UNKNOWN'
    return sentiments

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

def analyze_weather_sentiment(weather_code):
    if weather_code > 116:
        return "NEGATIVE"
    else:
        return "POSITIVE"

def analyze_aqi_sentiment(aqi_us):
    if aqi_us < 51:
        return "POSITIVE"
    elif 51 <= aqi_us <= 100:
        return "NEUTRAL"
    else:
        return "NEGATIVE"

def determine_overall_sentiment(sentiments):
    sentiment_count = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0, "UNKNOWN": 0}
    if isinstance(sentiments, list):
        for sentiment in sentiments:
            if sentiment != 'UNKNOWN':
                sentiment_count[sentiment] += 1
    overall_sentiment = max(sentiment_count, key=sentiment_count.get)
    return overall_sentiment

# Main handler for Vercel (the function that gets executed)
def handler(req):
    news = fetch_latest_news(NEWS_API_KEY)
    if not news:
        return {'error': 'Unable to fetch news'}, 500
    
    news_results = []
    news_sentiments = []
    for article in news:
        title = article.get('title')
        if title:
            sentiment = analyze_sentiment_vader(title)
            news_sentiments.append(sentiment)
            news_results.append({'title': title, 'sentiment': sentiment})

    overall_news_sentiment = determine_overall_sentiment(news_sentiments)

    weather = fetch_weather(WEATHER_API_KEY)
    if weather:
        weather_code = weather.get('weather_code', 0)
        weather_sentiment = analyze_weather_sentiment(weather_code)
    else:
        weather_sentiment = 'UNKNOWN'
    
    aqi = fetch_aqi(AQI_API_KEY)
    if aqi:
        aqi_us = aqi.get('aqius', 0)
        aqi_sentiment = analyze_aqi_sentiment(aqi_us)
    else:
        aqi_sentiment = 'UNKNOWN'

    stock_sentiments = fetch_stock_market_data(ALPHA_VANTAGE_API_KEY)
    
    all_sentiments = [overall_news_sentiment, stock_sentiments, weather_sentiment, aqi_sentiment]
    master_sentiment = determine_overall_sentiment(all_sentiments)

    response = {
        'news_results': news_results,
        'overall_news_sentiment': overall_news_sentiment,
        'stock_sentiments': stock_sentiments,
        'weather_sentiment': weather_sentiment,
        'aqi_sentiment': aqi_sentiment,
        'master_sentiment': master_sentiment
    }

    return response
