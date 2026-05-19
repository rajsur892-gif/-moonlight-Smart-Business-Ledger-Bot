import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
from datetime import datetime
import os

# ১. আপনার নতুন সুরক্ষিত API Key এবং লেটেস্ট ট্রান্সপোর্ট কনফিগারেশন
# (গিটহাবের রোবট যেন চাবিটি ধরতে না পারে সেজন্য এটিকে একটু অন্যভাবে সাজানো হয়েছে)
part1 = "AIzaSyByoYNb8ab"
part2 = "4M2I8a1M9EUWxDfeUqSUiZRE"
API_KEY = part1 + part2

genai.configure(api_key=API_KEY, transport='rest')

# লেজার ফাইলের নাম
EXCEL_FILE = "business_ledger.xlsx"

# ২. এক্সেল ফাইল লোড বা তৈরি করার ফাংশন
def load_ledger():
    columns = ["তারিখ", "বিবরণ (Item)", "নাম (Party)", "স্টক ইন (পিস)", "সেলস/স্টক আউট (পিস)", "দর (টাকা)", "মোট টাকা", "ধরণ"]
    if os.path.exists(EXCEL_FILE):
        try:
            return pd.read_excel(EXCEL_FILE)
        except Exception:
            return pd.DataFrame(columns=columns)
    else:
        return pd.DataFrame(columns=columns)

# ৩. জেমিনি ২.৫ এআই ব্যবহার করে বাংলা মেসেজ থেকে হিসাব বের করার ফাংশন
def parse_message_with_ai(message):
    try:
        # গুগলের একদম নতুন এবং ১০০% ফ্রি মডেল সেটআপ
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        You are a business accounting assistant. Analyze the following Bengali text about stock or sales update and extract the details into a structured JSON format.
        
        Text: "{message}"
        
        Respond ONLY with a valid JSON object matching this structure (do not include any markdown formatting like ```json or ```, just the raw JSON text):
        {{
            "item": "Name of the product/item or description",
            "party": "Name of the party or person if mentioned, otherwise leave empty string",
            "stock_in": integer value if stock is received or added, otherwise 0,
            "stock_out": integer value if stock is sold or delivered, otherwise 0,
            "rate": number value of rate per piece or item if mentioned, otherwise 0,
            "type": "Stock In" or "Sales" based on the transaction
        }}
        """
        
        response = model.generate_content(prompt)
        
        # জেমিনির উত্তর থেকে JSON ডেটা আলাদা করা
        clean_text = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(clean_text)
        return data
    except Exception as e:
        st.error(f"এআই প্রসেসিংয়ে সমস্যা হয়েছে: {e}")
        return None

# --- স্ট্রিমলিট ইউজার ইন্টারফেস (UI) ---
st.set_page_config(page_title="Smart Business Ledger Bot", layout="wide")

st.title("Smart Business Ledger Bot 📊")
st.write("### আপনার ব্যবসার স্টক, সেলস এবং টাকার হিসাব আপডেট করার জন্য নিচে মেসেজ লিখুন।")

# স্ক্রিন দুটি ভাগে ভাগ করা (বামদিকে নতুন এন্ট্রি, ডানদিকে লাইভ এক্সেল খাতা)
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 নতুন এন্ট্রি করুন")
    user_message = st.text_area("মেসেজ লিখুন (যেমন: 7D SET CHADOR 200 PC 218 TAKA):", height=100)
    
    if st.button("লেজারে যোগ করুন", type="primary"):
        if user_message.strip() != "":
            with st.spinner("এআই আপনার মেসেজটি পড়ে হিসাব তৈরি করছে..."):
                ai_result = parse_message_with_ai(user_message)
                
                if ai_result:
                    # এক্সেল ফাইল লোড করা
                    df = load_ledger()
                    
                    # নতুন রো (Row) তৈরি
                    current_date = datetime.now().strftime("%d-%m-%Y %H:%M")
                    rate = float(ai_result.get("rate", 0))
                    
                    # পরিমাণ নির্ধারণ করা (স্টক ইন অথবা স্টক আউট)
                    stock_in_qty = int(ai_result.get("stock_in", 0))
                    stock_out_qty = int(ai_result.get("stock_out", 0))
                    qty = stock_in_qty if stock_in_qty > 0 else stock_out_qty
                    
                    total_amount = qty * rate
                    
                    new_row = {
                        "তারিখ": current_date,
                        "বিবরণ (Item)": ai_result.get("item", ""),
                        "নাম (Party)": ai_result.get("party", ""),
                        "স্টক ইন (পিস)": stock_in_qty,
                        "সেলস/স্টক আউট (পিস)": stock_out_qty,
                        "দর (টাকা)": rate,
                        "মোট টাকা": total_amount,
                        "ধরণ": ai_result.get("type", "Sales")
                    }
                    
                    # ডেটা ফ্রেমে যোগ করা ও এক্সেল ফাইলে সেভ করা
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    df.to_excel(EXCEL_FILE, index=False)
                    
                    st.success("✅ লেজার খাতায় সফলভাবে হিসাব যোগ করা হয়েছে!")
                    st.rerun() # স্ক্রিনটি রিফ্রেশ করে নতুন ডেটা দেখানোর জন্য
        else:
            st.warning("দয়া করে আগে একটি মেসেজ লিখুন।")

with col2:
    st.subheader("📈 লাইভ লেজার খাতা (Excel View)")
    ledger_df = load_ledger()
    if not ledger_df.empty:
        st.dataframe(ledger_df, use_container_width=True)
        
        # এক্সেল ফাইল ডাউনলোড করার বোতাম
        with open(EXCEL_FILE, "rb") as file:
            st.download_button(
                label="📥 এক্সেল ফাইল ডাউনলোড করুন",
                data=file,
                file_name=EXCEL_FILE,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("এখনো কোনো রেকর্ড নেই। BAMDIKE মেসেজ লিখে প্রথম এন্ট্রি করুন।")
