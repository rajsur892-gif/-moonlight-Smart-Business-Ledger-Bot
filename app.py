import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
from datetime import datetime
import os
from PIL import Image  # গিটহাবের ছবি সরাসরি পড়ার জন্য

# ১. আপনার জেমিনি এআই চাবি (পুরনো চাবিটিই এখানে রাখা হলো)
API_KEY = "AIzaSyDuq2YKw8M3PHpsxtaSv6teOH7kZya0fPk"
genai.configure(api_key=API_KEY)

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

# ৩. জেমিনি এআই ফাংশন
def parse_message_with_ai(message):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"""
        You are a business accounting assistant. Analyze the following Bengali text about stock or sales update and extract the details into a structured JSON format.
        Text: "{message}"
        Respond ONLY with a valid JSON object matching this structure:
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
        clean_text = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(clean_text)
        return data
    except Exception as e:
        st.error(f"এআই প্রসেসিংয়ে সমস্যা হয়েছে: {e}")
        return None

# --- স্ট্রিমলিট ইউজার ইন্টারফেস (বড় লোগো এবং কালারফুল ডিজাইন) ---
st.set_page_config(page_title="Moonlight Smart Ledger", layout="wide")

# মাঝখানে লোগো এবং নাম সাজানোর জন্য ৩টি কলাম তৈরি করা হলো
col_left, col_mid, col_right = st.columns([1, 2, 1])

with col_mid:
    # গিটহাব থেকে সরাসরি ছবি লোড করা এবং এর সাইজ বড় করা (width=300 করা হলো)
    # আর ছবিটিকে নামের থেকে সামান্য একটু ওপরে তুলতে padding-top দেওয়া হলো
    st.markdown('<div style="text-align: center; padding-top: 20px;">', unsafe_allow_html=True)
    try:
        logo_image = Image.open("SHIVE THAKUR.jfif")
        # ছবির সাইজ আগের থেকে প্রায় দ্বিগুণ বড় করে দেওয়া হলো
        st.image(logo_image, width=300, caption="Moonlight Business Ledger", use_column_width=False)
    except Exception:
        pass  # ছবি না পেলে অ্যাপ যেন ক্র্যাশ না করে
    st.markdown('</div>', unsafe_allow_html=True)

    # কালারফুল নাম এবং মহাদeb স্লোগান (এদের পজিশন ছবির থেকে সামান্য একটু নিচে রাখা হলো padding-top: 10px দিয়ে)
    st.markdown("""
        <div style="text-align: center; padding-top: 10px;">
            <h1 style="color: #004080; font-family: 'Arial Black', Gadget, sans-serif; font-size: 42px; margin-bottom: 0px; margin-top: -20px;">
                🌙 Moonlight Smart Ledger
            </h1>
            <p style="color: #D4AF37; font-size: 20px; font-weight: bold; letter-spacing: 2px; margin-top: 5px;">
                || हर हर महादेव ||
            </p>
        </div>
    """, unsafe_allow_html=True)

st.write("---")
st.write("### 📊 আপনার ব্যবসার স্টক, সেলস এবং টাকার হিসাব আপডেট করার জন্য নিচে মেসেজ লিখুন।")

# স্ক্রিন দুটি ভাগে ভাগ করা (বামদিকে নতুন এন্ট্রি, ডানদিকে লাইভ এক্সেল খাতা)
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<h3 style="color: #004080;">📝 নতুন ডিজিটাল এন্ট্রি করুন</h3>', unsafe_allow_html=True)
    user_message = st.text_area("মেসেজ লিখুন (যেমন: 7D SET CHADOR 50 PC 238 TAKA):", height=100)
    
    if st.button("লেজারে যোগ করুন", type="primary"):
        if user_message.strip() != "":
            with st.spinner("এআই আপনার মেসেজটি পড়ে হিসাব তৈরি করছে..."):
                ai_result = parse_message_with_ai(user_message)
                
                if ai_result:
                    df = load_ledger()
                    current_date = datetime.now().strftime("%d-%m-%Y %H:%M")
                    rate = float(ai_result.get("rate", 0))
                    
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
                    
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    df.to_excel(EXCEL_FILE, index=False)
                    
                    st.success("✅ লেজার খাতায় সফলভাবে হিসাব যোগ করা হয়েছে!")
                    st.rerun()
        else:
            st.warning("দয়া করে আগে একটি মেসেজ লিখুন।")

with col2:
    st.markdown('<h3 style="color: #004080;">📈 লাইভ লেজার খাতা (Excel View)</h3>', unsafe_allow_html=True)
    ledger_df = load_ledger()
    if not ledger_df.empty:
        st.dataframe(ledger_df, use_container_width=True)
        
        # ডাউনলোড বোতাম
        with open(EXCEL_FILE, "rb") as file:
            st.download_button(
                label="📥 এক্সেল ফাইল ডাউনলোড করুন",
                data=file,
                file_name=EXCEL_FILE,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("এখনো কোনো রেকর্ড নেই। বামদিকে মেসেজ লিখে প্রথম এন্ট্রি করুন।")
