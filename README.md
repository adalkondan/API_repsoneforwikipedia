# README.md

## Project Title: Wikipedia Scraper API

A Flask-based application that scrapes content from Wikipedia pages and returns structured data in JSON format.

---

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Usage](#usage)
  - [API Endpoint](#api-endpoint)
  - [Error Handling](#error-handling)
- [Dependencies](#dependencies)
- [How to Run](#how-to-run)

---

## Introduction

This application provides an API endpoint to scrape content from Wikipedia pages. It extracts structured data, including sections, paragraphs, lists, images, and tables, and returns it in a JSON format.

---

## Features

- **Structured Data Extraction**:
  - Hierarchical sections with titles and content.
  - Flat lists of all paragraphs, lists, images, and tables.

- **Image Filtering**:
  - Excludes decorative or small images (e.g., those marked as 'thumbimage' or from '/wikipedia/commons/').

---

## Usage

### API Endpoint
The application exposes an endpoint at `/scrape-wikipedia` that accepts a URL parameter (`url`) specifying the Wikipedia page to scrape.

**Example usage**:
```
GET /scrape-wikipedia?url=https://en.wikipedia.org/wiki/Python_(programming_language)
```

### Error Handling

- **Missing or Invalid URL**: Returns a 400 error with details.
- **Network Issues**: Returns a 500 error if fetching the page fails.

---

## Dependencies

- `Flask`: For serving the web application. Version used: ≥2.0
- `requests`: For making HTTP requests. Version used: ≥2.31
- `beautifulsoup4`: For parsing HTML. Version used: ≥4.11

---

## How to Run

1. Clone the repository and create a virtual environment:
   ```bash
   git clone https://github.com/adalkondan/API_repsoneforwikipedi.git
   cd API_repsoneforwikipedi.git
   pip install -r requirements.txt
   ```

2. Install dependencies as specified in `requirements.txt`.

3. Run the application using Flask:
   ```bash
   python app.py
   ```

4. Visit the API endpoint at `http://localhost:5000/scrape-wikipedia` to test it.

---

## Notes

- The scraper is designed for development and testing purposes.
- Image URLs are normalized by prepending 'https:' if they're protocol-relative.
- All extracted text is cleaned of extra whitespace and empty values before storage.
