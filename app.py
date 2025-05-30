from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# Helper to clean text
def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

@app.route('/scrape-wikipedia', methods=['GET'])
def scrape_wikipedia():
    wikipedia_url = request.args.get('url')

    if not wikipedia_url:
        return jsonify({"error": "Missing 'url' parameter. Please provide a Wikipedia page URL."}), 400

    if "wikipedia.org" not in wikipedia_url:
        return jsonify({"error": "Invalid URL. Only Wikipedia URLs are supported."}), 400

    try:
        response = requests.get(wikipedia_url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch page: {e}"}), 500

    soup = BeautifulSoup(response.content, 'lxml')

    # --- Extract Page Title ---
    page_title_tag = soup.find('h1', id='firstHeading')
    page_title = clean_text(page_title_tag.get_text()) if page_title_tag else "Title Not Found"

    # --- Extract Main Content Area ---
    # Wikipedia content is typically within the div with id 'bodyContent' or 'mw-content-text'
    content_div = soup.find('div', id='mw-content-text')
    if not content_div:
        return jsonify({"error": "Could not find main content div on the page."}), 500

    # Initialize structures for output
    sections_data = []
    paragraphs_data = []
    lists_data = []
    images_data = []
    tables_data = []

    # --- Extract Paragraphs, Lists, and Images (Flat) ---
    # Iterate over common content elements within the main content div
    for element in content_div.find_all(['p', 'ul', 'ol', 'img', 'table']):
        if element.name == 'p':
            paragraph_text = clean_text(element.get_text())
            if paragraph_text: # Avoid adding empty paragraphs
                paragraphs_data.append(paragraph_text)
        elif element.name in ['ul', 'ol']:
            list_items = [clean_text(li.get_text()) for li in element.find_all('li') if clean_text(li.get_text())]
            if list_items:
                lists_data.append({
                    "list_type": element.name,
                    "items": list_items
                })
        elif element.name == 'img':
            if 'src' in element.attrs:
                img_url = element['src']
                # Prepend 'https:' if the URL is protocol-relative
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                alt_text = element.get('alt', '')
                # Filter out small or decorative images by common Wikipedia classes
                if 'thumbimage' in element.get('class', []) or '/wikipedia/commons/' in img_url:
                    images_data.append({
                        "url": img_url,
                        "alt_text": clean_text(alt_text)
                    })
        elif element.name == 'table':
            table_rows = []
            for row in element.find_all('tr'):
                row_cells = []
                for cell in row.find_all(['th', 'td']):
                    row_cells.append(clean_text(cell.get_text()))
                if row_cells: # Only add non-empty rows
                    table_rows.append(row_cells)
            if table_rows:
                tables_data.append(table_rows)


    # --- Extract Sections/Headings (Hierarchical) ---
    # This part requires more careful traversal to link content to its section.
    # We'll use a more robust approach here.
    # Collect all headings and significant content tags
    elements_to_process = content_div.find_all(lambda tag: tag.name.startswith('h') and tag.name[1].isdigit() or tag.name in ['p', 'ul', 'ol', 'table', 'figure', 'dl'])

    current_section_stack = [] # To manage hierarchy

    for element in elements_to_process:
        if element.name.startswith('h') and element.name[1].isdigit():
            level = int(element.name[1])
            heading_span = element.find('span', class_='mw-headline')
            section_title = clean_text(heading_span.get_text()) if heading_span else clean_text(element.get_text())
            if not section_title: # Skip empty headings
                continue

            new_section = {
                "title": section_title,
                "level": level,
                "content": [],
                "subsections": []
            }

            # Adjust stack based on new section's level
            while current_section_stack and current_section_stack[-1]['level'] >= level:
                current_section_stack.pop()

            if current_section_stack:
                current_section_stack[-1]['subsections'].append(new_section)
            else:
                sections_data.append(new_section)
            current_section_stack.append(new_section)

        elif current_section_stack: # Add content to the current active section
            content_item = None
            if element.name == 'p':
                text = clean_text(element.get_text())
                if text: content_item = {"type": "paragraph", "text": text}
            elif element.name in ['ul', 'ol']:
                list_items = [clean_text(li.get_text()) for li in element.find_all('li') if clean_text(li.get_text())]
                if list_items: content_item = {"type": "list", "list_type": element.name, "items": list_items}
            elif element.name == 'table':
                table_rows = []
                for row in element.find_all('tr'):
                    row_cells = []
                    for cell in row.find_all(['th', 'td']):
                        row_cells.append(clean_text(cell.get_text()))
                    if row_cells: table_rows.append(row_cells)
                if table_rows: content_item = {"type": "table", "data": table_rows}
            elif element.name == 'figure' and element.find('img'): # For images wrapped in <figure>
                 img_tag = element.find('img')
                 img_url = img_tag['src'] if 'src' in img_tag.attrs else ''
                 if img_url.startswith('//'): img_url = 'https:' + img_url
                 alt_text = img_tag.get('alt', '')
                 if 'thumbimage' in img_tag.get('class', []) or '/wikipedia/commons/' in img_url:
                     content_item = {"type": "image", "url": img_url, "alt_text": clean_text(alt_text)}
            elif element.name == 'dl': # Handle description lists (often used for definitions)
                dl_items = []
                for dt in element.find_all('dt'):
                    dd = dt.find_next_sibling('dd')
                    if dd:
                        dl_items.append({"term": clean_text(dt.get_text()), "description": clean_text(dd.get_text())})
                if dl_items: content_item = {"type": "description_list", "items": dl_items}

            if content_item:
                current_section_stack[-1]['content'].append(content_item)


    # Final JSON structure
    scraped_data = {
        "page_title": page_title,
        "sections": sections_data, # Hierarchical sections are generally more useful
        "all_paragraphs": paragraphs_data, # Flat list for convenience
        "all_lists": lists_data, # Flat list for convenience
        "all_images": images_data, # Flat list for convenience
        "all_tables": tables_data # Flat list for convenience
    }

    return jsonify(scraped_data)

if __name__ == '__main__':
    # You can run this directly using: python app.py
    # For production, use a WSGI server like Gunicorn or uWSGI
    app.run(debug=True) # debug=True enables auto-reloading and better error messages