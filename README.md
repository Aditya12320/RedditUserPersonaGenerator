
# Reddit User Persona Generator

![Project Screenshot](screenshot.png) <!-- Add a screenshot if available -->

A powerful tool that generates detailed user personas from Reddit profiles by analyzing their posts and comments using natural language processing and AI models.

---

## 🚀 Features

- 🔍 Extracts insights from Reddit user activity (posts + comments)
- 🧑‍💼 Generates realistic user personas with:
  - Demographic Info (age, gender, location, occupation)
  - Personality Traits (archetypes, characteristics)
  - Motivations, Goals, Frustrations
  - Behavioral Summary
- 💾 Export options: PDF, JPG, JSON, TXT
- 🕘 View history of generated personas
- 🌐 Clean and responsive web interface

---

## 🧰 Prerequisites

- Python 3.8 or above
- `pip` (Python package manager)
- Reddit API credentials *(optional but improves accuracy)*

---

## 📦 Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/reddit-user-persona-generator.git
cd reddit-user-persona-generator
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root and add the following:

```ini
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
TOGETHER_API_KEY=your_together_api_key  # Optional: Used for LLM-based analysis
```

---

## ▶️ Project Running

You can run the project in two ways: via **Command Line** or the **Web Interface**.

### 🔧 1. Command Line (TXT Output)

Use this if you want to generate a persona and save it as a `.txt` file:

```bash
python main.py Hungry-Move-6603 --output persona.txt
```

This will generate a detailed persona for the user `Hungry-Move-6603` and save it in `persona.txt`.

### 🌐 2. Web Interface (Frontend)

Use this if you prefer a user-friendly interface:

```bash
python frontend/app.py
```

Then open your browser and navigate to:  
👉 [http://localhost:5000](http://localhost:5000)

From there, you can:

- Enter any Reddit username (e.g., `Hungry-Move-6603`)
- Click "Generate Persona"
- View the generated result
- Download the result as PDF, JPG, or JSON

---

## 📁 Project Structure

```plaintext
reddit-user-persona-generator/
├── .env
├── README.md
├── frontend
│   ├── app.py
│   └── templates
│       ├── index.html
│       ├── persona.html
│       └── persona_card.html
├── main.py
├── persona_template.py
├── reddit_scraper.py
├── requirements.txt
└── temp_uploads
    └── 0c58670d-08d2-419d-9d25-62519d1a4543.json

```

---

## 📄 License

This project is licensed under the **MIT License**.  
See the `LICENSE` file for details.

---

## 🙌 Contributing

Pull requests are welcome.  
For major changes, please open an issue first to discuss what you'd like to change.

---

## 📬 Contact

For support or feedback, contact [adityajjilla26@gmail.com](mailto:adityajjilla26@gmail.com)
