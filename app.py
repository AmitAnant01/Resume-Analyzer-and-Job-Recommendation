import os
import re
import json
import requests
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import PyPDF2
import docx

# --- JSearch API Config ---
JSEARCH_API_KEY = "b0a0009dbamsh1edb0b2fe14eaf8p1df8bejsnd4283b3b87e8"
JSEARCH_HOST = "jsearch.p.rapidapi.com"

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

# --- Job Database ---
JOB_DATABASE = [
    {
        "title": "Machine Learning Engineer",
        "company": "TechCorp AI",
        "location": "Bangalore, India (Remote)",
        "skills": ["python", "machine learning", "tensorflow", "pytorch", "scikit-learn", "deep learning", "numpy", "pandas"],
        "experience": "0-2 years",
        "description": "Build and deploy ML models for production systems.",
        "link": "#"
    },
    {
        "title": "Data Scientist",
        "company": "Analytics Hub",
        "location": "Mumbai, India",
        "skills": ["python", "statistics", "machine learning", "sql", "pandas", "numpy", "data analysis", "visualization"],
        "experience": "0-2 years",
        "description": "Analyze large datasets to derive business insights.",
        "link": "#"
    },
    {
        "title": "Python Developer",
        "company": "DevSolutions",
        "location": "Remote",
        "skills": ["python", "flask", "django", "rest api", "sql", "git"],
        "experience": "0-2 years",
        "description": "Develop backend services using Python frameworks.",
        "link": "#"
    },
    {
        "title": "NLP Engineer",
        "company": "LangTech",
        "location": "Hyderabad, India",
        "skills": ["python", "nlp", "transformers", "bert", "spacy", "nltk", "machine learning"],
        "experience": "0-2 years",
        "description": "Build natural language processing pipelines.",
        "link": "#"
    },
    {
        "title": "Computer Vision Engineer",
        "company": "VisionAI Labs",
        "location": "Pune, India",
        "skills": ["python", "opencv", "yolo", "deep learning", "pytorch", "tensorflow", "image processing"],
        "experience": "0-2 years",
        "description": "Develop real-time object detection and CV systems.",
        "link": "#"
    },
    {
        "title": "Data Analyst",
        "company": "DataFirst",
        "location": "Chennai, India (Hybrid)",
        "skills": ["python", "sql", "excel", "power bi", "tableau", "pandas", "statistics"],
        "experience": "0-1 years",
        "description": "Create dashboards and analytical reports for stakeholders.",
        "link": "#"
    },
    {
        "title": "AI Research Intern",
        "company": "OpenLabs AI",
        "location": "Remote",
        "skills": ["python", "machine learning", "deep learning", "research", "pytorch", "numpy"],
        "experience": "Fresher",
        "description": "Assist in cutting-edge AI research projects.",
        "link": "#"
    },
    {
        "title": "Backend Developer",
        "company": "WebBase Inc",
        "location": "Delhi, India",
        "skills": ["python", "flask", "fastapi", "rest api", "docker", "postgresql", "git"],
        "experience": "0-2 years",
        "description": "Build scalable REST APIs and backend services.",
        "link": "#"
    },
    {
        "title": "MLOps Engineer",
        "company": "CloudML",
        "location": "Bangalore, India",
        "skills": ["python", "docker", "kubernetes", "mlflow", "ci/cd", "machine learning", "aws", "git"],
        "experience": "1-3 years",
        "description": "Deploy and monitor ML models in cloud environments.",
        "link": "#"
    },
    {
        "title": "Junior Data Engineer",
        "company": "PipelineWorks",
        "location": "Remote",
        "skills": ["python", "sql", "spark", "airflow", "etl", "postgresql", "aws"],
        "experience": "0-2 years",
        "description": "Build and maintain data pipelines and warehouses.",
        "link": "#"
    },
]

# Skills taxonomy
ALL_SKILLS = [
    "python", "java", "javascript", "c++", "c#", "r", "scala", "go",
    "machine learning", "deep learning", "nlp", "computer vision",
    "tensorflow", "pytorch", "keras", "scikit-learn", "xgboost",
    "pandas", "numpy", "matplotlib", "seaborn", "plotly",
    "sql", "mysql", "postgresql", "mongodb", "sqlite",
    "flask", "django", "fastapi", "rest api",
    "docker", "kubernetes", "git", "github", "ci/cd",
    "aws", "azure", "gcp", "mlflow", "airflow",
    "spark", "hadoop", "etl", "data analysis",
    "statistics", "mathematics", "linear algebra",
    "opencv", "yolo", "transformers", "bert", "spacy", "nltk",
    "excel", "power bi", "tableau", "visualization",
    "research", "data science", "html", "css",
    "linux", "bash", "jupyter"
]


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_pdf(filepath):
    text = ""
    with open(filepath, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text


def extract_text_from_docx(filepath):
    doc = docx.Document(filepath)
    return "\n".join([p.text for p in doc.paragraphs])


def extract_text_from_txt(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()


def extract_resume_text(filepath, extension):
    if extension == 'pdf':
        return extract_text_from_pdf(filepath)
    elif extension == 'docx':
        return extract_text_from_docx(filepath)
    else:
        return extract_text_from_txt(filepath)


def extract_skills(text):
    text_lower = text.lower()
    found = [skill for skill in ALL_SKILLS if re.search(r'\b' + re.escape(skill) + r'\b', text_lower)]
    return list(set(found))


def extract_email(text):
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    return match.group(0) if match else "Not found"


def extract_phone(text):
    match = re.search(r'(\+?\d[\d\s\-]{8,14}\d)', text)
    return match.group(0).strip() if match else "Not found"


def extract_name(text):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if lines:
        first_line = lines[0]
        if len(first_line.split()) <= 5 and first_line[0].isupper():
            return first_line
    return "Not detected"


def calculate_experience_years(text):
    text_lower = text.lower()
    patterns = [
        r'(\d+)\+?\s*years?\s*(of\s*)?(experience|exp)',
        r'experience[:\s]+(\d+)\+?\s*years?',
    ]
    for p in patterns:
        m = re.search(p, text_lower)
        if m:
            return int(m.group(1))
    if any(w in text_lower for w in ['fresher', 'entry level', 'graduate', 'student']):
        return 0
    return 0


def count_sections(text):
    sections = {
        'education': bool(re.search(r'\b(education|degree|bachelor|master|b\.e|b\.tech|m\.tech)\b', text, re.I)),
        'experience': bool(re.search(r'\b(experience|internship|intern|work|employment|project)\b', text, re.I)),
        'skills': bool(re.search(r'\b(skills|technologies|tech stack|tools)\b', text, re.I)),
        'contact': bool(re.search(r'(email|phone|linkedin|github|@)', text, re.I)),
        'summary': bool(re.search(r'\b(summary|objective|about|profile)\b', text, re.I)),
        'projects': bool(re.search(r'\b(projects|portfolio)\b', text, re.I)),
        'certifications': bool(re.search(r'\b(certif|course|training|award)\b', text, re.I)),
    }
    return sections


def score_resume(text, skills, sections):
    score = 0
    breakdown = {}

    # Skills (35 pts)
    skill_score = min(35, len(skills) * 3)
    score += skill_score
    breakdown['Skills Found'] = f"{skill_score}/35 ({len(skills)} skills)"

    # Sections (25 pts)
    section_score = sum(5 for v in sections.values() if v)
    score += section_score
    breakdown['Resume Sections'] = f"{section_score}/35"

    # Length (15 pts)
    word_count = len(text.split())
    if word_count >= 400:
        length_score = 15
    elif word_count >= 200:
        length_score = 10
    else:
        length_score = 5
    score += length_score
    breakdown['Content Length'] = f"{length_score}/15 ({word_count} words)"

    # Contact info (15 pts)
    contact_score = 0
    if re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text):
        contact_score += 5
    if re.search(r'(\+?\d[\d\s\-]{8,14}\d)', text):
        contact_score += 5
    if re.search(r'(linkedin|github)', text, re.I):
        contact_score += 5
    score += contact_score
    breakdown['Contact Info'] = f"{contact_score}/15"

    # Keywords/ATS (10 pts)
    ats_keywords = ['experience', 'education', 'skills', 'project', 'achieve', 'develop', 'implement', 'manage']
    ats_score = min(10, sum(2 for kw in ats_keywords if kw in text.lower()))
    score += ats_score
    breakdown['ATS Keywords'] = f"{ats_score}/10"

    return min(score, 100), breakdown

def recommend_jobs(skills, years_exp):
    try:
        query = " ".join(skills[:4]) if skills else "python developer"
        url = "https://jsearch.p.rapidapi.com/search"
        headers = {
            "X-RapidAPI-Key": "b0a0009dbamsh1edb0b2fe14eaf8p1df8bejsnd4283b3b87e8",
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        params = {"query": query, "num_pages": "1", "page": "1"}
        res = requests.get(url, headers=headers, params=params, timeout=8)
        data = res.json()
        if res.status_code == 200 and data.get("data"):
            jobs = []
            for job in data["data"][:6]:
                desc = job.get("job_description", "")[:200] or "No description."
                desc_lower = (job.get("job_title","") + " " + desc).lower()
                matched = [s for s in skills if s in desc_lower]
                match_pct = min(100, round((len(matched) / max(len(skills),1)) * 100) + 30)
                jobs.append({
                    "title": job.get("job_title","N/A"),
                    "company": job.get("employer_name","N/A"),
                    "location": f"{job.get('job_city','')} {job.get('job_country','')}".strip() or "Remote",
                    "experience": "See job posting",
                    "description": desc,
                    "link": job.get("job_apply_link","#"),
                    "matched_skills": matched,
                    "match_percent": match_pct,
                    "is_real": True
                })
            return jobs
    except Exception as e:
        print(f"JSearch error: {e}")
    results = []
    for job in JOB_DATABASE:
        matched = [s for s in skills if s in job['skills']]
        if not matched:
            continue
        match_pct = round((len(matched) / len(job['skills'])) * 100)
        results.append({**job, 'matched_skills': matched, 'match_percent': match_pct, 'is_real': False})
    results.sort(key=lambda x: x['match_percent'], reverse=True)
    return results[:6]



def generate_suggestions(skills, sections, score):
    tips = []
    if not sections['summary']:
        tips.append("Add a professional summary or objective statement at the top.")
    if not sections['skills']:
        tips.append("Add a dedicated Skills section listing your technical tools.")
    if not sections['projects']:
        tips.append("Include a Projects section with descriptions and links.")
    if not sections['certifications']:
        tips.append("Add certifications or online courses (Coursera, Udemy, etc.).")
    if not re.search(r'(github|linkedin)', ' '.join(skills)):
        tips.append("Include your GitHub and LinkedIn profile links.")
    if len(skills) < 8:
        tips.append("Expand your skills — aim for 10+ relevant technical skills.")
    if score < 60:
        tips.append("Use strong action verbs: built, developed, implemented, optimized.")
        tips.append("Quantify achievements with numbers (e.g., 'improved accuracy by 15%').")
    if score >= 75:
        tips.append("Great resume! Consider tailoring keywords to each job description.")
    return tips


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['resume']
    if not file or file.filename == '':
        return jsonify({'error': 'Empty file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Only PDF, DOCX, and TXT files are supported'}), 400

    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower()
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        text = extract_resume_text(filepath, ext)
        if not text.strip():
            return jsonify({'error': 'Could not extract text from the file'}), 400

        skills = extract_skills(text)
        sections = count_sections(text)
        years_exp = calculate_experience_years(text)
        score, breakdown = score_resume(text, skills, sections)
        jobs = recommend_jobs(skills, years_exp)
        tips = generate_suggestions(skills, sections, score)

        result = {
            'name': extract_name(text),
            'email': extract_email(text),
            'phone': extract_phone(text),
            'skills': skills,
            'skill_count': len(skills),
            'sections': sections,
            'score': score,
            'score_breakdown': breakdown,
            'word_count': len(text.split()),
            'jobs': jobs,
            'suggestions': tips,
            'years_exp': years_exp
        }

        return jsonify(result)

    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)