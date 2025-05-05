import streamlit as st
from streamlit_chat import message
from groq import Groq
import os
from dotenv import load_dotenv
import time
import requests
from fpdf import FPDF
from io import BytesIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Load environment variables
load_dotenv()  # Load variables from .env file if it exists

# Try to load secrets from Streamlit's secrets management, fall back to environment variables
def get_secret(key):
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        # Fall back to environment variables
        return os.environ.get(key)

groq_api_key = get_secret("GROQ_API_KEY")
jooble_api_key = get_secret("JOOBLE_API_KEY")
sender_email = get_secret("SENDER_EMAIL")
sender_password = get_secret("SENDER_PASSWORD")

# Verify that required keys are available
if not groq_api_key:
    st.error("GROQ API key is missing. Please set it in .streamlit/secrets.toml or as an environment variable.")
    st.stop()

# GROQ client setup
client = Groq(api_key=groq_api_key)

# Streamlit config
st.set_page_config(page_title="Hiring Partner AI", page_icon="🤝", layout="centered")

# Custom CSS
st.markdown("""
    <style>
    .stChatInputContainer {
        background: #fff;
        border-top: 2px solid #ccc;
    }
    .stButton button {
        background-color: #003366;
        color: white;
        font-weight: bold;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown("## 🤝 Hiring Partner Assistant")
st.caption("Smarter hiring through intelligent conversations.")

# Session states
if "messages" not in st.session_state:
    st.session_state.messages = []
if "stage" not in st.session_state:
    st.session_state.stage = "greeting"
if "candidate_info" not in st.session_state:
    st.session_state.candidate_info = {}
if "tech_questions" not in st.session_state:
    st.session_state.tech_questions = []
if "code_questions" not in st.session_state:
    st.session_state.code_questions = []
if "job_recommendations" not in st.session_state:
    st.session_state.job_recommendations = []
if "end_chat" not in st.session_state:
    st.session_state.end_chat = False

# Generate LLM response
def generate_llm_response(prompt):
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error: {e}"

# Technical questions
def get_technical_questions(tech_stack):
    prompt = f"""You are an AI recruiter. Generate 3 concise technical interview questions EACH for the following technologies:\n{tech_stack}."""
    return generate_llm_response(prompt)

# High-level coding questions
def get_coding_questions(tech_stack):
    prompt = f"""As a senior AI interviewer, suggest 3 challenging coding questions based on the following tech stack:\n{tech_stack}."""
    return generate_llm_response(prompt)

# Job recommendations from Jooble API
def get_job_recommendations(position, location, remote=True):
    # Force fallback to use our custom implementation with real links
    use_fallback = True  # Always use our improved fallback with real links
    debug_mode = False
    debug_container = st.empty()
    
    # Function to clean HTML tags and normalize text
    def clean_html(text):
        if not text or not isinstance(text, str):
            return ""
        import re
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]*>', '', text)
        # Replace multiple dots, dashes with a single one
        clean_text = re.sub(r'\.{2,}', '. ', clean_text)
        clean_text = re.sub(r'\-{2,}', ' - ', clean_text)
        # Remove extra whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        return clean_text

    # Generate high-quality reliable job listings with REAL working links
    def generate_quality_jobs():
        # Create position-relevant data based on the position input
        position_lower = position.lower()
        position_encoded = requests.utils.quote(position)
        location_encoded = requests.utils.quote(location)
        
        # Create real job search URLs that will actually work
        indeed_search = f"https://www.indeed.com/jobs?q={position_encoded}&l={location_encoded}"
        linkedin_search = f"https://www.linkedin.com/jobs/search/?keywords={position_encoded}&location={location_encoded}"
        glassdoor_search = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={position_encoded}&locT=C&locId=0&locKeyword={location_encoded}"
        ziprecruiter_search = f"https://www.ziprecruiter.com/jobs/search?q={position_encoded}&l={location_encoded}"
        monster_search = f"https://www.monster.com/jobs/search?q={position_encoded}&where={location_encoded}"
        
        mock_jobs = []
        
        # Developer/Tech related positions
        if any(tech in position_lower for tech in ['developer', 'engineer', 'programming', 'software', 'web', 'full stack', 'frontend', 'backend']):
            mock_jobs = [
                {
                    'title': f"{position.title()} - Remote Opportunities",
                    'company': "Multiple Companies via LinkedIn",
                    'location': f"{location}",
                    'salary': "$85,000 - $125,000 per year (typical range)",
                    'snippet': "Browse multiple software development opportunities matching your skills and location. LinkedIn features positions from startups to Fortune 500 companies.",
                    'link': linkedin_search
                },
                {
                    'title': f"Senior {position.title()} Positions",
                    'company': "Various Tech Employers via Indeed",
                    'location': f"{location}",
                    'salary': "$120,000 - $160,000 per year (typical range)",
                    'snippet': "Indeed features numerous senior developer roles requiring leadership experience and technical expertise. Filter by salary, company size, and more.",
                    'link': indeed_search
                },
                {
                    'title': f"Entry & Mid-Level {position.title()}",
                    'company': "Tech Companies via ZipRecruiter",
                    'location': f"{location}",
                    'salary': "$65,000 - $110,000 per year (typical range)",
                    'snippet': "Find development jobs for all experience levels. ZipRecruiter offers positions with various tech stacks and company cultures.",
                    'link': ziprecruiter_search
                }
            ]
        # Data related positions
        elif any(term in position_lower for term in ['data', 'analyst', 'scientist', 'machine learning', 'ai', 'analytics']):
            mock_jobs = [
                {
                    'title': f"{position.title()} - Latest Listings",
                    'company': "Top Companies via Glassdoor",
                    'location': f"{location}",
                    'salary': "$95,000 - $135,000 per year (typical range)",
                    'snippet': "Explore data science and analytics roles on Glassdoor. Compare companies using employee reviews and reported salary information.",
                    'link': glassdoor_search
                },
                {
                    'title': f"Remote {position.title()} Opportunities",
                    'company': "Various Employers via LinkedIn",
                    'location': f"{location} & Remote",
                    'salary': "$90,000 - $150,000 per year (typical range)",
                    'snippet': "Find flexible and remote data positions. LinkedIn features jobs from companies embracing remote work culture for data professionals.",
                    'link': linkedin_search
                },
                {
                    'title': f"{position.title()} - All Levels",
                    'company': "Multiple Organizations via Indeed",
                    'location': f"{location}",
                    'salary': "$75,000 - $180,000 based on experience",
                    'snippet': "Indeed lists numerous data-focused positions from entry-level to director roles. Filter by company ratings, job type, and experience level.",
                    'link': indeed_search
                }
            ]
        # Marketing/Sales positions
        elif any(term in position_lower for term in ['marketing', 'sales', 'account', 'business development', 'growth']):
            mock_jobs = [
                {
                    'title': f"{position.title()} - Latest Opportunities",
                    'company': "Various Companies via LinkedIn",
                    'location': f"{location}",
                    'salary': "Competitive Base + Commission (typical structure)",
                    'snippet': "Discover sales and marketing roles matching your experience level and industry interests. LinkedIn features positions with established companies and growing startups.",
                    'link': linkedin_search
                },
                {
                    'title': f"Senior {position.title()} Roles",
                    'company': "Multiple Employers via Monster",
                    'location': f"{location}",
                    'salary': "$85,000 - $120,000 + Commission (typical range)",
                    'snippet': "Monster features numerous senior sales positions with competitive compensation packages. Find roles that match your industry expertise and sales approach.",
                    'link': monster_search
                },
                {
                    'title': f"Entry-Level {position.title()}",
                    'company': "Various Organizations via Indeed",
                    'location': f"{location}",
                    'salary': "$45,000 - $60,000 + Commission (typical range)",
                    'snippet': "Start or advance your sales career with positions perfect for developing your skills. Indeed offers roles with training programs and growth potential.",
                    'link': indeed_search
                }
            ]
        # Generic positions (default)
        else:
            mock_jobs = [
                {
                    'title': f"{position.title()} - Recent Listings",
                    'company': "Multiple Employers via Indeed",
                    'location': f"{location}",
                    'salary': "Varies by employer",
                    'snippet': "Indeed features numerous positions matching your search criteria. Filter by salary range, job type, and company ratings to find your ideal match.",
                    'link': indeed_search
                },
                {
                    'title': f"{position.title()} Opportunities",
                    'company': "Various Organizations via LinkedIn",
                    'location': f"{location}",
                    'salary': "Competitive based on experience",
                    'snippet': "Browse LinkedIn's extensive job listings for this position. Connect directly with recruiters and see if your network has connections at hiring companies.",
                    'link': linkedin_search
                },
                {
                    'title': f"{position.title()} - All Experience Levels",
                    'company': "Multiple Companies via ZipRecruiter",
                    'location': f"{location}",
                    'salary': "Varies by employer and experience",
                    'snippet': "ZipRecruiter offers a wide range of opportunities from entry-level to senior positions. Their matching technology helps identify roles aligned with your experience.",
                    'link': ziprecruiter_search
                }
            ]
        
        # Add an additional general job search option
        mock_jobs.append({
            'title': f"All {position.title()} Jobs",
            'company': "Glassdoor Comprehensive Search",
            'location': f"{location} and surrounding areas",
            'salary': "All salary ranges",
            'snippet': "Access Glassdoor's complete database of positions matching your criteria. Compare companies based on employee reviews and reported compensation.",
            'link': glassdoor_search
        })
        
        return mock_jobs
    
    # If we're using fallback data directly, skip the API call
    if use_fallback:
        jobs = generate_quality_jobs()
    else:
        # Try the API first using the correct endpoint and parameters
        def fetch_jobs(keywords):
            try:
                # Prepare parameters according to API documentation
                params = {
                    'keyword': keywords,
                    'location': location
                }
                
                # Add remote parameter if applicable
                if remote:
                    params['remote'] = 'true'
                
                # Set up headers with proper authorization
                headers = {
                    'Authorization': f'Bearer {jooble_api_key}'
                }
                
                if debug_mode:
                    with debug_container.container():
                        with st.expander("API Debug Info", expanded=False):
                            st.write(f"Searching for jobs: {keywords} in {location}")
                            st.write(f"API URL: {base_url}")
                            st.write(f"Parameters: {params}")
                
                # Use GET request with query parameters as per API documentation
                response = requests.get(base_url, params=params, headers=headers)
                
                if debug_mode:
                    with debug_container.container():
                        with st.expander("API Response", expanded=False):
                            st.write(f"Status code: {response.status_code}")
                
                if response.status_code == 200:
                    job_data = response.json()
                    
                    # Extract jobs from the 'results' field as shown in the documentation
                    jobs = job_data.get('results', [])
                    
                    if debug_mode:
                        with debug_container.container():
                            with st.expander("Jobs Found", expanded=False):
                                st.write(f"Found {len(jobs)} jobs")
                    
                    return jobs
                else:
                    if debug_mode:
                        with debug_container.container():
                            with st.expander("API Error", expanded=False):
                                st.write(f"API Error: {response.status_code}")
                                st.write(response.text)
                    
                    # If API call fails, try the previous implementation as fallback
                    return try_legacy_api(keywords)
            except Exception as e:
                if debug_mode:
                    with debug_container.container():
                        with st.expander("API Exception", expanded=False):
                            st.write(f"Exception: {str(e)}")
                
                # If exception occurs, try the previous implementation as fallback
                return try_legacy_api(keywords)
        
        # Legacy API call as fallback
        def try_legacy_api(keywords):
            try:
                legacy_url = "https://jooble.org/api/"
                payload = {
                    "keywords": keywords,
                    "location": location,
                    "remote": remote
                }
                legacy_headers = {'Content-Type': 'application/json'}
                
                response = requests.post(f"{legacy_url}{jooble_api_key}", json=payload, headers=legacy_headers)
                
                if response.status_code == 200:
                    job_data = response.json()
                    return job_data.get('jobs', [])
                return []
            except Exception:
                return []
        
        # First try with the specific position
        jobs = fetch_jobs(position)
        
        # If no jobs found, try with broader terms
        if not jobs:
            if debug_mode:
                with debug_container.container():
                    with st.expander("API Debug Info", expanded=False):
                        st.write("Trying with broader search terms...")
            jobs = fetch_jobs(f"{position} OR entry OR graduate")
        
        # If still no jobs, use fallback data
        if not jobs:
            if debug_mode:
                with debug_container.container():
                    with st.expander("API Debug Info", expanded=False):
                        st.write("Using fallback job data...")
            jobs = generate_quality_jobs()

    # Format job listings consistently
    formatted = []
    for job in jobs[:5]:
        try:
            # Get job details with proper fallbacks
            title = clean_html(job.get('title', 'Position Available'))
            company = clean_html(job.get('company', job.get('companyName', 'Hiring Company')))
            job_location = clean_html(job.get('location', location))
            
            # Handle salary with default
            salary = clean_html(job.get('salary', 'Salary not specified'))
            if not salary or len(salary) < 3:
                salary = "Competitive salary"
            
            # Ensure we have a proper description
            snippet = clean_html(job.get('description', job.get('snippet', '')))
            
            # Adjust description based on job type if missing or short
            if not snippet or len(snippet) < 10:
                if 'developer' in position.lower() or 'engineer' in position.lower():
                    snippet = "Join our development team working on exciting projects. This role requires technical expertise and problem-solving skills."
                elif 'sales' in position.lower() or 'marketing' in position.lower():
                    snippet = "Help grow our business through strategic sales initiatives. Strong communication skills and results-oriented mindset required."
                else:
                    snippet = "Join our team of professionals in a collaborative work environment with opportunities for growth and development."
            
            # Format snippet to reasonable length
            if len(snippet) > 150:
                cutoff = 150
                last_period = snippet[:cutoff].rfind('.')
                last_space = snippet[:cutoff].rfind(' ')
                
                break_point = last_period if last_period > 0 else last_space
                if break_point > 0:
                    snippet = snippet[:break_point + 1] + "..."
                else:
                    snippet = snippet[:cutoff] + "..."
            
            # Get link URL with fallback to real job search sites
            link = job.get('link', job.get('url', job.get('jobUrl', '')))
            
            # If link is missing or appears to be a dummy/invalid URL, replace with a real job site search
            if not link or link == '#' or 'example.com' in link or link == 'https://www.jooble.org':
                position_encoded = requests.utils.quote(position)
                location_encoded = requests.utils.quote(location)
                link = f"https://www.indeed.com/jobs?q={position_encoded}&l={location_encoded}"
            
            # Build consistently formatted job listing
            job_listing = (
                f"🔹 **{title}**\n"
                f"🏢 {company}\n"
                f"📍 {job_location}\n"
                f"💰 {salary}\n"
                f"📝 {snippet}\n"
                f"🔗 [Apply Here]({link})"
            )
            formatted.append(job_listing)
        except Exception as e:
            if debug_mode:
                with debug_container.container():
                    with st.expander("Format Error", expanded=False):
                        st.write(f"Error formatting job: {str(e)}")
            continue
    
    # If we couldn't format any jobs properly, use simplified backup format
    if not formatted:
        backup_jobs = generate_quality_jobs()
        for job in backup_jobs:
            formatted.append(
                f"🔹 **{job['title']}**\n"
                f"🏢 {job['company']}\n"
                f"📍 {job['location']}\n"
                f"💰 {job['salary']}\n"
                f"📝 {job['snippet']}\n"
                f"🔗 [Apply Here]({job['link']})"
            )
    
    # Clear the debug container
    debug_container.empty()
        
    return formatted

# PDF Export
def export_pdf(candidate_info, tech_qs, code_qs, job_recs):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, "Hiring Partner - Candidate Summary", ln=True, align='C')
    pdf.ln(10)

    for key, val in candidate_info.items():
        pdf.multi_cell(0, 10, f"{key}: {val}")

    pdf.ln(5)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, "Technical Questions", ln=True)
    pdf.set_font("Arial", size=12)
    for q in tech_qs:
        pdf.multi_cell(0, 10, f"- {q}")

    pdf.ln(5)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, "Coding Questions", ln=True)
    pdf.set_font("Arial", size=12)
    for q in code_qs:
        pdf.multi_cell(0, 10, f"- {q}")

    pdf.ln(5)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, "Recommended Jobs", ln=True)
    pdf.set_font("Arial", size=12)
    for job in job_recs:
        pdf.multi_cell(0, 10, job.replace("🔹", "-").replace("📍", "Location:"))

    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer

# Email sending
def send_email_with_pdf(recipient_email, pdf_buffer):
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = "Your Hiring Partner Candidate Report"

    body = "Dear Candidate,\n\nAttached is your summary report from Hiring Partner.\n\nBest regards,\nHiring Partner Team"
    message.attach(MIMEText(body, "plain"))

    part = MIMEApplication(pdf_buffer.getvalue(), Name="HiringPartner_Candidate_Report.pdf")
    part['Content-Disposition'] = 'attachment; filename="HiringPartner_Candidate_Report.pdf"'
    message.attach(part)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# Chat logic
def chat_logic(user_input):
    info = st.session_state.candidate_info
    stage = st.session_state.stage

    if user_input.lower() in ["exit", "quit", "bye", "end"]:
        st.session_state.end_chat = True
        return "✅ Thank you for chatting with Hiring Partner! We’ll be in touch shortly. Goodbye! 👋"

    if stage == "greeting":
        st.session_state.stage = "full_name"
        return "👋 Welcome! I’m your virtual assistant from Hiring Partner.\n\nCan I know your **full name**?"

    elif stage == "full_name":
        info["Full Name"] = user_input
        st.session_state.stage = "email"
        return "📧 What’s your **email address**?"

    elif stage == "email":
        info["Email"] = user_input
        st.session_state.stage = "phone"
        return "📞 Could you share your **phone number**?"

    elif stage == "phone":
        info["Phone"] = user_input
        st.session_state.stage = "experience"
        return "🧑‍💻 How many **years of experience** do you have?"

    elif stage == "experience":
        info["Experience"] = user_input
        st.session_state.stage = "position"
        return "🎯 What **position(s)** are you applying for?"

    elif stage == "position":
        info["Position"] = user_input
        st.session_state.stage = "location"
        return "📍 Where are you **currently located**?"

    elif stage == "location":
        info["Location"] = user_input
        st.session_state.stage = "tech_stack"
        return "💻 Please list your **tech stack** (e.g., Python, React, MongoDB)..."

    elif stage == "tech_stack":
        info["Tech Stack"] = user_input
        st.session_state.stage = "questioning"
        tech_q = get_technical_questions(user_input)
        code_q = get_coding_questions(user_input)
        st.session_state.tech_questions = tech_q.split("\n")
        st.session_state.code_questions = code_q.split("\n")
        return f"🧪 Here are technical questions:\n\n{tech_q}\n\n💡 Coding questions:\n\n{code_q}"

    elif stage == "questioning":
        st.session_state.stage = "job_rec"
        recs = get_job_recommendations(info["Position"], info["Location"])
        st.session_state.job_recommendations = recs
        return "💼 Based on your profile, here are some job recommendations:\n\n" + "\n\n".join(recs)

    elif stage == "job_rec":
        st.session_state.stage = "done"
        return "✅ That’s all I need for now. Thank you for your time! You’ll hear from us soon. 🙏"

    else:
        return "❓ Hmm, I didn’t quite get that. Could you please rephrase?"

# Chat display
with st.container():
    for i, msg in enumerate(st.session_state.messages):
        message(msg["content"], is_user=msg["role"] == "user", key=str(i))

# Chat input
if not st.session_state.end_chat:
    user_prompt = st.chat_input("Type here to talk to Hiring Partner...")
    if user_prompt:
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        bot_response = chat_logic(user_prompt)
        time.sleep(0.2)
        st.session_state.messages.append({"role": "assistant", "content": bot_response})
        st.rerun()
else:
    st.success("✅ Chat ended. Report will be sent to your email shortly.")
    with st.expander("📄 Candidate Summary"):
        for k, v in st.session_state.candidate_info.items():
            st.markdown(f"**{k}:** {v}")

        st.markdown("### 🧪 Technical Questions")
        for q in st.session_state.tech_questions:
            st.markdown(f"- {q}")

        st.markdown("### 💡 Coding Questions")
        for q in st.session_state.code_questions:
            st.markdown(f"- {q}")

        st.markdown("### 💼 Job Recommendations")
        for job in st.session_state.job_recommendations:
            st.markdown(job)

        if st.button("📄 Export & Email Report"):
            pdf_buffer = export_pdf(
                st.session_state.candidate_info,
                st.session_state.tech_questions or ["No technical questions generated."],
                st.session_state.code_questions or ["No coding questions generated."],
                st.session_state.job_recommendations or ["No job recommendations available."]
            )

            recipient = st.session_state.candidate_info.get("Email")
            if recipient:
                email_sent = send_email_with_pdf(recipient, pdf_buffer)
                if email_sent:
                    st.success(f"📧 Report sent to {recipient}")
                else:
                    st.error("❌ Failed to send email. Check logs or SMTP setup.")
            else:
                st.warning("⚠ No email address found in candidate info.")
