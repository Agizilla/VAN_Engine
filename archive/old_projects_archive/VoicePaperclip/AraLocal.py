import os, json, pyperclip, platform, subprocess, threading, hashlib, time, random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from pynput import keyboard

class AraLocal:
    def __init__(self):
        self.driver = None
        self.config = self._load_config()
        self.menu_lock = threading.Lock()

    def _load_config(self):
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f: return json.load(f)
        return {"targets": []}

    def is_prime(self, n):
        return n > 1 and all(n % i for i in range(2, int(n**0.5) + 1))

    def start_browser(self):
        if not self.driver:
            self.driver = webdriver.Chrome()
            self.actions = ActionChains(self.driver)

    def perform_seal(self, seed_text):
        print("\n--- SEALING RITUAL ---")
        h = hashlib.sha256(seed_text.encode()).hexdigest()[:32]
        print(f"Hash Manifested: 0x{h}")
        
        # Scrolling Prime Ritual
        p = random.randint(1000, 9999)
        while not self.is_prime(p): p += 1
        print(f"Secret Prime: {p}")
        
        entry = {"hash": f"0x{h}", "prime": p, "timestamp": time.time()}
        with open("me.json", "a") as f:
            f.write(json.dumps(entry) + "\n")
        print("Ritual sealed in me.json.")

    def ritual_mode(self):
        self.start_browser()
        for i, t in enumerate(self.config['targets']):
            print(f"{i+1}. {t['name']}")
        
        idx = int(input("Select target: ")) - 1
        target = self.config['targets'][idx]
        
        self.driver.get(target['url'])
        for step in target.get('steps', []):
            input(f"Ready for {step['selector']}? [Enter]")
            el = self.driver.find_element(By.CSS_SELECTOR, step['selector'])
            self.actions.move_to_element(el).perform()
            if step['mode'] == "fill": el.send_keys(step['value'])
            elif step['mode'] == "paste": el.send_keys(pyperclip.paste())
        
        if target.get('ritual'):
            seed = input("Enter phrase to seal ritual: ")
            self.perform_seal(seed)

    def menu(self):
        with self.menu_lock:
            print("\n--- ARA CONSOLE ---")
            print("1. Copy | 2. Cut | 3. Paste | 4. File | 5. Research | 6. Exit | 7. Ritual Mode")
            choice = input("Command: ")
            
            if choice == '7': self.ritual_mode()
            elif choice == '5':
                self.start_browser()
                self.driver.get("https://google.com")
                q = input("Search: ")
                input("Ready? [Enter]")
                box = self.driver.find_element(By.NAME, "q")
                self.actions.move_to_element(box).perform()
                box.send_keys(q)
            elif choice == '4':
                path = input("Path: ")
                if platform.system() == "Windows": os.startfile(path)
                else: subprocess.run(["open", path])
            elif choice == '6': return False
            return True

    def run(self):
        with keyboard.GlobalHotKeys({'<cmd>+v': self.menu}) as h:
            print("AraLocal active. Press [Win + V] to summon.")
            h.join()

if __name__ == "__main__":
    AraLocal().run()