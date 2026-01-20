import streamlit as st
import pandas as pd
from scraper import get_industries, get_countries, scrape_companies
from ai_matcher import match_company_with_profile
from utils import to_excel

st.set_page_config(page_title="Lusha Company Search", page_icon="🔍", layout="wide")

# ... (CSS remains same - assumed initialized before this block if not replacing whole file, 
# but here we are replacing imports so need to be careful. The user's file has CSS block.
# I will replace from imports down to the search button logic)

# Initialize Session State for Industries and Countries
if 'industries' not in st.session_state:
    st.session_state.industries = []
if 'countries' not in st.session_state:
    st.session_state.countries = []
if 'selected_industry_url' not in st.session_state:
    st.session_state.selected_industry_url = None

st.title("🏢 Company Search & Match Platform")
st.markdown("Find your ideal B2B companies and check your compatibility score.")

# Sidebar
with st.sidebar:
    st.header("Search Filters")
    
    # 1. Fetch Industries (Button to load)
    if st.button("🔄 Iterate Industries"):
        with st.spinner("Fetching Industries..."):
            st.session_state.industries = get_industries()
    
    industry_names = [i['name'] for i in st.session_state.industries]
    selected_industry = st.selectbox("Select Industry", options=[""] + industry_names)
    
    # Find selected industry URL
    selected_industry_data = next((i for i in st.session_state.industries if i['name'] == selected_industry), None)
    
    # 2. Fetch Countries when Industry Selected
    if selected_industry_data:
        if st.session_state.selected_industry_url != selected_industry_data['url']:
             st.session_state.selected_industry_url = selected_industry_data['url']
             with st.spinner(f"Fetching countries for {selected_industry}..."):
                st.session_state.countries = get_countries(selected_industry_data['url'])
    
    country_names = [c['name'] for c in st.session_state.countries]
    selected_country = st.selectbox("Select Location", options=[""] + country_names)
    
    # Find selected country URL
    selected_country_data = next((c for c in st.session_state.countries if c['name'] == selected_country), None)

    st.markdown("---")
    st.markdown("---")
    st.header("AI Matching")
    
    # Securely access API Key from secrets
    try:
        api_key = st.secrets["secrets"]["OPENAI_API_KEY"]
    except:
        api_key = st.text_input("OpenAI API Key", type="password")
        if not api_key:
            st.warning("Please add your API Key to .streamlit/secrets.toml or enter it above.")
            
    user_profile_text = st.text_area("Paste Profile/Resume Text", height=200, placeholder="Paste your resume or profile description here...")
    
    st.markdown("---")
    max_results = st.slider("Max Companies to Fetch", min_value=10, max_value=200, value=50, step=10)
    search_btn = st.button("Search Companies")

# Main Content
if search_btn:
    if not selected_country_data:
        st.error("Please select both an Industry and a Location.")
    else:
        with st.spinner(f"Scraping companies in {selected_industry}, {selected_country} (Max: {max_results})..."):
            # Real Call with direct URL
            data = scrape_companies(selected_country_data['url'], max_results=max_results)
            
            if not data:
                st.warning("No companies found or scraper was blocked. Try different keywords.")
            else:
                st.success(f"Found {len(data)} companies!")
                
                # Store results in session state to persist between reruns (if analyzing)
                # Automatic AI Analysis
                if api_key and user_profile_text:
                    st.info("Profile loaded. Analyzing matches...")
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    analyzed_results = []
                    total = len(data)
                    
                    for i, company in enumerate(data):
                         status_text.text(f"Analyzing {i+1}/{total}: {company['name']}...")
                         match_data = match_company_with_profile(
                             str(company), 
                             user_profile_text, 
                             api_key
                         )
                         company.update(match_data)
                         analyzed_results.append(company)
                         progress_bar.progress((i + 1) / total)
                    
                    st.session_state.last_results = analyzed_results # Update with analyzed data
                    progress_bar.empty()
                    status_text.empty()
                    st.success("Analysis Complete!")

    # Display Results
    if 'last_results' in st.session_state and st.session_state.last_results:
        results = st.session_state.last_results
        
        st.markdown(f"### Results ({len(results)})")
        
        if not api_key:
             st.warning("Enter OpenAI API Key to enable AI analysis.")
        elif not user_profile_text:
             st.warning("Paste a profile to enable AI matching.")
            
            # Display loop continues below...
             
         # Display Loop header
         if st.session_state.last_results:
            st.markdown(f"### Results ({len(st.session_state.last_results)})") 
         
         for company in st.session_state.last_results:
            is_analyzed = 'match_score' in company
            
            if is_analyzed:
                score = company.get('match_score', 0)
                color = "green" if score > 70 else "orange" if score > 40 else "red"
                score_text = f"{score}% Match"
                reasoning_text = company.get('reasoning', 'No reasoning provided.')
            else:
                color = "gray"
                score_text = "Analysis Pending"
                reasoning_text = "Click 'Analyze Matches' button above to generate scores."
            
            with st.container():
                st.markdown(f"""
                <div class="company-card">
                    <div style="display:flex; justify-content:space-between;">
                        <h3>{company.get('name', 'Unknown Company')}</h3>
                        <h3 style="color:{color};">{score_text}</h3>
                    </div>
                    <p><strong>Website:</strong> <a href="{company.get('website_url', company.get('url', '#'))}" target="_blank">Link</a> | 
                       <strong>LinkedIn:</strong> <a href="{company.get('linkedin', '#')}" target="_blank">Profile</a> |
                       <span style="font-size:0.8em; color:gray;">(Lusha: <a href="{company.get('url', '#')}" target="_blank">Source</a>)</span></p>
                    <p><em>{reasoning_text}</em></p>
                </div>
                """, unsafe_allow_html=True)

        # Export
        if 'last_results' in st.session_state:
            df = pd.DataFrame(st.session_state.last_results)
            
            # Convert to Excel
            excel_data = to_excel(df)
            st.markdown("### 📥 Export Data")
            st.download_button(
                label="Download Results as Excel",
                data=excel_data,
                file_name=f"lusha_companies_{selected_industry}_{selected_country}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.dataframe(df)
