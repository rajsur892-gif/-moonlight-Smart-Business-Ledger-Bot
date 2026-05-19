import streamlit as st
import google.generativeai as genai
import pandas as pd

st.title("Smart Business Ledger Bot 📊")
st.write("আপনার ব্যবসার স্টক এবং সেলস আপডেট করার জন্য নিচে মেসেজ লিখুন।")

# মেসেজ ইনপুট বক্স
user_input = st.text_input("এখানে লিখুন (যেমন: আজ ৫০ পিস মাল ডেলিভারি দিলাম):")

if st.button("আপডেট করুন"):
    if user_input:
        st.success(f"আপনার মেসেজটি রেকর্ড করা হয়েছে: {user_input}")
    else:
        st.warning("অনুগ্রহ করে কিছু একটা লিখুন।")
        import streamlit as st
import google.genrativeai as genai
import pandas as pd
import json
from datetime import datetime
import os

# ১. আপনার সঠিক API Key
API_KEY = "AIzaSyDuq2YKw8M3PHpsxtaSv6teOH7kZya0fPk"

# লেজার ফাইলের নাম
EXCEL_FILE = "business_ledger.xlsx"

# ২. এক্সেল ফাইল লোড বা তৈরি করার ফাংশন (নতুন কলাম সহ)
def load_ledger():
    columns = ["তারিখ", "বিবরণ (Item)", "নাম (Party)", "স্টক ইন (In)", "স্টক আউট (Out)", "দর (Rate)", "মোট টাকা (Amount)"]
    if os.path.exists(EXCEL_FILE):
        try:
            df = pd.read_excel(EXCEL_FILE)
            # যদি নতুন কলামগুলো না থাকে তবে যোগ করবে
            for col in columns:
                if col not in df.columns:
                    df[col] = 0
            return df[columns] # কলামের ক্রম ঠিক রাখার জন্য
        except:
            return pd.DataFrame(columns=columns)
    else:
        return pd.DataFrame(columns=columns)

# পৃষ্ঠা সেটআপ
st.set_page_config(layout="wide")
st.title("Smart Business Ledger Bot 📊")
st.write("আপনার ব্যবসার স্টক, সেলস এবং টাকার হিসাব আপডেট করার জন্য নিচে মেসেজ লিখুন।")

# ৩. লেজার ডেটা লোড করা
ledger_df = load_ledger()

# স্ক্রিনটিকে দুটি ভাগে ভাগ করা (বামদিকে ইনপুট, ডানদিকে লাইভ এক্সেল)
col1, col2 = st.columns([1, 1.3])

with col1:
    st.subheader("📝 নতুন এন্ট্রি করুন")
    user_input = st.text_input("মেসেজ লিখুন (যেমন: 7D SET CHADOR 200 PC 218 TAKA):", key="input")
    
    if st.button("লেজারে যোগ করুন"):
        if user_input:
            with st.spinner("AI ডেটা প্রসেস করছে..."):
                try:
                    # ৪. ক্লায়েন্ট সেটআপ
                    client = genai.Client(api_key=API_KEY)
                    
                    prompt = f"""
                    You are a professional business accounting assistant. Analyze the text and extract structured information.
                    Respond ONLY with a valid JSON object. Do not include markdown formatting or backticks.
                    
                    Text: "{user_input}"
                    
                    JSON format to return:
                    {{
                        "item": "Name or specifications of the product in Bengali/English (e.g., 7D SET CHADOR)",
                        "party": "Name of customer/supplier/brand if mentioned. If not, use 'নগদ'",
                        "type": "Either 'IN' if stock is added/received or 'OUT' if sold/delivered",
                        "quantity": integer number of pieces/units,
                        "rate": number indicating price per unit/piece. If not specified, use 0
                    }}
                    """
                    
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                    )
                    
                    # JSON পার্স করা
                    clean_text = response.text.strip().replace("```json", "").replace("```", "")
                    data = json.loads(clean_text)
                    
                    # ৫. দর ও মোট টাকা হিসাব করা
                    current_date = datetime.now().strftime("%d-%m-%Y")
                    qty = data.get('quantity', 0)
                    rate = data.get('rate', 0)
                    total_amount = qty * rate # অটোমেটিক গুণ করবে
                    
                    stock_in = qty if data['type'] == 'IN' else 0
                    stock_out = qty if data['type'] == 'OUT' else 0
                    
                    new_row = {
                        "তারিখ": current_date,
                        "বিবরণ (Item)": data['item'],
                        "নাম (Party)": data['party'],
                        "স্টক ইন (In)": stock_in,
                        "স্টক আউট (Out)": stock_out,
                        "দর (Rate)": rate,
                        "মোট টাকা (Amount)": total_amount
                    }
                    
                    ledger_df = pd.concat([ledger_df, pd.DataFrame([new_row])], ignore_index=True)
                    
                    try:
                        ledger_df.to_excel(EXCEL_FILE, index=False)
                    except:
                        ledger_df.to_csv("business_ledger.csv", index=False)
                    
                    st.success("✅ লেজারে সফলভাবে আপডেট করা হয়েছে!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"ভুলটি হলো: {str(e)}")
        else:
            st.warning("অনুগ্রহ করে সঠিক মেসেজ দিন।")

with col2:
    st.subheader("📈 লাইভ লেজার খাতা (Excel View)")
    if not ledger_df.empty:
        # টেবিলটিকে সুন্দর করে দেখানো
        st.dataframe(ledger_df, use_container_width=True)
        
        # নিচে একটি ছোট্ট হিসাব প্যানেল (Summary)
        st.write("---")
        total_in = ledger_df["স্টক ইন (In)"].sum()
        total_out = ledger_df["স্টক আউট (Out)"].sum()
        total_cash = ledger_df["মোট টাকা (Amount)"].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("মোট স্টক ইন (Total In)", f"{total_in} পিস")
        c2.metric("মোট স্টক আউট (Total Out)", f"{total_out} পিস")
        c3.metric("মোট বেচাকেনা (Total Sales)", f"₹ {total_cash}/-")
    else:
        st.info("এখনো কোনো রেকর্ড নেই। বামদিকে মেসেজ লিখে প্রথম এন্ট্রি করুন।")
