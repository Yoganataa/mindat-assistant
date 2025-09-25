# 🤖 Telegram Bot Admin - Pencatat Administrasi

Bot Telegram canggih untuk pencatatan data administrasi langsung ke Google Sheets menggunakan Natural Language Processing. Bot ini memungkinkan pengguna untuk mencatat transaksi, inventory, atau data administrasi lainnya dengan cara yang intuitif.

## ✨ Fitur Utama

- 🗣️ **Natural Language Input** - Input data dengan bahasa natural Indonesia
- 📊 **Google Sheets Integration** - Otomatis menyimpan ke spreadsheet
- 🔄 **State Management** - Mengelola status pengguna dengan persistent storage
- 📱 **Interactive Menu** - Menu keyboard yang user-friendly
- 🔍 **Smart Parsing** - Mengenali item, jumlah, harga, dan jenis transaksi
- 🛡️ **Secure** - Kredensial disimpan dengan aman menggunakan environment variables
- ⚡ **Async/Await** - Performa optimal dengan operasi asynchronous

## 🛠️ Tech Stack

- **Python 3.10+**
- **Pyrogram** - Modern Telegram Bot framework
- **gspread** - Google Sheets API integration
- **python-dotenv** - Environment configuration management

## 📁 Struktur Proyek

```
telegram-bot-project/
├── .env.example              # Template environment variables
├── requirements.txt          # Python dependencies
├── config.py                # Konfigurasi aplikasi
├── state_manager.py         # Manajemen state pengguna
├── main.py                  # Entry point aplikasi
├── services/
│   ├── gsheet_service.py    # Google Sheets service
│   └── nlp_parser.py        # Natural Language Parser
└── handlers/
    ├── command_handler.py   # Handler untuk commands
    └── message_handler.py   # Handler untuk messages
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.10 atau lebih baru
- Akun Telegram Bot (dari [@BotFather](https://t.me/botfather))
- Google Cloud Project dengan Sheets API enabled
- Google Service Account dengan kredensial JSON

### 2. Clone dan Setup

```bash
# Clone repositori
git clone <repository-url>
cd telegram-bot-project

# Buat virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Konfigurasi Environment

```bash
# Copy template environment
cp .env.example .env

# Edit file .env dengan editor favorit Anda
nano .env
```

Isi file `.env` dengan konfigurasi berikut:

```env
# Telegram Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here
API_ID=your_telegram_api_id_here
API_HASH=your_telegram_api_hash_here

# Google Sheets Configuration
GOOGLE_CREDENTIALS_FILE=path/to/your/google_credentials.json
DEFAULT_SPREADSHEET_ID=your_default_spreadsheet_id_here

# Bot Configuration
STATE_FILE=user_states.json
DEFAULT_SHEET_NAME=Sheet1
```

### 4. Setup Google Sheets

#### a. Buat Service Account

1. Buka [Google Cloud Console](https://console.cloud.google.com/)
2. Buat project baru atau pilih existing project
3. Enable Google Sheets API dan Google Drive API
4. Buat Service Account:
   - IAM & Admin → Service Accounts
   - Create Service Account
   - Download JSON key file

#### b. Setup Spreadsheet

1. Buat Google Spreadsheet baru
2. Share spreadsheet dengan email service account (dengan akses Editor)
3. Copy Spreadsheet ID dari URL
4. Setup header di Sheet1, contoh:
   ```
   Item | Quantity | Amount | Type | Note | Timestamp
   ```

### 5. Setup Telegram Bot

1. Chat dengan [@BotFather](https://t.me/botfather)
2. Gunakan `/newbot` untuk membuat bot baru
3. Dapatkan Bot Token
4. Dapatkan API ID dan API Hash dari [my.telegram.org](https://my.telegram.org)

### 6. Jalankan Bot

```bash
python main.py
```

Bot akan menampilkan informasi startup dan siap digunakan!

## 📖 Panduan Penggunaan

### Menu Utama

Bot menyediakan menu interaktif dengan tombol-tombol berikut:

- 🆘 **Help** - Menampilkan panduan penggunaan
- 🗒️ **Input** - Masuk ke mode input data
- 📝 **Header** - Mengelola header kolom sheet
- 📒 **Sheets** - Mengelola sheets dalam spreadsheet
- 🗃️ **Spreadsheets** - Informasi spreadsheet aktif
- 🛑 **Stop** - Keluar dari mode input

### Mode Input Data

1. Klik **🗒️ Input** untuk masuk mode input
2. Ketik data dalam bahasa natural, contoh:
   ```
   Laptop Asus terjual 2 unit seharga 15jt
   Beli kertas A4 5 rim harga 250rb
   Mouse wireless dijual 10 pcs 500ribu
   ```
3. Bot akan otomatis parsing dan menyimpan ke Google Sheets
4. Klik **🛑 Stop** untuk keluar dari mode input

### Format Input yang Didukung

#### Nominal Uang
- `15jt`, `2.5juta` → 15,000,000
- `250rb`, `1.2ribu` → 250,000
- `1,500`, `1500.50` → angka langsung

#### Quantity
- `2 unit`, `5 buah`, `10 pcs`
- `3 kg`, `500 gram`, `2 liter`

#### Jenis Transaksi
- **Penjualan**: terjual, dijual, sold, laku
- **Pembelian**: dibeli, beli, bought, purchase
- **Pengeluaran**: biaya, expense, cost, pengeluaran
- **Pemasukan**: pemasukan, income, revenue, hasil

## 🔧 Konfigurasi Lanjutan

### Custom Header Mapping

Edit file `services/nlp_parser.py` pada bagian `header_mapping` untuk menyesuaikan mapping header:

```python
header_mapping = {
    'item': 'item_name',
    'nama': 'item_name',
    'barang': 'item_name',
    'product': 'item_name',
    # Tambahkan mapping custom Anda
}
```

### Extend NLP Parser

Untuk menambah pattern recognition, edit `services/nlp_parser.py`:

```python
# Tambahkan pattern baru
self.custom_patterns = [
    r'pattern_regex_anda',
]

# Tambahkan keywords baru
self.transaction_keywords['custom_type'] = ['keyword1', 'keyword2']
```

## 🐛 Troubleshooting

### Bot tidak merespon
- Pastikan BOT_TOKEN benar
- Cek koneksi internet
- Lihat log error di `bot.log`

### Error Google Sheets
- Pastikan service account memiliki akses ke spreadsheet
- Cek path file kredensial JSON
- Pastikan Sheets API enabled di Google Cloud

### Error parsing data
- Cek format input sesuai contoh
- Pastikan header sheet sudah diatur
- Lihat log untuk detail error

### State tidak tersimpan
- Pastikan direktori memiliki write permission
- Cek file `user_states.json` dibuat dengan benar

## 📝 Development

### Menambah Handler Baru

1. Buat handler di `handlers/` directory
2. Import di `main.py`
3. Register ke Pyrogram client

```python
# Contoh custom handler
@self.app.on_message(filters.regex(r"^custom_pattern$"))
async def custom_handler(client: Client, message: Message):
    await message.reply("Custom response")
```

### Menambah Service Baru

1. Buat file di `services/` directory
2. Implement class dengan metod async
3. Import dan gunakan di handler

### Testing

```bash
# Install testing dependencies
pip install pytest pytest-asyncio

# Run tests (jika tersedia)
pytest tests/
```

## 🔒 Security Best Practices

1. **Jangan commit kredensial** ke repository
2. **Gunakan environment variables** untuk semua konfigurasi sensitif
3. **Restrict service account permissions** sesuai kebutuhan
4. **Enable 2FA** untuk akun Google yang digunakan
5. **Regular backup** file state dan konfigurasi

## 📊 Monitoring dan Logging

Bot menggunakan Python logging untuk monitoring:

```python
# Log levels
DEBUG    # Detail debugging info
INFO     # General information
WARNING  # Potential issues
ERROR    # Error conditions
```

Log disimpan di:
- `bot.log` - File log
- Console output - Real-time monitoring

## 🤝 Contributing

1. Fork repository
2. Buat feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📞 Support

Jika mengalami masalah atau memiliki pertanyaan:

1. Cek [Issues](../../issues) untuk masalah yang sudah ada
2. Buat [Issue baru](../../issues/new) untuk bug report atau feature request
3. Lihat dokumentasi Google Sheets API dan Pyrogram untuk referensi

## 🙏 Acknowledgments

- [Pyrogram](https://github.com/pyrogram/pyrogram) - Modern Telegram Bot framework
- [gspread](https://github.com/burnash/gspread) - Google Sheets Python API
- [python-dotenv](https://github.com/theskumar/python-dotenv) - Environment variable management

---

**Happy coding! 🚀**