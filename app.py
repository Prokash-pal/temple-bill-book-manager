import streamlit as st
import pandas as pd
from datetime import date
import io

# পেজ সেটআপ
st.set_page_config(page_title="Temple Bill Book Manager", layout="wide")
st.title("🙏 মন্দির বিল বই ম্যানেজমেন্ট সিস্টেম")

# Session State তৈরি করা (যাতে পেজ রিফ্রেশ হলেও ডেটা থাকে)
if 'master_df' not in st.session_state:
    st.session_state.master_df = pd.DataFrame()
if 'book_df' not in st.session_state:
    st.session_state.book_df = pd.DataFrame()
if 'report_df' not in st.session_state:
    st.session_state.report_df = pd.DataFrame(columns=["Date", "Devotee_ID", "Name", "Mobile", "Book_ID", "Start_Bill", "End_Bill", "Status"])

# সাইডবার - ফাইল আপলোড
st.sidebar.header("১. ফাইল আপলোড করুন")
master_file = st.sidebar.file_uploader("Master List আপলোড করুন (Excel)", type=["xlsx"])
book_file = st.sidebar.file_uploader("Book List আপলোড করুন (Excel)", type=["xlsx"])

if master_file is not None and st.session_state.master_df.empty:
    st.session_state.master_df = pd.read_excel(master_file)
    st.sidebar.success("Master List আপলোড সফল!")

if book_file is not None and st.session_state.book_df.empty:
    df = pd.read_excel(book_file)
    if 'Status' not in df.columns:
        df['Status'] = 'Available'
    st.session_state.book_df = df
    st.sidebar.success("Book List আপলোড সফল!")

# মেইন উইন্ডো - ৩টি ট্যাব
tab1, tab2, tab3 = st.tabs(["📖 বই দিন (Issue)", "↩️ বই ফেরত (Return)", "📊 রিপোর্ট ও ডাউনলোড (Download)"])

# --- TAB 1: ISSUE BOOK ---
with tab1:
    st.subheader("ভক্তকে নতুন বই ইস্যু করুন")
    if not st.session_state.master_df.empty and not st.session_state.book_df.empty:
        col1, col2 = st.columns(2)
        with col1:
            dev_id = st.text_input("Devotee ID লিখুন:")
        with col2:
            num_books = st.number_input("কটি বই দেবেন?", min_value=1, step=1)
            
        if st.button("বই ইস্যু করুন", type="primary"):
            try:
                # ভক্তের নাম ও মোবাইল খোঁজা (আপনার মাস্টার শিটের কলামের নাম অনুযায়ী)
                dev_id_int = int(dev_id)
                devotee = st.session_state.master_df[st.session_state.master_df['ID'] == dev_id_int]
                
                if devotee.empty:
                    st.error("এই ID মাস্টার লিস্টে পাওয়া যায়নি!")
                else:
                    dev_name = devotee['NAME'].values[0]
                    dev_mobile = devotee['MOBILE - 1'].values[0]
                    
                    # Available বই খোঁজা
                    available_books = st.session_state.book_df[st.session_state.book_df['Status'] == 'Available']
                    
                    if len(available_books) < num_books:
                        st.error(f"স্টকে পর্যাপ্ত বই নেই! মাত্র {len(available_books)} টি বই Available আছে।")
                    else:
                        # প্রথম থেকে ফাঁকা বইগুলো নেওয়া
                        books_to_issue = available_books.head(num_books)
                        
                        new_records = []
                        today = date.today().strftime("%d-%m-%Y")
                        
                        for index, row in books_to_issue.iterrows():
                            b_id = row['Book_ID']
                            # Book List এ Status আপডেট করা
                            st.session_state.book_df.loc[st.session_state.book_df['Book_ID'] == b_id, 'Status'] = 'Issued'
                            
                            # রিপোর্টে রেকর্ড যোগ করা
                            new_records.append({
                                "Date": today, "Devotee_ID": dev_id_int, "Name": dev_name,
                                "Mobile": dev_mobile, "Book_ID": b_id, 
                                "Start_Bill": row['Start_Bill_No'], "End_Bill": row['End_Bill_No'], "Status": "Issued"
                            })
                            
                        # নতুন রেকর্ড মূল রিপোর্টে যোগ করা
                        st.session_state.report_df = pd.concat([st.session_state.report_df, pd.DataFrame(new_records)], ignore_index=True)
                        st.success(f"{dev_name} কে সফলভাবে {num_books} টি বই দেওয়া হয়েছে!")
            except ValueError:
                st.warning("দয়া করে সঠিক Devotee ID লিখুন।")
    else:
        st.info("দয়া করে বাঁদিকের মেনু থেকে Master List এবং Book List আপলোড করুন।")

# --- TAB 2: RETURN BOOK ---
with tab2:
    st.subheader("ফেরত আসা বই জমা নিন")
    if not st.session_state.book_df.empty:
        return_book_id = st.text_input("ফেরত আসা Book ID লিখুন (যেমন: B006):")
        if st.button("বই ফেরত নিন"):
            if return_book_id in st.session_state.book_df['Book_ID'].values:
                # Book List এ Status Available করা
                st.session_state.book_df.loc[st.session_state.book_df['Book_ID'] == return_book_id, 'Status'] = 'Available'
                
                # রিপোর্টে আপডেট করা (যাতে বোঝা যায় ফেরত এসেছে)
                st.session_state.report_df.loc[st.session_state.report_df['Book_ID'] == return_book_id, 'Status'] = 'Returned'
                st.success(f"{return_book_id} নম্বর বইটি সফলভাবে ফেরত নেওয়া হয়েছে এবং আবার স্টকে যোগ হয়েছে!")
            else:
                st.error("এই Book ID টি খুঁজে পাওয়া যায়নি!")
    else:
        st.info("Book List আপলোড করা নেই।")

# --- TAB 3: REPORT & DOWNLOAD ---
with tab3:
    st.subheader("বর্তমান রিপোর্ট")
    if not st.session_state.report_df.empty:
        st.dataframe(st.session_state.report_df)
        
        # এক্সেলে কনভার্ট করার ফাংশন
        def convert_df_to_excel(df1, df2):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df1.to_excel(writer, index=False, sheet_name='Issued_Report')
                df2.to_excel(writer, index=False, sheet_name='Updated_Book_Inventory')
            return output.getvalue()
        
        excel_data = convert_df_to_excel(st.session_state.report_df, st.session_state.book_df)
        
        st.download_button(
            label="📥 ফাইনাল এক্সেল ডাউনলোড করুন",
            data=excel_data,
            file_name="Final_Devotee_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("এখনো কোনো বই ইস্যু বা ফেরত নেওয়া হয়নি।")