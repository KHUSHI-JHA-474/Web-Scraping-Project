import os
import requests
import csv
from bs4 import BeautifulSoup
from google.cloud import dialogflow_v2 as dialogflow
from google.oauth2 import service_account
import uuid
import time
import web-scraping-project-python-ab3ce8536ba4.json

# Manually set up Google Cloud credentials using the JSON key
credentials = service_account.Credentials.from_service_account_file(
    r'web-scraping-project-python-ab3ce8536ba4.json'
)

# Function to perform Google search and get results
def google_search(query, api_key, cx):
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={api_key}&cx={cx}"
    response = requests.get(url)
    return response.json()

# Function to extract search results
def extract_search_results(search_results):
    results = []
    for item in search_results.get('items', []):
        title = item.get('title')
        link = item.get('link')
        snippet = get_ai_snippet(link)  # Generate AI snippet for the URL
        results.append([title, link, snippet])
    return results

# Function to fetch page content and generate a snippet using Dialogflow
def get_ai_snippet(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = ' '.join([p.get_text() for p in soup.find_all('p')])

        if len(text_content) > 256:
            text_content = text_content[:256]
        if not text_content.strip():
            return "No content available"

        session_id = str(uuid.uuid4())
        client = dialogflow.SessionsClient(credentials=credentials)
        session = client.session_path('web-scraping-project-python', session_id)

        query_input = dialogflow.QueryInput(text=dialogflow.TextInput(text=text_content, language_code='en'))
        response = client.detect_intent(session=session, query_input=query_input)

        return response.query_result.fulfillment_text.strip()
    except Exception as e:
        print(f"Error fetching snippet for {url}: {e}")
        return "No snippet available"

# Function to save results to CSV (append mode)
def save_results_to_csv(results, filename='search_results.csv'):
    file_exists = os.path.isfile(filename)
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Title', 'Link', 'Snippet'])  # Write header
        writer.writerows(results)

# Function to check for duplicate links in the CSV
def is_duplicate(link, filename='search_results.csv'):
    if not os.path.isfile(filename):
        return False
    with open(filename, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        return any(row[1] == link for row in reader if len(row) > 1)

# Continuous scraping process for a single query
def continuous_scraping_for_query():
    API_KEY = 'AIzaSyA6casqB1J7Z6tlOyO2ZtBNzbuG23K8Cg0'
    CX = '00bb95ac6f2c74b94'
    
    search_query = input("Enter search query: ")  # Take query once
    filename = f"search_results_{search_query.replace(' ', '_')}.csv"  # Use query in filename

    print(f"Starting continuous scraping for query: {search_query}")

    while True:
        try:
            search_results = google_search(search_query, API_KEY, CX)
            extracted_results = extract_search_results(search_results)

            # Filter out duplicates before saving
            new_results = [result for result in extracted_results if not is_duplicate(result[1], filename)]

            if new_results:
                save_results_to_csv(new_results, filename)
                print(f"New results saved to '{filename}'")
            else:
                print("No new results to save.")

        except Exception as e:
            print(f"Error during scraping: {e}")

        print("Waiting 2 minutes before the next scrape...")
        time.sleep(120)  # Wait before the next scrape

if __name__ == "__main__":
    continuous_scraping_for_query()
