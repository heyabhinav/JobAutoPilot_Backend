import os
import re
import requests
import pandas as pd
import pdfplumber
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Mock user resume directory
RESUME_DIR = 'resumes/'  # The directory where user resumes are stored

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


# Function to extract information from resume
def extract_resume_details(file_path: str):
    with pdfplumber.open(file_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()

    # Regex patterns to extract data
    name_pattern = re.compile(r'(Name|Full Name):?\s*([A-Z][a-z]+\s[A-Z][a-z]+)')
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    phone_pattern = re.compile(r'\b(\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9})\b')
    job_status_pattern = re.compile(r'(Job Status|Employment Status):?\s*(Employed|Unemployed|Freelancing)')
    description_pattern = re.compile(r'(Description|About Me|Summary):?\s*(.*)')

    # Extract information
    name_match = name_pattern.search(text)
    email_match = email_pattern.search(text)
    phone_match = phone_pattern.search(text)
    job_status_match = job_status_pattern.search(text)
    description_match = description_pattern.search(text)

    # Structure the extracted data into a dictionary
    extracted_data = {
        "name": name_match.group(2) if name_match else "Not Found",
        "email": email_match.group(0) if email_match else "Not Found",
        "phone": phone_match.group(0) if phone_match else "Not Found",
        "job_status": job_status_match.group(2) if job_status_match else "Not Found",
        "description": description_match.group(2) if description_match else "Not Found"
    }

    return extracted_data


# Input model for URL
class URLModel(BaseModel):
    url: str


# Input model for user ID
class UserModel(BaseModel):
    user_id: str


# Define the FastAPI endpoint for web scraping
@app.post("/scrape-url/")
async def scrape_url(url_model: URLModel):
    # Call the scraping function
    csv_file = scrape_web(url_model.url)

    # Check if it returned a CSV file
    if csv_file.endswith('.csv'):
        return {"message": "Scraping successful, CSV saved!", "csv_file": csv_file}
    else:
        return {"error": csv_file}


# Endpoint to extract resume details for a user
@app.post("/extract-resume/")
async def extract_resume(user_model: UserModel):
    # Assuming resume files are named by user ID (e.g., 1234_resume.pdf)
    resume_file = os.path.join(RESUME_DIR, f"{user_model.user_id}_resume.pdf")

    # Check if the file exists
    if not os.path.exists(resume_file):
        raise HTTPException(status_code=404, detail="Resume file not found")

    # Extract details from the resume
    extracted_data = extract_resume_details(resume_file)
    
    return extracted_data


# To run the server, use:
# uvicorn filename:app --reload
