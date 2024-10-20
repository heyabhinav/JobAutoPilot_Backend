import requests
import pandas as pd
from bs4 import BeautifulSoup
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Ignore tags that you don't want to scrape
ignore_tags = ['script', 'metadata', 'link', 'style', 'svg', 'path']

# Web scraping function
def scrape_web(url: str):
    try:
        # Request the webpage content
        path = requests.get(url)
        soup = BeautifulSoup(path.content, 'html.parser')

        data = []

        # Loop through all tags in the HTML
        for tag in soup.find_all(True):  # True gets all tags
            if tag.name in ignore_tags:
                continue

            # Get class and id attributes
            class_attr = tag.get('class', None)
            id_attr = tag.get('id', None)

            # If both class and id are present
            if class_attr is not None and id_attr is not None:
                text = tag.get_text(strip=True)  # Get the text inside the tag
                data.append({
                    'tag': tag.name,
                    'class': ' '.join(class_attr) if class_attr else None,
                    'id': id_attr,
                    'text': text
                })

        # Convert data to a DataFrame and save to CSV
        df = pd.DataFrame(data)
        csv_filename = 'classAndIdTable.csv'
        df.to_csv(csv_filename, index=False)

        return csv_filename  # Return the filename of the CSV
    except Exception as e:
        return str(e)

# Input model for URL
class URLModel(BaseModel):
    url: str

# Define the FastAPI endpoint
@app.post("/scrape-url/")
async def scrape_url(url_model: URLModel):
    # Call the scraping function
    csv_file = scrape_web(url_model.url)
    
    # Check if it returned a CSV file
    if csv_file.endswith('.csv'):
        return {"message": "Scraping successful, CSV saved!", "csv_file": csv_file}
    else:
        return {"error": csv_file}

# To run the server, use:
# uvicorn filename:app --reload
