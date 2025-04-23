import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import os

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

    valid_supports = [(date, level) for (date, level) in support_levels if abs(current_close - level) / current_close <= 0.1]
    return valid_supports

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
            ## st.warning(err_msg)

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

    st.dataframe(df, use_container_width=True)

    # Buat list unik emiten dari example
    emiten_list = list({item['Emiten'] for item in example})  # pakai set agar unik, lalu ubah ke list

    # Buat selectbox-nya
    
    selected_ticker = st.selectbox("Pilih Emiten:", sorted(emiten_list))

    if selected_ticker:
        # st.write(f"Menampilkan visualisasi untuk: **{selected_ticker}**")

        ticker_full = selected_ticker + ".JK"

        # Cari support level yang sesuai
        support_levels = next((levels for tick, levels, _ in valid_ticker if tick == ticker_full), None)

        if support_levels is None:
            st.warning("Support level untuk emiten ini tidak ditemukan.")
        else:
            # Ambil data saham yang dipilih
            data = yf.download(ticker_full, period="6mo", interval="1d", progress=False)

            if data.empty or len(data) < 2:
                st.error("Data tidak cukup untuk divisualisasikan.")
            else:
                # Visualisasi
                plt.figure(figsize=(14, 7))
                plt.plot(data.index, data['Close'], label='Harga Penutupan', color='blue', alpha=0.5)
                plt.title(f'Zona Support Saham {selected_ticker}', fontsize=16)
                plt.xlabel('Tanggal', fontsize=12)
                plt.ylabel('Harga (IDR)', fontsize=12)

                for idx, (date, price) in enumerate(support_levels):
                    plt.axhline(y=price, color='green', linestyle='--', alpha=0.5,
                                label=f'Support {price:.0f}' if idx == 0 else "")
                    plt.fill_between(data.index, price*0.98, price*1.02, color='green', alpha=0.1)

                # Atur legenda agar tidak duplikat
                handles, labels = plt.gca().get_legend_handles_labels()
                by_label = dict(zip(labels, handles))
                plt.legend(by_label.values(), by_label.keys())

                plt.grid(True, linestyle='--', alpha=0.7)
                plt.tight_layout()

                st.pyplot(plt)
        st.write("Sumber data: Yahoo Finance (via yfinance)")
