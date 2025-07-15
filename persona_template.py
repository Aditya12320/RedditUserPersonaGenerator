
import base64
from datetime import datetime
from typing import List, Dict, Tuple
import os
from dotenv import load_dotenv
import json
import re
from together import Together

load_dotenv()

class PersonaGenerator:
    def __init__(self):
        """Initialize with Together API."""
        self.client = Together(api_key=os.getenv("TOGETHER_API_KEY"))
        self.model = "deepseek-ai/DeepSeek-V3"
        self.template = """
# {name}

**AGE** {age} | **OCCUPATION** {occupation} | **STATUS** {status} | **LOCATION** {location} | **TUBE** {tube} | **ARCHETYPE** {archetype}

---

## {primary_traits}

### {secondary_traits}

---

## MOTIVATIONS

{motivations}

---

## BEHAVIOR & HABITS

{behavior}

---

## GOALS & NEEDS

{goals}

---

## FRUSTRATIONS

{frustrations}

---

"{quote}"
"""

    def generate_persona(self, username: str, posts: List[Dict], comments: List[Dict]) -> str:
        """Generate persona using either API or heuristic analysis."""
        if not posts and not comments:
            return self._create_empty_persona(username)
        
        combined_text = self._combine_text_data(posts, comments)
        
        try:
            analysis = self._analyze_with_together_api(username, combined_text)
            return self._format_persona(analysis)
        except Exception as e:
            print(f"Together API failed, using heuristic analysis: {e}")
            return self._heuristic_analysis(username, posts, comments)

    def _analyze_with_together_api(self, username: str, text_data: str) -> Dict:
        """Use Together API to analyze user data."""
        prompt = f"""Analyze this Reddit user's activity and create a detailed persona in JSON format:
        
        Username: {username}
        Activity Data:
        {text_data[:10000]}  # Limit to avoid hitting token limits
        
        Required JSON format:
        {{
            "name": "string",
            "age": "string",
            "occupation": "string",
            "status": "string",
            "location": "string",
            "tube": "string",
            "archetype": "string",
            "primary_traits": "string",
            "secondary_traits": "string",
            "motivations": ["string"],
            "behavior": ["string"],
            "goals": ["string"],
            "frustrations": ["string"],
            "quote": "string"
        }}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Extract the generated content
            generated_text = response.choices[0].message.content
            
            # Clean the response to extract JSON
            json_str = self._extract_json(generated_text)
            return json.loads(json_str)
            
        except Exception as e:
            print(f"Together API error: {e}")
            raise ValueError("Failed to analyze with Together API")

    def _extract_json(self, text: str) -> str:
        """Extract JSON content from the API response."""
        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        return text  # fallback to return the whole text if JSON not found

    def _format_persona(self, analysis: Dict) -> str:
        """Format the analysis into the persona template."""
        def format_list(items):
            return "\n".join(f"- {item}" for item in items) if items else "- No data available"
        
        return self.template.format(
            name=analysis.get("name", "Unknown"),
            age=analysis.get("age", "Unknown"),
            occupation=analysis.get("occupation", "Unknown"),
            status=analysis.get("status", "Unknown"),
            location=analysis.get("location", "Unknown"),
            tube=analysis.get("tube", "Unknown"),
            archetype=analysis.get("archetype", "Unknown"),
            primary_traits=analysis.get("primary_traits", "Unknown"),
            secondary_traits=analysis.get("secondary_traits", "Unknown"),
            motivations=format_list(analysis.get("motivations", [])),
            behavior=format_list(analysis.get("behavior", [])),
            goals=format_list(analysis.get("goals", [])),
            frustrations=format_list(analysis.get("frustrations", [])),
            quote=analysis.get("quote", "No representative quote available")
        )

    def _combine_text_data(self, posts: List[Dict], comments: List[Dict]) -> str:
        """Combine and prioritize high-quality content."""
        text_parts = []
        
        # Add most upvoted posts first
        for post in sorted(posts, key=lambda x: x.get('upvotes', 0), reverse=True)[:30]:
            text_parts.append(f"POST in r/{post['subreddit']} ({post.get('upvotes', 0)} upvotes): {post['title']}\n{post['text']}")
        
        # Add most upvoted comments
        for comment in sorted(comments, key=lambda x: x.get('upvotes', 0), reverse=True)[:30]:
            text_parts.append(f"COMMENT in r/{comment['subreddit']} ({comment.get('upvotes', 0)} upvotes): {comment['text']}")
        
        return "\n\n".join(text_parts)


    def _heuristic_analysis(self, username: str, posts: List[Dict], comments: List[Dict]) -> str:
        """Comprehensive analysis using multiple inference methods."""
        print("Performing comprehensive heuristic analysis...")
        
        # Combine all activity items
        all_items = posts + comments
        
        # Basic metrics
        subreddits = self._get_subreddit_stats(all_items)
        total_posts = len(posts)
        total_comments = len(comments)
        most_active_subreddits = sorted(subreddits.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Detailed inferences
        age = self._infer_age(all_items)
        occupation = self._infer_occupation(all_items)
        location = self._infer_location(all_items)
        status = self._infer_relationship_status(all_items)
        motivations = self._infer_motivations(all_items)
        goals = self._infer_goals(all_items)
        frustrations = self._infer_frustrations(all_items)
        quote = self._find_representative_quote(all_items)
        
        # Enhanced behavior analysis
        behavior = [
            f"Active in {len(subreddits)} subreddits",
            f"Has made {total_posts} posts and {total_comments} comments",
            f"Most active in: {', '.join([f'r/{s[0]} ({s[1]} activities)' for s in most_active_subreddits])}",
            f"Most frequent posting times: {self._infer_posting_times(all_items)}",
            f"Engagement style: {self._infer_engagement_style(all_items)}"
        ]
        
        # Add specific behaviors if found
        specific_behaviors = self._find_specific_behaviors(all_items)
        behavior.extend(specific_behaviors)
        
        return self.template.format(
            name=username,
            age=age,
            occupation=occupation,
            status=status,
            location=location,
            tube=self._infer_tube_archetype(all_items)[0],
            archetype=self._infer_tube_archetype(all_items)[1],
            primary_traits=self._infer_traits(all_items)[0],
            secondary_traits=self._infer_traits(all_items)[1],
            motivations=self._format_list(motivations),
            behavior=self._format_list(behavior),
            goals=self._format_list(goals),
            frustrations=self._format_list(frustrations),
            quote=quote
        )

    def _get_subreddit_stats(self, items: List[Dict]) -> Dict[str, int]:
        """Calculate subreddit activity statistics."""
        subreddits = {}
        for item in items:
            sub = item.get('subreddit', 'unknown')
            subreddits[sub] = subreddits.get(sub, 0) + 1
        return subreddits

    def _infer_age(self, items: List[Dict]) -> str:
        """Enhanced age inference."""
        age_clues = {
            'teen': 0, 'school': 0, 'college': 0, 'university': 0,
            'job': 0, 'career': 0, 'wife': 0, 'husband': 0,
            'kids': 0, 'children': 0, 'retirement': 0
        }
        
        for item in items:
            text = (item.get('title', '') + ' ' + item.get('text', '')).lower()
            for clue in age_clues:
                if clue in text:
                    age_clues[clue] += 1
        
        if age_clues['kids'] > 2 or age_clues['children'] > 2:
            return "35-50 (parent)"
        if age_clues['wife'] > 1 or age_clues['husband'] > 1:
            return "30-45 (married)"
        if age_clues['college'] > 1 or age_clues['university'] > 1:
            return "18-25 (student)"
        if age_clues['job'] > 2 or age_clues['career'] > 2:
            return "25-40 (professional)"
        if age_clues['retirement'] > 0:
            return "60+ (retired)"
        
        # Default based on Reddit demographics
        return "25-35"

    def _infer_occupation(self, items: List[Dict]) -> str:
        """Enhanced occupation inference."""
        occupation_keywords = {
            'student': ['school', 'college', 'university', 'homework', 'exam'],
            'tech': ['code', 'programming', 'software', 'developer', 'python'],
            'legal': ['lawyer', 'legal', 'court', 'judge', 'attorney', 'adhiwakta', 'nyay'],
            'medical': ['doctor', 'hospital', 'nurse', 'patient', 'medical'],
            'business': ['business', 'startup', 'entrepreneur', 'company'],
            'creative': ['artist', 'designer', 'writer', 'photograph']
        }
        
        keyword_counts = {occ: 0 for occ in occupation_keywords}
        
        for item in items:
            text = (item.get('title', '') + ' ' + item.get('text', '')).lower()
            for occ, keywords in occupation_keywords.items():
                for kw in keywords:
                    if kw in text:
                        keyword_counts[occ] += 1
        
        # Get top 2 occupations
        top_occupations = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:2]
        
        if top_occupations[0][1] > 0:
            if top_occupations[0][0] == 'legal' or 'adhiwakta' in top_occupations[0][0]:
                return "Legal Professional"
            return top_occupations[0][0].title()
        return "Unknown"

    def _infer_location(self, items: List[Dict]) -> str:
        """Enhanced location inference."""
        location_keywords = {
            'Delhi': ['delhi', 'dilli'],
            'Mumbai': ['mumbai', 'bombay'],
            'Bangalore': ['bangalore', 'bengaluru'],
            'Lucknow': ['lucknow', 'lko'],
            'Nagpur': ['nagpur'],
            'India': ['india', 'bharat'],
            'USA': ['usa', 'america', 'new york', 'california'],
            'UK': ['uk', 'london', 'britain']
        }
        
        for item in items:
            text = (item.get('title', '') + ' ' + item.get('text', '')).lower()
            for loc, keywords in location_keywords.items():
                if any(kw in text for kw in keywords):
                    return loc
        
        return "Unknown"

    def _infer_relationship_status(self, items: List[Dict]) -> str:
        """Infer relationship status."""
        status_keywords = {
            'Single': ['single', 'dating', 'boyfriend', 'girlfriend'],
            'Married': ['married', 'wife', 'husband', 'spouse'],
            'Divorced': ['divorced', 'ex-wife', 'ex-husband']
        }
        
        for item in items:
            text = (item.get('title', '') + ' ' + item.get('text', '')).lower()
            for status, keywords in status_keywords.items():
                if any(kw in text for kw in keywords):
                    return status
        
        return "Unknown"

    def _infer_tube_archetype(self, items: List[Dict]) -> Tuple[str, str]:
        """Infer tech adoption and personality archetype."""
        tech_keywords = ['tech', 'gadget', 'smartphone', 'app', 'software']
        creative_keywords = ['create', 'art', 'write', 'design', 'build']
        help_keywords = ['help', 'advice', 'suggestion']
        
        tech_count = 0
        creative_count = 0
        help_count = 0
        
        for item in items:
            text = item.get('text', '').lower()
            tech_count += sum(1 for kw in tech_keywords if kw in text)
            creative_count += sum(1 for kw in creative_keywords if kw in text)
            help_count += sum(1 for kw in help_keywords if kw in text)
        
        # Determine tube
        if tech_count > 3:
            tube = "Early Adopter"
        elif tech_count > 0:
            tube = "Mainstream"
        else:
            tube = "Laggard"
        
        # Determine archetype
        if creative_count > help_count and creative_count > 2:
            archetype = "The Creator"
        elif help_count > 2:
            archetype = "The Helper"
        else:
            archetype = "The Participant"
        
        return tube, archetype

    def _infer_traits(self, items: List[Dict]) -> Tuple[str, str]:
        """Enhanced personality trait inference."""
        positive_words = ['great', 'awesome', 'love', 'happy', 'nice']
        negative_words = ['hate', 'terrible', 'awful', 'bad', 'worst']
        analytical_words = ['think', 'analysis', 'logical', 'reason']
        social_words = ['friend', 'community', 'group', 'together']
        
        counts = {
            'positive': 0,
            'negative': 0,
            'analytical': 0,
            'social': 0
        }
        
        for item in items:
            text = item.get('text', '').lower()
            counts['positive'] += sum(1 for w in positive_words if w in text)
            counts['negative'] += sum(1 for w in negative_words if w in text)
            counts['analytical'] += sum(1 for w in analytical_words if w in text)
            counts['social'] += sum(1 for w in social_words if w in text)
        
        # Primary traits
        if counts['analytical'] > counts['social']:
            primary = "Analytical, Logical"
        else:
            primary = "Social, Emotional"
        
        # Secondary traits
        if counts['positive'] > counts['negative']:
            secondary = "Positive, Helpful"
        else:
            secondary = "Critical, Direct"
        
        return primary, secondary

    def _infer_motivations(self, items: List[Dict]) -> List[str]:
        """Enhanced motivation inference."""
        motivations = []
        motivation_keywords = {
            'Learning': ['learn', 'study', 'read', 'knowledge'],
            'Helping': ['help', 'advice', 'suggest'],
            'Sharing': ['share', 'tell', 'story'],
            'Entertainment': ['fun', 'game', 'movie', 'music']
        }
        
        for item in items:
            text = item.get('text', '').lower()
            for mot, keywords in motivation_keywords.items():
                if any(kw in text for kw in keywords) and mot not in motivations:
                    motivations.append(mot)
        
        return motivations or ["Unknown"]

    def _infer_goals(self, items: List[Dict]) -> List[str]:
        """Enhanced goal inference."""
        goals = []
        goal_keywords = {
            'Career growth': ['promotion', 'career', 'job', 'work'],
            'Education': ['degree', 'study', 'course', 'learn'],
            'Relationships': ['friend', 'partner', 'relationship'],
            'Financial': ['money', 'save', 'invest', 'rich']
        }
        
        for item in items:
            text = item.get('text', '').lower()
            for goal, keywords in goal_keywords.items():
                if any(kw in text for kw in keywords) and goal not in goals:
                    goals.append(goal)
        
        return goals or ["Unknown"]

    def _infer_frustrations(self, items: List[Dict]) -> List[str]:
        """Enhanced frustration inference."""
        frustrations = []
        frustration_keywords = {
            'Technology': ['bug', 'crash', 'slow', 'internet'],
            'Work': ['boss', 'stress', 'meeting', 'hours'],
            'Society': ['government', 'rules', 'system', 'corrupt'],
            'Personal': ['lonely', 'tired', 'sick', 'angry']
        }
        
        for item in items:
            text = item.get('text', '').lower()
            for frust, keywords in frustration_keywords.items():
                if any(kw in text for kw in keywords) and frust not in frustrations:
                    frustrations.append(frust)
        
        return frustrations or ["Unknown"]

    def _find_representative_quote(self, items: List[Dict]) -> str:
        """Find most representative quote with context."""
        if not items:
            return "No representative quote available"
        
        # Find the most upvoted item
        most_upvoted = max(items, key=lambda x: x.get('upvotes', 0))
        text = most_upvoted.get('text', most_upvoted.get('title', ''))
        
        # Add context if available
        subreddit = most_upvoted.get('subreddit', '')
        if subreddit:
            return f"[r/{subreddit}] {text[:200]}..." if len(text) > 200 else text
        return text[:200] + "..." if len(text) > 200 else text

    def _infer_posting_times(self, items: List[Dict]) -> str:
        """Infer typical posting times."""
        if not items:
            return "Unknown"
        
        # Count posts by hour (UTC)
        hours = [0]*24
        for item in items:
            if 'created_utc' in item:
                hour = datetime.utcfromtimestamp(item['created_utc']).hour
                hours[hour] += 1
        
        # Find peak hours
        peak_hours = sorted(range(24), key=lambda x: hours[x], reverse=True)[:2]
        return f"{peak_hours[0]}:00-{peak_hours[0]+1}:00 UTC, {peak_hours[1]}:00-{peak_hours[1]+1}:00 UTC"

    def _infer_engagement_style(self, items: List[Dict]) -> str:
        """Infer how the user engages with others."""
        question_count = sum(1 for item in items if '?' in item.get('text', ''))
        answer_count = sum(1 for item in items if '?' not in item.get('text', '') and item.get('text', ''))
        
        if question_count > answer_count * 2:
            return "Mostly asks questions"
        elif answer_count > question_count * 2:
            return "Mostly provides answers"
        return "Balanced questions and answers"

    def _find_specific_behaviors(self, items: List[Dict]) -> List[str]:
        """Identify specific behavioral patterns."""
        behaviors = []
        
        # Check for meme usage
        meme_keywords = ['meme', 'lol', 'haha', 'funny']
        meme_count = sum(1 for item in items if any(kw in item.get('text', '').lower() for kw in meme_keywords))
        if meme_count > 2:
            behaviors.append(f"Frequently shares memes/humor ({meme_count} instances)")
        
        # Check for political engagement
        political_keywords = ['politics', 'government', 'vote', 'election']
        political_count = sum(1 for item in items if any(kw in item.get('text', '').lower() for kw in political_keywords))
        if political_count > 2:
            behaviors.append(f"Engages in political discussions ({political_count} instances)")
        
        return behaviors

    def _format_list(self, items: List[str]) -> str:
        """Format list for template."""
        return "\n".join(f"- {item}" for item in items) if items else "- No data available"
    
    def generate_persona_json(self, username: str, posts: List[Dict], comments: List[Dict]) -> Dict:
        """Generate persona as structured JSON data."""
        if not posts and not comments:
            return self._create_empty_persona_json(username)
        
        combined_text = self._combine_text_data(posts, comments)
        
        try:
            analysis = self._analyze_with_together_api(username, combined_text)
            # Ensure the photo is included in the API response
            if 'photo' not in analysis:
                analysis['photo'] = self._get_user_photo(username)
            return analysis
        except Exception as e:
            print(f"Together API failed, using heuristic analysis: {e}")
            return self._heuristic_analysis_json(username, posts, comments)

    def _get_user_photo(self, username: str) -> str:
        """Get user photo URL or generate default avatar.
        Attempts to fetch Reddit avatar first, falls back to generated SVG."""
        try:
            # Try to get Reddit avatar using praw
            if hasattr(self, 'reddit'):
                redditor = self.reddit.redditor(username)
                if hasattr(redditor, 'icon_img') and redditor.icon_img:
                    return redditor.icon_img
        except Exception as e:
            print(f"Couldn't fetch Reddit avatar: {e}")
        
        # Fallback to generated SVG avatar
        return self._generate_svg_avatar(username)

    def _generate_svg_avatar(self, username: str) -> str:
        """Generate a consistent SVG avatar based on username."""
        import hashlib
        
        # Clean username and get initials
        clean_name = ''.join([c for c in username if c.isalnum()])
        initials = (clean_name[:2] if len(clean_name) >= 2 
                else clean_name + clean_name).upper()
        
        # Generate colors from username hash
        hash_val = int(hashlib.md5(username.encode()).hexdigest(), 16)
        hue = hash_val % 360
        bg_color = f"hsl({hue}, 70%, 40%)"
        text_color = "#ffffff"
        
        svg = f"""<svg width="400" height="280" viewBox="0 0 400 280" xmlns="http://www.w3.org/2000/svg">
            <rect width="400" height="280" fill="{bg_color}"/>
            <circle cx="200" cy="140" r="80" fill="{text_color}"/>
            <text x="200" y="150" font-family="Arial" font-size="80" fill="{bg_color}" 
                text-anchor="middle" dominant-baseline="middle">{initials}</text>
        </svg>"""
        
        return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"

    def _heuristic_analysis_json(self, username: str, posts: List[Dict], comments: List[Dict]) -> Dict:
        """Comprehensive analysis using multiple inference methods, returning JSON."""
        # Combine all activity items
        all_items = posts + comments
        
        # Basic metrics
        subreddits = self._get_subreddit_stats(all_items)
        total_posts = len(posts)
        total_comments = len(comments)
        most_active_subreddits = sorted(subreddits.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Detailed inferences
        persona = {
            'username': username,
            'name': username,  # Default to username if name not found
            'age': self._infer_age(all_items),
            'occupation': self._infer_occupation(all_items),
            'status': self._infer_relationship_status(all_items),
            'location': self._infer_location(all_items),
            'tube': self._infer_tube_archetype(all_items)[0],
            'archetype': self._infer_tube_archetype(all_items)[1],
            'primary_traits': self._infer_traits(all_items)[0],
            'secondary_traits': self._infer_traits(all_items)[1],
            'motivations': self._infer_motivations(all_items),
            'behavior': [],
            'goals': self._infer_goals(all_items),
            'frustrations': self._infer_frustrations(all_items),
            'quote': self._find_representative_quote(all_items),
            'photo': "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjI4MCIgdmlld0JveD0iMCAwIDQwMCAyODAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMjgwIiBmaWxsPSIjOEI3MzU1Ii8+CjxjaXJjbGUgY3g9IjIwMCIgY3k9IjEyMCIgcj0iNDAiIGZpbGw9IiNGRkY1RjAiLz4KPHJlY3QgeD0iMTcwIiB5PSIxNzAiIHdpZHRoPSI2MCIgaGVpZ2h0PSI4MCIgcng9IjEwIiBmaWxsPSIjNjhBRTVCIi8+CjxyZWN0IHg9IjE2MCIgeT0iMjMwIiB3aWR0aD0iODAiIGhlaWdodD0iNTAiIHJ4PSI1IiBmaWxsPSIjRkY1NzMzIi8+CjxyZWN0IHg9IjE4NSIgeT0iMTAwIiB3aWR0aD0iMzAiIGhlaWdodD0iMTAiIHJ4PSI1IiBmaWxsPSIjMzMzIi8+CjwvdXZnPgo="
        }
        
        # Enhanced behavior analysis
        behavior = [
            f"Active in {len(subreddits)} subreddits",
            f"Has made {total_posts} posts and {total_comments} comments",
            f"Most active in: {', '.join([f'r/{s[0]} ({s[1]} activities)' for s in most_active_subreddits])}",
            f"Most frequent posting times: {self._infer_posting_times(all_items)}",
            f"Engagement style: {self._infer_engagement_style(all_items)}"
        ]
        
        # Add specific behaviors if found
        specific_behaviors = self._find_specific_behaviors(all_items)
        behavior.extend(specific_behaviors)
        persona['behavior'] = behavior
        
        return persona

    def _create_empty_persona_json(self, username: str) -> Dict:
        """Create empty persona as JSON."""
        return {
            'username': username,
            'name': username,
            'age': "Unknown",
            'occupation': "Unknown",
            'status': "Unknown",
            'location': "Unknown",
            'tube': "Unknown",
            'archetype': "Unknown",
            'primary_traits': "Unknown",
            'secondary_traits': "Unknown",
            'motivations': ["No data available"],
            'behavior': ["No data available"],
            'goals': ["No data available"],
            'frustrations': ["No data available"],
            'quote': "No representative quote available"
        }
        
    def _create_empty_persona(self, username: str) -> str:
        """Create empty persona template."""
        return self.template.format(
            name=username,
            age="Unknown",
            occupation="Unknown",
            status="Unknown",
            location="Unknown",
            tube="Unknown",
            archetype="Unknown",
            primary_traits="Unknown",
            secondary_traits="Unknown",
            motivations="- No data available",
            behavior="- No data available",
            goals="- No data available",
            frustrations="- No data available",
            quote="No representative quote available"
        )
