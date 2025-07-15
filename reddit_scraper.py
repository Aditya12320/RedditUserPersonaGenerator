import praw
from praw.models import Redditor
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from typing import List, Dict, Tuple
import time

load_dotenv()

class RedditScraper:
    def __init__(self):
        """Initialize with more robust error handling."""
        self.api_available = False
        try:
            self.reddit = praw.Reddit(
                client_id=os.getenv('REDDIT_CLIENT_ID'),
                client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                user_agent='UserPersonaGenerator/2.0'
            )
            # Test the connection
            _ = self.reddit.user.me()
            self.api_available = True
        except Exception as e:
            print(f"PRAW initialization failed: {e}")
            self.api_available = False

    def get_user_data(self, username: str) -> Tuple[List[Dict], List[Dict]]:
        """Enhanced data collection with better fallback."""
        try:
            if self.api_available:
                return self._get_via_api(username)
            return self._get_via_scraping(username)
        except Exception as e:
            print(f"Error getting user data: {e}")
            return [], []

    def _get_via_api(self, username: str) -> Tuple[List[Dict], List[Dict]]:
        """More comprehensive API data collection."""
        try:
            redditor = self.reddit.redditor(username)
            
            posts = []
            for post in redditor.submissions.new(limit=100):
                posts.append({
                    'title': post.title,
                    'text': post.selftext,
                    'created_utc': post.created_utc,
                    'subreddit': str(post.subreddit),
                    'upvotes': post.score,
                    'url': post.url,
                    'type': 'post'
                })
                time.sleep(0.5)  # Rate limiting
            
            comments = []
            for comment in redditor.comments.new(limit=100):
                comments.append({
                    'text': comment.body,
                    'created_utc': comment.created_utc,
                    'subreddit': str(comment.subreddit),
                    'upvotes': comment.score,
                    'url': f"https://reddit.com{comment.permalink}",
                    'type': 'comment'
                })
                time.sleep(0.5)
            
            return posts, comments
            
        except Exception as e:
            print(f"API failed: {e}")
            return self._get_via_scraping(username)

    def _get_via_scraping(self, username: str) -> Tuple[List[Dict], List[Dict]]:
        """More robust scraping fallback."""
        print("Falling back to web scraping...")
        base_url = f"https://www.reddit.com/user/{username}/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(base_url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            data = []
            for item in soup.find_all('div', {'class': 'Post'}):
                try:
                    title = item.find('h3', class_='_eYtD2XCVieq6emjKBH3m')
                    text = item.find('div', class_='_292iotee39Lmt0MkQZ2hPV')
                    subreddit = item.find('a', class_='_3ryJoIoycVkA88fy40qNJc')
                    timestamp = item.find('a', class_='_3jOxDPIQ0KaOWpzvSQo-1s')
                    
                    if title:
                        data.append({
                            'title': title.text,
                            'text': text.text if text else '',
                            'subreddit': subreddit.text if subreddit else '',
                            'url': f"https://reddit.com{timestamp['href']}" if timestamp else '',
                            'type': 'post' if text else 'comment'
                        })
                except Exception as e:
                    print(f"Error parsing item: {e}")
            
            # Separate posts and comments
            posts = [item for item in data if item['type'] == 'post']
            comments = [item for item in data if item['type'] == 'comment']
            
            return posts, comments
            
        except Exception as e:
            print(f"Scraping failed: {e}")
            return [], []