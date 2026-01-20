import io
import pandas as pd

# PDF extraction removed as per user request
# def extract_text_from_pdf(uploaded_file): ...

def to_excel(df):
    """
    Converts a pandas DataFrame to an Excel binary.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()
