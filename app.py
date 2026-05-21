import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
from datetime import datetime
import os
from PIL import Image

# ১. আপনার জেমিনি এআই চাবি (পুরনো চাবিটিই এখানে রাখা হলো)
API_KEY = "AIzaSyCuBt_XKXQRiiLV5ueUZw6aF9LoNDO9DPg"
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

# --- স্ট্রিমলিট ইউজার ইন্টারফেস (নতুন রাজকীয় থিম) ---
st.set_page_config(page_title="Moonlight Smart Ledger", layout="wide")

# ব্যাকগ্রাউন্ড এবং বর্ডারের জন্য কাস্টম সুন্দর কালার ডিজাইন
st.markdown("""
    <style>
    .reportview-container { background: #f0f4f8; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .card {
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        text-align: center;
        color: white;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# মাঝখানে মহাদেবের লোগো এবং পবিত্র স্লোগান
col_left, col_mid, col_right = st.columns([1, 2, 1])
with col_mid:
    st.markdown('<div style="text-align: center; padding-top: 10px;">', unsafe_allow_html=True)
    try:
        logo_image = Image.open("SHIVE THAKUR.jfif")
        st.image(logo_image, width=280, use_column_width=False)
    except Exception:
        pass
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
        <div style="text-align: center; margin-top: -10px; margin-bottom: 20px;">
            <p style="color: #D4AF37; font-size: 26px; font-weight: bold; letter-spacing: 3px;">
                || हर हर महादेव ||
            </p>
        </div>
    """, unsafe_allow_html=True)

# ডাটা লোড করা লাইভ হিসাবের জন্য
df_current = load_ledger()

# --- ২. লাইভ ড্যাশবোর্ড বক্স (আজকের মোট হিসাবের বাক্স) ---
total_sales_money = 0.0
total_stock_in_qty = 0
total_stock_out_qty = 0

if not df_current.empty:
    # মোট টাকা, স্টক ইন এবং স্টক আউটের যোগফল বের করা
    total_sales_money = df_current["মোট টাকা"].sum()
    total_stock_in_qty = df_current["স্টক ইন (পিস)"].sum()
    total_stock_out_qty = df_current["সেলস/স্টক আউট (পিস)"].sum()

dash_col1, dash_col2, dash_col3 = st.columns(3)
with dash_col1:
    st.markdown(f'<div class="card" style="background-color: #2e7d32;">💰 মোট বিক্রি<br><span style="font-size: 22px;">{total_sales_money:,.2f} টাকা</span></div>', unsafe_allow_html=True)
with dash_col2:
    st.markdown(f'<div class="card" style="background-color: #1565c0;">📦 মোট স্টক ইন (জমা)<br><span style="font-size: 22px;">{total_stock_in_qty} পিস</span></div>', unsafe_allow_html=True)
with dash_col3:
    st.markdown(f'<div class="card" style="background-color: #e65100;">🚛 মোট স্টক আউট (ডেলিভারি)<br><span style="font-size: 22px;">{total_stock_out_qty} পিস</span></div>', unsafe_allow_html=True)

st.write("---")

# স্ক্রিন দুটি ভাগে ভাগ করা (বামদিকে নতুন এন্ট্রি, ডানদিকে লাইভ এক্সেল খাতা)
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<h3 style="color: #004080;">📝 নতুন ডিজিটাল এন্ট্রি করুন</h3>', unsafe_allow_html=True)
    
    # --- ৩. ক্যালেন্ডার বা তারিখ বাছার বোতাম ---
    selected_date = st.date_input("হিসাবের তারিখ বাছুন:", datetime.now())
    selected_time = datetime.now().strftime("%H:%M")
    final_datetime = f"{selected_date.strftime('%d-%m-%Y')} {selected_time}"
    
    user_message = st.text_area("মেসেজ লিখুন (যেমন: 7D SET CHADOR 50 PC 238 TAKA):", height=100)
    
    if st.button("লেজারে যোগ করুন", type="primary"):
        if user_message.strip() != "":
            with st.spinner("এআই আপনার মেসেজটি পড়ে হিসাব তৈরি করছে..."):
                ai_result = parse_message_with_ai(user_message)
                
                if ai_result:
                    df = load_ledger()
                    rate = float(ai_result.get("rate", 0))
                    
                    stock_in_qty = int(ai_result.get("stock_in", 0))
                    stock_out_qty = int(ai_result.get("stock_out", 0))
                    qty = stock_in_qty if stock_in_qty > 0 else stock_out_qty
                    
                    total_amount = qty * rate
                    
                    new_row = {
                        "তারিখ": final_datetime, # ক্যালেন্ডার থেকে নেওয়া তারিখ
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
        
        # দুই বোতামের জন্য সাব-কলাম
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            # ডাউনলোড বোতাম
            with open(EXCEL_FILE, "rb") as file:
                st.download_button(
                    label="📥 এক্সেল ডাউনলোড করুন",
                    data=file,
                    file_name=EXCEL_FILE,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        with btn_col2:
            # --- ৪. ভুল হলে এন্ট্রি মুছে ফেলার লাল বোতাম ---
            if st.button("🗑️ শেষ ভুল এন্ট্রিটি মুছুন", type="secondary", help="এটি টিপলে একদম শেষ লাইনের হিসাবটি মুছে যাবে"):
                df_delete = load_ledger()
                if not df_delete.empty:
                    df_delete = df_delete.drop(df_delete.index[-1]) # শেষ রো কেটে দেওয়া
                    df_delete.to_excel(EXCEL_FILE, index=False)
                    st.warning("⚠️ শেষ এন্ট্রিটি খাতা থেকে মুছে দেওয়া হয়েছে!")
                    st.rerun()
    else:
        st.info("এখনো কোনো রেকর্ড নেই। বামদিকে মেসেজ লিখে প্রথম এন্ট্রি করুন।")
