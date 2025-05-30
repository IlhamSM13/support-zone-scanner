import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import yfinance as yf
import os
from datetime import datetime, timedelta

# Fungsi Identifikasi Support Level
def identify_support_levels(low_series, current_close, window=10):
    low_series = low_series.squeeze()
    min_values = low_series.rolling(window=window, center=True).min()
    support_levels = []

    for i in range(window, len(low_series) - window):
        price = float(low_series.iloc[i])
        min_val = min_values.iloc[i]

        if pd.notna(min_val) and price == float(min_val):
            if (price < low_series.iloc[i-window:i]).all() and (price < low_series.iloc[i+1:i+1+window]).all():
                support_levels.append((low_series.index[i], price))

    valid_supports = [(date, level) for (date, level) in support_levels if abs(current_close - level) / current_close <= 0.05]
    return valid_supports

# Fungsi Menampilkan Garis Support
def draw_support(fig, support_levels):
    for idx, (date, price) in enumerate(support_levels):
        fig.add_hline(
            y=price, 
            line_dash="dot", 
            line_color="green",
            opacity=0.5,
            annotation_text=f"Support {price:.0f}" if idx == 0 else None,
            annotation_position="bottom right"
        )

# Fungsi untuk plot candlestick
def plot_candlestick(data, title):
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(0)
    
    clean_data = pd.DataFrame({
        'Datetime': data.index,
        'Open': data['Open'].values if 'Open' in data else data.iloc[:,0],
        'High': data['High'].values if 'High' in data else data.iloc[:,1],
        'Low': data['Low'].values if 'Low' in data else data.iloc[:,2],
        'Close': data['Close'].values if 'Close' in data else data.iloc[:,3],
        'Volume': data['Volume'].values if 'Volume' in data else data.iloc[:,4]
    })

    fig = go.Figure(data=[go.Candlestick(
        x=clean_data['Datetime'],
        open=clean_data['Open'],
        high=clean_data['High'],
        low=clean_data['Low'],
        close=clean_data['Close']
    )])

    # 5. Atur layout
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Price (IDR)',
        xaxis_rangeslider_visible=False,
        template='plotly_white'
    )

    return fig

# Fungsi looping setiap saham terhadap identifikasi support level
def process_stock(ticker):
    try:
        data = yf.download(ticker, period='3mo', interval='1d', progress=False)

        low_series = data['Low']
        current_close = data['Close'].iloc[-1].item()

        support_levels = identify_support_levels(low_series, current_close)

        if support_levels:
            return (ticker, support_levels, current_close), None
        else:
            return None, f"Emiten {ticker} tidak memiliki support yang valid."
    except Exception as e:
        if "No object to concatenate" in str(e):
            return None, f"Gagal memproses {ticker}: Tidak ada data yang dapat digabungkan."
        return None, f"Gagal memproses {ticker}: {e}"

sector_dict = {
    'Healthcare': 'dft_shm_healthcare.xlsx',
    'Basic Materials': 'dft_shm_basicmaterials.xlsx',
    'Financials': 'dft_shm_financials.xlsx',
    'Transportation & Logistic': 'dft_shm_transport.xlsx',
    'Technology': 'dft_shm_technology.xlsx',
    'Consumer Non-Cyclicals': 'dft_shm_consnoncyclicals.xlsx',
    'Industrials': 'dft_shm_industrials.xlsx',
    'Energy': 'dft_shm_energy.xlsx',
    'Consumer Cyclicals': 'dft_shm_conscyclicals.xlsx',
    'Infrastructures': 'dft_shm_industrials.xlsx',
    'Properties & Real Estate': 'dft_shm_estate.xlsx',
}

# Streamlit App
st.markdown(
    """
    <h3 style='margin-bottom: 10px;'>📊 Stocks Screening by Support Zone</h3>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div style='text-align: justify; font-size: 16px; line-height: 1.6; padding: 10px 15px; background-color: #f9f9f9; border-radius: 8px;'>
        Fitur ini bertujuan membantu kamu menyaring saham-saham yang sedang berada dekat dengan zona support, yaitu dalam rentang ±10% dari harga penutupan terakhir terhadap level support terdekat. 
        Zona support ditentukan berdasarkan pola harga terendah historis harian dalam periode 20 hari, yang mencerminkan potensi area pantulan harga. 
        Harap diingat bahwa alat ini tidak dimaksudkan sebagai pedoman investasi mutlak, melainkan sebagai pelengkap dalam proses analisis teknikal.
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")

selected_sector = st.selectbox("Pilih sektor di sini:", list(sector_dict))

if 'Scanned' not in st.session_state:
    st.session_state['Scanned'] = False

if selected_sector:
    st.session_state['Scanned'] = True

# Membaca Daftar Saham
if st.session_state['Scanned']:
    valid_ticker = []
    error_messages = []

    file_path = os.path.join('daftar_saham', sector_dict[selected_sector])
    df_sector = pd.read_excel(file_path)

    list_ticker = [kode + '.JK' for kode in df_sector['Kode'].tolist()]

    for ticker in list_ticker:
        result, err_msg = process_stock(ticker)
        if result:
            valid_ticker.append(result)
        else:
            error_messages.append(err_msg)

    example = []

    for ticker, supports, current_close in valid_ticker:
        for date, price in supports:
            example.append({
                'Emiten': ticker.replace(".JK",""),
                'Support Date': date.date(),
                'Support Price': round(price, 2),
                'Range (%)': round(((current_close - price) / current_close) * 100, 2)
            })

    # Buat DataFrame dan reset index
    df = pd.DataFrame(example)

    st.markdown(
        """
        <h3 style='margin-bottom: 10px;'>📈 Support Zone Overview</h3>
        """,
        unsafe_allow_html=True
    )

    st.dataframe(df, use_container_width=True, hide_index=True)

    # Buat list unik emiten dari example
    emiten_list = list({item['Emiten'] for item in example})

    # Buat selectbox-nya
    selected_ticker = st.selectbox("Pilih Emiten:", sorted(emiten_list))

    if selected_ticker:
        ticker_full = selected_ticker + ".JK"

        # Cari support level yang sesuai
        support_levels = next((levels for tick, levels, _ in valid_ticker if tick == ticker_full), None)

        if support_levels is None:
            st.warning("Support level untuk emiten ini tidak ditemukan.")
        else:
            # Tab layout untuk multi-timeframe
            tab1, tab2, tab3 = st.tabs(["Daily (Support)", "Hourly (1 Month)", "Weekly (1 Year)"])
            
            with tab1:
                # Ambil data saham yang dipilih
                data_daily = yf.download(
                    ticker_full,
                    period='6mo',
                    interval='1d',
                    progress=False
                )

                if data_daily.empty:
                    st.error("Data daily tidak tersedia.")
                else:
                    fig_daily = plot_candlestick(data_daily, f"Daily Candlestick (6 Months) - {selected_ticker}")
                    draw_support(fig_daily, support_levels)
                    st.plotly_chart(fig_daily, use_container_width=True)
            
            with tab2:
                # Data hourly (1 bulan terakhir)
                data_hourly = yf.download(
                    ticker_full, 
                    start=datetime.now() - timedelta(days=14), 
                    end=datetime.now(), 
                    interval="1h", 
                    progress=False
                )
                
                if data_hourly.empty:
                    st.error("Data hourly tidak tersedia.")
                else:
                    fig_hourly = plot_candlestick(data_hourly, f"Hourly Candlestick (14 Days) - {selected_ticker}")
                    draw_support(fig_hourly, support_levels)
                    st.plotly_chart(fig_hourly, use_container_width=True)
            
            with tab3:
                # Data weekly (1 tahun terakhir)
                data_weekly = yf.download(
                    ticker_full, 
                    period="1y", 
                    interval="1wk", 
                    progress=False
                )
                
                if data_weekly.empty:
                    st.error("Data weekly tidak tersedia.")
                else:
                    fig_weekly = plot_candlestick(data_weekly, f"Weekly Candlestick (1 Year) - {selected_ticker}")
                    draw_support(fig_weekly, support_levels)
                    st.plotly_chart(fig_weekly, use_container_width=True)

        st.write("Sumber data: Yahoo Finance (via yfinance)")
