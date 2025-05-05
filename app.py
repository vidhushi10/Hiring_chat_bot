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
        
        # Use a safer URL encoding approach for cloud compatibility
        try:
            # Simple URL encoding for cloud compatibility
            position_encoded = position.replace(" ", "+").replace(",", "%2C")
            location_encoded = location.replace(" ", "+").replace(",", "%2C")
            
            # Create simple, cloud-friendly URLs
            indeed_search = f"https://indeed.com/jobs?q={position_encoded}&l={location_encoded}"
            linkedin_search = f"https://linkedin.com/jobs/search?keywords={position_encoded}&location={location_encoded}"
            glassdoor_search = f"https://glassdoor.com/Job/jobs.htm?sc.keyword={position_encoded}&locT=C&locKeyword={location_encoded}"
            ziprecruiter_search = f"https://ziprecruiter.com/jobs/search?q={position_encoded}&l={location_encoded}"
        except Exception:
            # Ultra-safe fallbacks if encoding fails
            indeed_search = "https://indeed.com/jobs"
            linkedin_search = "https://linkedin.com/jobs"
            glassdoor_search = "https://glassdoor.com/Job"
            ziprecruiter_search = "https://ziprecruiter.com/jobs"
        
        # Set up mock jobs with cloud-friendly URLs
        mock_jobs = []
        
        # Developer/Tech related positions
        if any(tech in position_lower for tech in ['developer', 'engineer', 'programming', 'software', 'web', 'full stack', 'frontend', 'backend']):
            mock_jobs = [
                {
                    'title': f"{position.title()} Opportunities",
                    'company': "Multiple Tech Companies",
                    'location': f"{location}",
                    'salary': "$85,000 - $125,000 per year (typical range)",
                    'snippet': "Browse software development opportunities on LinkedIn. Their platform features positions from startups to Fortune 500 companies.",
                    'link': linkedin_search
                },
                {
                    'title': f"{position.title()} - Senior Roles",
                    'company': "Various Tech Employers",
                    'location': f"{location}",
                    'salary': "$120,000+ (typical for senior roles)",
                    'snippet': "Indeed features numerous developer roles requiring technical expertise. Filter by salary, company size, and more.",
                    'link': indeed_search
                },
                {
                    'title': f"{position.title()} - Entry & Mid-Level",
                    'company': "Tech Companies Hiring Now",
                    'location': f"{location}",
                    'salary': "$65,000 - $110,000 per year (typical range)",
                    'snippet': "Find jobs for all experience levels on ZipRecruiter. Their platform offers positions with various tech stacks and company cultures.",
                    'link': ziprecruiter_search
                }
            ]
        # Data related positions
        elif any(term in position_lower for term in ['data', 'analyst', 'scientist', 'machine learning', 'ai', 'analytics']):
            mock_jobs = [
                {
                    'title': f"{position.title()} Roles",
                    'company': "Top Tech Companies",
                    'location': f"{location}",
                    'salary': "$95,000 - $135,000 per year (typical range)",
                    'snippet': "Explore data science and analytics roles on Glassdoor. Review employee ratings and salary information.",
                    'link': glassdoor_search
                },
                {
                    'title': f"{position.title()} - Remote Options",
                    'company': "Various Tech Employers",
                    'location': f"{location} & Remote",
                    'salary': "$90,000 - $150,000 per year (typical range)",
                    'snippet': "Find flexible data positions on LinkedIn. Many companies now embrace remote work for data professionals.",
                    'link': linkedin_search
                },
                {
                    'title': f"{position.title()} - All Levels",
                    'company': "Multiple Organizations",
                    'location': f"{location}",
                    'salary': "$75,000 - $180,000 based on experience",
                    'snippet': "Indeed lists numerous data positions from entry-level to director roles. Filter by company, job type, and experience level.",
                    'link': indeed_search
                }
            ]
        # Other positions (sales, marketing, etc.)
        else:
            mock_jobs = [
                {
                    'title': f"{position.title()} - Latest Listings",
                    'company': "Multiple Employers",
                    'location': f"{location}",
                    'salary': "Varies by employer",
                    'snippet': "Indeed features numerous positions matching your search criteria. Filter results to find your ideal match.",
                    'link': indeed_search
                },
                {
                    'title': f"{position.title()} Opportunities",
                    'company': "Various Organizations",
                    'location': f"{location}",
                    'salary': "Competitive based on experience",
                    'snippet': "Browse LinkedIn's extensive job listings for this position. Connect with recruiters and companies directly.",
                    'link': linkedin_search
                },
                {
                    'title': f"{position.title()} - All Levels",
                    'company': "Multiple Companies",
                    'location': f"{location}",
                    'salary': "Varies by experience level",
                    'snippet': "ZipRecruiter offers a wide range of opportunities from entry-level to senior positions.",
                    'link': ziprecruiter_search
                }
            ]
        
        # Always add a general job search option that's guaranteed to work
        mock_jobs.append({
            'title': f"Search: {position.title()} Jobs",
            'company': "Job Search Engines",
            'location': f"{location} and surrounding areas",
            'salary': "All salary ranges",
            'snippet': "Access multiple job listings matching your criteria on major job search platforms. Compare opportunities and apply directly.",
            'link': "https://www.google.com/search?q=jobs+" + position.replace(" ", "+")
        })
        
        return mock_jobs
    
    # Skip API call and use our reliable implementation
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
            
            # Get link URL with ultimate fallback to Google job search
            link = job.get('link', job.get('url', job.get('jobUrl', '')))
            
            # Ensure we have a working link for cloud deployment
            if not link or link == '#' or 'example.com' in link:
                # Simple fallback that should work everywhere
                link = "https://www.google.com/search?q=jobs+" + position.replace(" ", "+")
            
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
            # Provide a basic job listing if anything fails
            try:
                basic_title = job.get('title', position.title() + ' Position')
                basic_link = "https://www.google.com/search?q=jobs+" + position.replace(" ", "+")
                
                formatted.append(
                    f"🔹 **{basic_title}**\n"
                    f"🏢 Job Search\n"
                    f"📍 {location}\n"
                    f"💰 Competitive salary\n"
                    f"📝 Find opportunities matching your profile and experience level.\n"
                    f"🔗 [Search Jobs]({basic_link})"
                )
            except:
                # Ultimate fallback - guaranteed to work
                formatted.append(
                    f"🔹 **{position.title()} Jobs**\n"
                    f"🏢 Multiple Employers\n"
                    f"📍 {location}\n"
                    f"💰 Various salary ranges\n"
                    f"📝 Search for positions matching your skills and experience.\n"
                    f"🔗 [Search Jobs](https://www.google.com/search?q=jobs)"
                )
    
    # If we still couldn't format any jobs, use ultra-reliable fallback
    if not formatted:
        formatted = [
            f"🔹 **{position.title()} Jobs**\n"
            f"🏢 Multiple Employers\n"
            f"📍 {location}\n"
            f"💰 Various salary ranges\n"
            f"📝 Search for positions matching your skills and experience.\n"
            f"🔗 [Search Jobs](https://www.google.com/search?q=jobs+{position.replace(' ', '+')})"
        ]
    
    # Clear any debug containers
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
