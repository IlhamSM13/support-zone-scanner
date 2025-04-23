# 📊 Stocks Screening by Support Zone

Aplikasi Streamlit ini membantu pengguna menyaring saham-saham yang sedang berada dekat dengan **zona support**, yaitu area potensial pantulan harga berdasarkan harga terendah historis.

## 🚀 Fitur
- Pilih sektor saham berdasarkan kategori industri.
- Scan saham dan identifikasi zona support.
- Tampilkan hasil dalam bentuk tabel dan grafik interaktif.
- Screening didasarkan pada level support dalam ±10% dari harga penutupan terakhir.

## 🔍 Metodologi
- Data diambil menggunakan `yfinance` dalam interval harian 3 bulan terakhir.
- Level support dihitung menggunakan metode **rolling minimum** dengan jendela (window) 20 hari.
- Saham dianggap valid jika harga penutupan terakhir berada dalam ±10% dari support level.

## 🛠️ Instalasi

1. Clone repository ini:
   ```bash
   git clone https://github.com/username/nama-repo.git
   cd nama-repo
