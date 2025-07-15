import argparse
from reddit_scraper import RedditScraper
from persona_template import PersonaGenerator
from datetime import datetime
import os

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate a user persona from Reddit profile.')
    parser.add_argument('username', type=str, help='Reddit username to analyze')
    parser.add_argument('--output', type=str, default='persona_output.txt', help='Output file path')
    args = parser.parse_args()
    
    print(f"Generating persona for user: {args.username}")
    
    # Step 1: Scrape Reddit data
    print("Scraping Reddit data...")
    scraper = RedditScraper()
    posts, comments = scraper.get_user_data(args.username)
    
    if not posts and not comments:
        print("Error: No data found for this user.")
        return
    
    # Step 2: Generate persona
    print("Analyzing data and generating persona...")
    generator = PersonaGenerator()
    persona = generator.generate_persona(args.username, posts, comments)
    
    # Step 3: Save output
    print(f"Saving persona to {args.output}")
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(f"Reddit User Persona Report\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Source: https://www.reddit.com/user/{args.username}/\n\n")
        f.write(persona)
    
    print("Persona generation complete!")

if __name__ == "__main__":
    main()