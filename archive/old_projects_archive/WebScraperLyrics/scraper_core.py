# scraper_core.py

import requests
from bs4 import BeautifulSoup
import json
import os
import re

# --- Configuration ---
HEADERS = {
    # It's polite to provide a user-agent to identify your scraper
    'User-Agent': 'ArcadeLyricScraper/1.0 (Contact: user@example.com - for personal use only)'
}
# BASE_LYRIC_URL is used to complete relative links found in the search results
BASE_LYRIC_URL = "https://www.azlyrics.com"
DATA_DIR = "music_library"

# --- Data Persistence (Load/Save) ---

def load_all_library_data():
    """Loads all existing artist JSON files from the DATA_DIR."""
    library = {}
    if not os.path.exists(DATA_DIR):
        return library
    
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".json"):
            artist_name = filename[:-5] # Remove .json
            filepath = os.path.join(DATA_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    library[artist_name] = json.load(f)
            except Exception as e:
                print(f"CORE ERROR: Error loading {filename}: {e}")
    return library

def save_artist_data(artist_name, songs):
    """Saves the scraped data for a single artist to a JSON file."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    # Sanitize artist name for a safe filename
    safe_artist_name = re.sub(r'[^\w\-_\. ]', '_', artist_name).strip()
    filename = os.path.join(DATA_DIR, f"{safe_artist_name}.json")
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(songs, f, indent=4, ensure_ascii=False)
        return filename
    except Exception as e:
        print(f"CORE ERROR: Error saving data: {e}")
        return None

# --- Scraper Logic ---

def get_song_links(artist_name, base_search_url):
    """
    Performs the search and extracts a list of song titles and their relative URLs.
    Supports both search query links and direct artist links (e.g., /e/ekoh.html).
    
    Returns: (list_of_song_dicts or error_status_str, executed_url)
    """
    
    try:
        # Use the passed URL for the search template, requires "{artist}" placeholder
        search_url = base_search_url.format(artist=requests.utils.quote(artist_name))
    except KeyError:
        return "URL_FORMAT_ERROR", None 
    
    executed_url = search_url 

    try:
        response = requests.get(executed_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException:
        return "NETWORK_ERROR", executed_url 

    soup = BeautifulSoup(response.text, 'html.parser')
    song_links = []
    
    # 1. Try to find links from a search results page (common AZLyrics search structure)
    song_table = soup.find('table', class_='table-condensed')
    if song_table:
        for link_tag in song_table.find_all('a', href=True):
            if '/lyrics/' in link_tag['href']:
                title = link_tag.text.strip()
                full_url = BASE_LYRIC_URL + link_tag['href']
                song_links.append({"title": title, "url": full_url, "artist": artist_name})
    
    # 2. If no search results found, try the direct artist page structure (e.g., /e/ekoh.html)
    if not song_links:
        artist_links_div = soup.find('div', id='listAlbum')
        if artist_links_div:
            # Look for links starting with "../lyrics/" which indicate a song link
            for link_tag in artist_links_div.find_all('a', href=lambda href: href and href.startswith('../lyrics/')):
                title = link_tag.text.strip()
                # Relative link needs to be cleaned up
                relative_path = link_tag['href'].replace('..', '') 
                full_url = BASE_LYRIC_URL + relative_path
                song_links.append({"title": title, "url": full_url, "artist": artist_name})
            
    return song_links, executed_url # Return the list AND the executed URL

# --- scrape_single_lyric and scrape_artist_lyrics functions remain the same ---
def scrape_single_lyric(song_data):
    """Fetches a single lyric page and extracts the text."""
    url = song_data['url']
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return None 

    soup = BeautifulSoup(response.text, 'html.parser')
    
    main_container = soup.find('div', class_='col-xs-12 col-lg-8 text-center')

    lyric_div = None
    if main_container:
        comment_text = " Usage of azlyrics.com content by any third-party lyrics provider is prohibited by our licensing agreement. Sorry about that. "
        
        for element in main_container.contents:
            if isinstance(element, requests.compat.Comment) and comment_text in element:
                next_element = element.find_next_sibling(name='div')
                if next_element:
                    lyric_div = next_element
                    break
            
    if lyric_div:
        lyrics = lyric_div.get_text(separator="\n", strip=True)
        return lyrics
    else:
        return None


def scrape_artist_lyrics(song_links, update_callback):
    """Orchestrates the scraping of all songs for an artist, calling a callback for status updates."""
    scraped_songs = {}
    total_songs = len(song_links)
    
    for i, song in enumerate(song_links):
        title = song['title']
        
        # Provide an update to the GUI thread
        update_callback(f"Scraping: {i+1}/{total_songs} - {title[:30]}...")
        
        lyrics = scrape_single_lyric(song)
        
        if lyrics:
            scraped_songs[title] = {
                "lyrics": lyrics,
                "url": song['url'],
                "play_count": 0 
            }
            
    return scraped_songs