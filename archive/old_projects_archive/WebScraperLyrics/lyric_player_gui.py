# lyric_player_gui.py

import pygame
import sys
import threading
import time
# Import the logic layer (ensure scraper_core.py is present)
import scraper_core as core 

# --- Pygame Configuration ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
CAPTION = "Neon Lyric Arcade: Builder & Player"
FPS = 60

# --- Color Palette (Neon Theme) ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
NEON_PINK = (255, 0, 140)
NEON_BLUE = (0, 200, 255)
NEON_GREEN = (57, 255, 20)
NEON_YELLOW = (255, 255, 0)
NEON_RED = (255, 50, 50)

# --- Global State Management ---
class AppState:
    MAIN_MENU = 0
    SCRAPING = 1
    LIBRARY = 2
    PLAYER = 3

current_state = AppState.MAIN_MENU
status_message = "System Initializing..."
music_library = {} # Holds the loaded data
url_history = []   # NEW: List to store executed URLs and their status

# Threading globals
scraper_thread = None
scraped_result = None # Holds the final result dict from the thread

# --- Pygame Setup ---
pygame.init()
try:
    TITLE_FONT = pygame.font.Font(None, 80) 
    UI_FONT = pygame.font.Font(None, 30)
except:
    TITLE_FONT = pygame.font.Font(None, 80)
    UI_FONT = pygame.font.Font(None, 30)
    
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(CAPTION)
clock = pygame.time.Clock()


# --- UI Element Classes (TextRenderer, Button, InputBox remain the same) ---

class TextRenderer:
    """Helper for rendering neon text with a simple glow/shadow effect."""
    @staticmethod
    def draw_neon_text(screen, text, font, color, x, y, glow_color=NEON_PINK):
        # Simple glow simulation
        for offset in [(2, 2), (-2, -2)]:
            glow_surface = font.render(text, True, glow_color)
            screen.blit(glow_surface, (x + offset[0], y + offset[1]))
        
        # Main text
        text_surface = font.render(text, True, color)
        screen.blit(text_surface, (x, y))

class Button:
    """A simple neon-style button."""
    def __init__(self, x, y, width, height, text, color, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.action = action
        self.hover = False

    def draw(self, screen):
        border_color = NEON_YELLOW if self.hover else self.color
        
        # Border/Glow
        pygame.draw.rect(screen, border_color, self.rect, 4, border_radius=5)
        
        # Draw Text
        TextRenderer.draw_neon_text(
            screen, self.text, UI_FONT, 
            WHITE, 
            self.rect.centerx - (UI_FONT.size(self.text)[0] // 2),
            self.rect.centery - (UI_FONT.size(self.text)[1] // 2),
            glow_color=self.color if self.hover else (self.color[0]//3, self.color[1]//3, self.color[2]//3)
        )

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            if self.action:
                self.action()
                return True
                
class InputBox:
    """A text input box for Pygame."""
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = NEON_BLUE
        self.text = text
        self.font = UI_FONT
        self.active = False
        self.placeholder = "Enter Text"
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = NEON_PINK if self.active else NEON_BLUE
        
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                self.active = False
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
                
    def draw(self, screen):
        # Border
        pygame.draw.rect(screen, self.color, self.rect, 3)
        
        # Text rendering
        display_text = self.text
        text_color = NEON_YELLOW
        if not self.text and not self.active:
            display_text = self.placeholder
            text_color = (100, 100, 100) # Dim placeholder color

        txt_surface = self.font.render(display_text, True, text_color)
        screen.blit(txt_surface, (self.rect.x + 10, self.rect.y + 5))

# --- NEW UI Element Class: HistoryDisplay ---

class HistoryDisplay:
    """Displays the execution history of URLs in a scrollable format."""
    def __init__(self, x, y, width, height, max_lines=14):
        self.rect = pygame.Rect(x, y, width, height)
        self.max_lines = max_lines
        self.scroll_offset = 0 # How many lines to scroll down (from the latest entry)
        self.line_height = 25
        
    def draw(self, screen):
        pygame.draw.rect(screen, BLACK, self.rect)
        pygame.draw.rect(screen, NEON_BLUE, self.rect, 2)
        
        TextRenderer.draw_neon_text(screen, "URL HISTORY:", UI_FONT, NEON_BLUE, self.rect.x, self.rect.y - 30, NEON_BLUE)
        
        # Calculate the visible range (displaying newest entries first, hence reverse indexing)
        total_history = len(url_history)
        
        # Start from the latest entry (total_history - 1) and go backwards
        # The history is displayed from the top of the box downwards
        
        start_index = total_history - 1 - self.scroll_offset
        
        y_pos = self.rect.y + 5
        
        for i in range(self.max_lines):
            history_index = start_index - i
            
            if history_index < 0:
                break # Reached the end of the history list
            
            entry = url_history[history_index]
            
            # Formatting and color based on status
            status_map = {'SUCCESS': NEON_GREEN, 'FAIL': NEON_RED, 'ERROR': NEON_RED}
            color = status_map.get(entry['status'], NEON_YELLOW)
            status_char = '✅' if entry['status'] == 'SUCCESS' else '❌'
            
            # Format the output for display
            # Show up to 40 characters of the URL
            display_text = f"{status_char} {entry['artist']}: {entry['url'][entry['url'].rfind('/')+1:entry['url'].rfind('.html')].replace('{artist}', '...')[:40]}"
            
            text_surface = UI_FONT.render(display_text, True, color)
            screen.blit(text_surface, (self.rect.x + 5, y_pos))
            y_pos += self.line_height

    def handle_event(self, event):
        total_history = len(url_history)
        if total_history <= self.max_lines:
            return # No scrolling needed

        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            # Check for scroll up (button 4) and scroll down (button 5)
            if event.button == 4: # Scroll Up (view older entries)
                # Max scroll offset is total_history - max_lines
                self.scroll_offset = min(self.scroll_offset + 1, total_history - self.max_lines)
            elif event.button == 5: # Scroll Down (view newer entries)
                self.scroll_offset = max(self.scroll_offset - 1, 0)


# --- Threading Worker and Status Functions ---

def update_scraper_status(msg):
    """Callback function for the core scraper to update the GUI status bar."""
    global status_message
    status_message = f"CORE: {msg}"

def background_scraper_worker(artist_name, base_search_url):
    """The long-running function executed in the background thread."""
    global scraped_result, url_history
    
    executed_url = "N/A"
    status_to_log = "SUCCESS"
    
    try:
        update_scraper_status(f"Searching for '{artist_name}' at {base_search_url[:20]}...")
        
        # MODIFIED CALL: Expecting two return values
        song_links_or_status, executed_url = core.get_song_links(artist_name, base_search_url) 
        
        if song_links_or_status == "URL_FORMAT_ERROR":
            scraped_result = {"status": "FAIL", "message": "URL FORMAT ERROR: Did you include {artist} in the base URL?"}
            status_to_log = "FAIL"
            return

        if song_links_or_status == "NETWORK_ERROR":
            scraped_result = {"status": "FAIL", "message": "NETWORK ERROR: Could not reach target domain. Check connection/URL."}
            status_to_log = "FAIL"
            return
        
        song_links = song_links_or_status # If no error, this is the list of links
        
        if not song_links:
            scraped_result = {"status": "FAIL", "message": f"No song results found for '{artist_name}'."}
            status_to_log = "FAIL"
            return
            
        update_scraper_status(f"Found {len(song_links)} songs. Starting scrape...")
        
        scraped_data = core.scrape_artist_lyrics(song_links, update_scraper_status)
        
        if scraped_data:
            core.save_artist_data(artist_name, scraped_data)
            scraped_result = {"status": "SUCCESS", "message": f"DB built: {len(scraped_data)} songs for {artist_name}."}
            # status_to_log remains 'SUCCESS'
        else:
             scraped_result = {"status": "FAIL", "message": f"Scrape completed, but 0 lyrics extracted for {artist_name}."}
             status_to_log = "FAIL"
            
    except Exception as e:
        scraped_result = {"status": "ERROR", "message": f"FATAL THREAD ERROR: {e.__class__.__name__}"}
        status_to_log = "ERROR"
        
    finally:
        # Log the result regardless of success/fail
        url_history.append({'artist': artist_name, 'url': executed_url, 'status': status_to_log})


def start_scrape_workflow():
    """Initiates the background scrape thread."""
    global scraper_thread, status_message, scraped_result
    
    artist = artist_input.text.strip()
    search_url = url_input.text.strip()
    
    if not artist or not search_url:
        status_message = "INPUT ERROR: Artist Name and Base URL must be entered."
        return
        
    if scraper_thread and scraper_thread.is_alive():
        status_message = "WARNING: Scrape already in progress."
        return

    # Reset result and start the thread, PASSING THE URL
    scraped_result = None
    scraper_thread = threading.Thread(target=background_scraper_worker, args=(artist, search_url), daemon=True)
    scraper_thread.start()
    
    change_state(AppState.SCRAPING)
    status_message = f"Scraping for {artist} started in background. Please wait..."
    
def change_state(new_state):
    """Transition the application state."""
    global current_state, status_message
    current_state = new_state
    if new_state == AppState.MAIN_MENU:
        # Reload library after any scrape might have happened
        load_initial_data()
        
def load_initial_data():
    """Loads all local JSON data into the global library."""
    global music_library, status_message
    music_library = core.load_all_library_data()
    status_message = f"Ready. {len(music_library)} artists loaded."
    
def view_library():
    """Placeholder for the library view screen."""
    status_message = f"Library View: {len(music_library)} artists available. Total Songs: {sum(len(d) for d in music_library.values())}. Feature coming soon!"
    change_state(AppState.MAIN_MENU) 
    
def quit_app():
    pygame.quit()
    sys.exit()

# --- Main Loop Setup (Initialization) ---

# Input Box for Artist Name
artist_input = InputBox(50, 150, 370, 40, text='')
artist_input.placeholder = "Enter Artist Name (e.g., ekoh)"

# Input Box for Base URL - NEW DEFAULT LINK
DEFAULT_URL = "https://www.azlyrics.com/e/{artist}.html" 
url_input = InputBox(50, 260, 370, 40, text=DEFAULT_URL)
url_input.placeholder = "Enter Search URL with {artist} placeholder"

# Buttons 
scrape_button = Button(50, 330, 370, 50, "SCRAPE & BUILD DB", NEON_GREEN, start_scrape_workflow)
library_button = Button(50, 410, 370, 50, "VIEW MUSIC LIBRARY", NEON_BLUE, view_library)
quit_button = Button(50, 500, 370, 50, "EXIT ARCADE", NEON_RED, quit_app)

buttons = [scrape_button, library_button, quit_button]

# History Display
history_display = HistoryDisplay(450, 150, 320, 350) # Positioned on the right side


# --- Main Pygame Loop (Drawing and Event Handling) ---
def run_game():
    global status_message, scraper_thread, scraped_result
    
    load_initial_data() 

    while True:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_app()
                
            artist_input.handle_event(event)
            url_input.handle_event(event)
            history_display.handle_event(event) # Handle history scrolling
            for button in buttons:
                button.handle_event(event)

        # --- Thread Monitoring Logic ---
        if current_state == AppState.SCRAPING and scraper_thread and not scraper_thread.is_alive():
            # The background thread has finished!
            if scraped_result and scraped_result["status"] == "SUCCESS":
                status_message = scraped_result["message"]
            elif scraped_result:
                status_message = f"FAIL: {scraped_result['message']}"

            scraper_thread = None
            scraped_result = None
            change_state(AppState.MAIN_MENU) 

        # --- Drawing ---
        screen.fill(BLACK) 

        # Title
        TextRenderer.draw_neon_text(screen, CAPTION, TITLE_FONT, NEON_PINK, 10, 50, NEON_YELLOW)
        
        # Content
        if current_state == AppState.MAIN_MENU or current_state == AppState.SCRAPING:
            # Input Fields
            TextRenderer.draw_neon_text(screen, "ARTIST NAME:", UI_FONT, WHITE, 50, 120, NEON_BLUE)
            artist_input.draw(screen)
            TextRenderer.draw_neon_text(screen, "BASE TEMPLATE URL:", UI_FONT, WHITE, 50, 230, NEON_BLUE)
            url_input.draw(screen)
            
            # Buttons
            for button in buttons:
                button.draw(screen)
                
            # History Display
            history_display.draw(screen) 
        
        # Status Bar
        status_color = NEON_GREEN if "Ready" in status_message or "SUCCESS" in status_message else NEON_RED
        TextRenderer.draw_neon_text(screen, f"STATUS: {status_message}", UI_FONT, status_color, 50, SCREEN_HEIGHT - 40, NEON_YELLOW)

        # --- Display Update ---
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == '__main__':
    run_game()