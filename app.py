import pandas as pd
import plotly.express as px
import streamlit as st

# ตั้งค่าหน้าเว็บให้เป็นแบบ Wide Mode
st.set_page_config(
    page_title='แดชบอร์ดวิเคราะห์ยอดขายร้านคาเฟ่', page_icon='☕', layout='wide'
)


# โหลดข้อมูลที่ทำความสะอาดแล้ว
@st.cache_data
def load_data():
  data = pd.read_csv('clean_cafe_sales.csv')
  data['วันที่'] = pd.to_datetime(data['วันที่'])
  return data


df = load_data()

# หัวข้อหลักของแดชบอร์ด
st.title('☕ แดชบอร์ดวิเคราะห์ยอดขายร้านคาเฟ่และเบเกอรี่')
st.markdown(
    'ระบบวิเคราะห์ข้อมูลเชิงลึกสำหรับผู้บริหาร: ภาพรวมยอดขาย พฤติกรรมลูกค้า'
    ' และประสิทธิภาพรายสาขา'
)
st.markdown('---')

# --- ส่วนควบคุมใน Sidebar (ตัวกรองข้อมูล) ---
st.sidebar.header('🔍 ตัวกรองข้อมูล (Filters)')

# 1. ตัวกรองช่วงวันที่ (Date Range)
min_date = df['วันที่'].min().date()
max_date = df['วันที่'].max().date()
date_range = st.sidebar.date_input(
    'เลือกช่วงวันที่',
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

# 2. ตัวกรองสาขา
branches = ['ทั้งหมด'] + list(df['สาขา'].unique())
selected_branch = st.sidebar.selectbox('เลือกสาขา', branches)

# 3. ตัวกรองหมวดหมู่สินค้า
categories = ['ทั้งหมด'] + list(df['หมวดหมู่'].unique())
selected_category = st.sidebar.selectbox('เลือกหมวดหมู่สินค้า', categories)

# กรองข้อมูลตามเงื่อนไขทั้งหมด
filtered_df = df.copy()

# กรองวันที่ (ตรวจสอบว่าเลือกครบทั้งวันเริ่มต้นและสิ้นสุด)
if len(date_range) == 2:
  start_date, end_date = date_range
  filtered_df = filtered_df[
      (filtered_df['วันที่'].dt.date >= start_date)
      & (filtered_df['วันที่'].dt.date <= end_date)
  ]

if selected_branch != 'ทั้งหมด':
  filtered_df = filtered_df[filtered_df['สาขา'] == selected_branch]

if selected_category != 'ทั้งหมด':
  filtered_df = filtered_df[filtered_df['หมวดหมู่'] == selected_category]

# --- แสดงผล KPI Metrics (Overview) ---
total_revenue = filtered_df['ยอดรวม'].sum()
total_orders = filtered_df['รหัสคำสั่งซื้อ'].nunique()
total_qty = filtered_df['จำนวน'].sum()
avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric('💰 ยอดขายรวมทั้งหมด', f'{total_revenue:,.2f} บาท')
col2.metric('🛒 จำนวนคำสั่งซื้อ', f'{total_orders:,} ออร์เดอร์')
col3.metric('📦 สินค้าที่ขายได้', f'{total_qty:,} หน่วย')
col4.metric('🧾 ยอดซื้อเฉลี่ยต่อบิล', f'{avg_order_value:,.2f} บาท')

st.markdown('---')

# --- ส่วนสรุปข้อค้นพบสำหรับผู้บริหาร (Executive Insights) ---
st.subheader('💡 สรุปข้อค้นพบสำคัญ (Executive Insights)')
if not filtered_df.empty:
  top_branch = filtered_df.groupby('สาขา')['ยอดรวม'].sum().idxmax()
  top_branch_val = filtered_df.groupby('สาขา')['ยอดรวม'].sum().max()

  top_menu = filtered_df.groupby('ชื่อเมนู')['ยอดรวม'].sum().idxmax()
  top_menu_qty = filtered_df.groupby('ชื่อเมนู')['จำนวน'].sum()[top_menu]

  top_payment = filtered_df.groupby('ช่องทางชำระเงิน')['ยอดรวม'].sum().idxmax()
  payment_pct = (
      filtered_df.groupby('ช่องทางชำระเงิน')['ยอดรวม'].sum().max()
      / total_revenue
  ) * 100

  st.info(
      f'📌 **ภาพรวมจากการกรองข้อมูลปัจจุบัน:**\n'
      f'- **สาขาทำเงินสูงสุด:** สาขา **{top_branch}** (ยอดขายรวม {top_branch_val:,.2f} บาท)\n'
      f'- **เมนูยอดนิยมอันดับ 1:** **{top_menu}** (ขายได้ทั้งหมด {top_menu_qty:,} หน่วย)\n'
      f'- **พฤติกรรมการชำระเงิน:** ลูกค้านิยมชำระผ่าน **{top_payment}** มากที่สุด คิดเป็น **{payment_pct:.1f}%** ของยอดขายทั้งหมด'
  )
else:
  st.warning('⚠️ ไม่พบข้อมูลในช่วงเงื่อนไขที่เลือก กรุณาปรับตัวกรองใหม่')

st.markdown('---')

# --- แถวที่ 1 ของกราฟ: ยอดขายรายสาขา & Top 5 เมนูขายดี ---
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
  st.subheader('📊 ยอดขายแยกตามสาขา')
  if not filtered_df.empty:
    branch_sales = filtered_df.groupby('สาขา')['ยอดรวม'].sum().reset_index()
    fig_branch = px.bar(
        branch_sales,
        x='สาขา',
        y='ยอดรวม',
        color='สาขา',
        text_auto=',.0f',
        title='เปรียบเทียบยอดขายรวมแต่ละสาขา (บาท)',
    )
    fig_branch.update_layout(showlegend=False)
    st.plotly_chart(fig_branch, use_container_width=True)

with col_chart2:
  st.subheader('☕ Top 5 เมนูขายดี')
  if not filtered_df.empty:
    menu_sales = filtered_df.groupby('ชื่อเมนู')['ยอดรวม'].sum().reset_index()
    menu_sales = menu_sales.sort_values(by='ยอดรวม', ascending=False).head(5)
    fig_menu = px.bar(
        menu_sales,
        x='ยอดรวม',
        y='ชื่อเมนู',
        orientation='h',
        color='ชื่อเมนู',
        text_auto=',.0f',
        title='เมนูที่ทำยอดขายสูงสุด 5 อันดับแรก (บาท)',
    )
    fig_menu.update_layout(
        yaxis={'categoryorder': 'total ascending'}, showlegend=False
    )
    st.plotly_chart(fig_menu, use_container_width=True)

# --- แถวที่ 2 ของกราฟ: แนวโน้มรายวัน & สัดส่วนช่องทางชำระเงิน (Pie Chart) ---
col_chart3, col_chart4 = st.columns([2, 1])

with col_chart3:
  st.subheader('📈 แนวโน้มยอดขายรายวัน')
  if not filtered_df.empty:
    daily_sales = filtered_df.groupby('วันที่')['ยอดรวม'].sum().reset_index()
    fig_daily = px.line(
        daily_sales,
        x='วันที่',
        y='ยอดรวม',
        markers=True,
        title='ความเคลื่อนไหวยอดขายตามช่วงเวลา',
    )
    st.plotly_chart(fig_daily, use_container_width=True)

with col_chart4:
  st.subheader('💳 ช่องทางชำระเงิน')
  if not filtered_df.empty:
    payment_sales = (
        filtered_df.groupby('ช่องทางชำระเงิน')['ยอดรวม'].sum().reset_index()
    )
    fig_payment = px.pie(
        payment_sales,
        values='ยอดรวม',
        names='ช่องทางชำระเงิน',
        hole=0.4,  # ทำเป็นกราฟโดนัทให้ดูทันสมัย
        title='สัดส่วนยอดขายตามช่องทางชำระเงิน',
    )
    fig_payment.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_payment, use_container_width=True)

st.markdown('---')

# --- ตารางข้อมูลเจาะลึก (Drill-down) พร้อมระบบค้นหาและดาวน์โหลด ---
st.subheader('📋 ตารางข้อมูลรายละเอียดการขาย (Drill-down)')

# ช่องค้นหา (Search)
search_query = st.text_input(
    '🔎 ค้นหาในตาราง (พิมพ์ชื่อเมนู, รหัสคำสั่งซื้อ หรือสาขา):', ''
)

display_df = filtered_df.copy()
display_df['วันที่'] = display_df['วันที่'].dt.strftime('%Y-%m-%d')

if search_query:
  display_df = display_df[
      display_df.apply(
          lambda row: row.astype(str)
          .str.contains(search_query, case=False)
          .any(),
          axis=1,
      )
  ]

st.dataframe(display_df, use_container_width=True)

# ปุ่มดาวน์โหลดข้อมูลที่กรองแล้วเป็น CSV
csv_data = display_df.to_csv(index=False).encode('utf-8-sig')
st.download_button(
    label='📥 ดาวน์โหลดข้อมูลชุดนี้ (.csv)',
    data=csv_data,
    file_name='cafe_sales_report.csv',
    mime='text/csv',
)