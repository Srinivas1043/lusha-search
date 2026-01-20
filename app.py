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
    st.header("AI Matching")
    api_key = st.text_input("OpenAI API Key", type="password")
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
                st.session_state.last_results = data
                
    # Display Results & AI Control
    if 'last_results' in st.session_state and st.session_state.last_results:
        results = st.session_state.last_results
        
        # AI Analysis Section
        st.markdown("### 🤖 AI Compatibility Analysis")
        
        if not api_key:
             st.warning("Enter OpenAI API Key to enable analysis.")
        else:
             if st.button("✨ Analyze Matches with AI (Batch Process)"):
                 with st.spinner("Analyzing companies in batches..."):
                     from ai_matcher import batch_match_companies
                     
                     # Process in batches of 20
                     batch_size = 20
                     analyzed_results = []
                     
                     for i in range(0, len(results), batch_size):
                         batch = results[i:i+batch_size]
                         # Call AI
                         ai_response = batch_match_companies(batch, user_profile_text, api_key)
                         
                         # Merge results
                         for idx, company in enumerate(batch):
                             # Key in response corresponds to index in the batch list (0 to batch_size-1)
                             match_data = ai_response.get(str(idx), {"match_score": 0, "reasoning": "AI Error"})
                             company.update(match_data)
                             analyzed_results.append(company)
                     
                     st.session_state.last_results = analyzed_results
                     st.success("Analysis Complete!")
                     st.rerun()

        # Display Loop
        for company in st.session_state.last_results:
            score = company.get('match_score', 0)
            color = "green" if score > 70 else "orange" if score > 40 else "red"
            
            with st.container():
                st.markdown(f"""
                <div class="company-card">
                    <div style="display:flex; justify-content:space-between;">
                        <h3>{company.get('name', 'Unknown Company')}</h3>
                        <h3 style="color:{color};">{score}% Match</h3>
                    </div>
                    <p><strong>Website:</strong> <a href="{company.get('url', '#')}" target="_blank">Link</a> | 
                       <strong>LinkedIn:</strong> <a href="{company.get('linkedin', '#')}" target="_blank">Profile</a></p>
                    <p><em>{company.get('reasoning', 'Click Analyze to see AI reasoning')}</em></p>
                </div>
                """, unsafe_allow_html=True)

                # Export
                if 'last_results' in st.session_state:
                    df = pd.DataFrame(st.session_state.last_results)
                    
                    # Convert to Excel
                    excel_data = to_excel(df)
                    st.download_button(
                        label="📥 Download Results as Excel",
                        data=excel_data,
                        file_name=f"lusha_companies_{selected_industry}_{selected_country}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    st.dataframe(df)
