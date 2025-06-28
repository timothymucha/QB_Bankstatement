import streamlit as st
import pandas as pd
import csv
from io import StringIO
from datetime import datetime

def convert_to_iif(df):
    output = StringIO()
    writer = csv.writer(output, delimiter='\t')

    # Write headers
    writer.writerow(["!TRNS", "TRNSTYPE", "DATE", "ACCNT", "NAME", "AMOUNT", "DOCNUM", "MEMO"])
    writer.writerow(["!SPL", "TRNSTYPE", "DATE", "ACCNT", "NAME", "AMOUNT", "DOCNUM",
                     "MEMO", "QNTY", "PRICE", "CLASS", "TAXABLE", "INVITEM"])
    writer.writerow(["!ENDTRNS"])

    df = df[df['Status'].str.lower() == 'closed']

    for _, row in df.iterrows():
        try:
            date_obj = pd.to_datetime(row['Date'], errors='coerce')
            date = date_obj.strftime('%m/%d/%Y') if not pd.isna(date_obj) else ""
        except:
            date = ""

        docnum = f"RCP-{str(row['Receipt number']).strip().replace(' ', '').replace('/', '-')}"
        amount = float(row['Net sales'])
        payment_type = row['Payment type'].strip().lower()

        if payment_type == 'mpesa':
            bank_account = 'Bank:M-Pesa'
        elif payment_type == 'cash':
            bank_account = 'Bank:Cash'
        elif payment_type == 'visa card':
            bank_account = 'Bank:Visa'
        else:
            continue  # Skip unknown payment types

        customer = "Walk In"

        # TRNS row: money received into bank
        writer.writerow(["TRNS", "PAYMENT", date, bank_account, customer,
                         f"{amount:.2f}", docnum, "Imported Receipt"])

        # SPL row: reduce A/R
        writer.writerow(["SPL", "PAYMENT", date, "Accounts Receivable", customer,
                         f"{-amount:.2f}", docnum, "Payment for receipt", "", "", "", "N", ""])

        writer.writerow(["ENDTRNS"])

    return output.getvalue()


st.title("📥 Bank Statement to IIF Converter")

uploaded_file = st.file_uploader("Upload CSV Bank Statement", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("✅ Loaded Data Preview", df.head())

    required_cols = {'Date', 'Receipt number', 'Net sales', 'Status', 'Payment type'}
    if not required_cols.issubset(set(df.columns)):
        st.error(f"Missing required columns: {required_cols - set(df.columns)}")
    else:
        iif_data = convert_to_iif(df)
        st.download_button("⬇️ Download .IIF File", data=iif_data, file_name="bank_import.iif", mime="text/plain")
