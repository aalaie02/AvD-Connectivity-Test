# 🌐 Port 443 Connectivity Tester for Azure Virtual Desktop (AvD)

This Streamlit app allows users to test network connectivity to key Azure Virtual Desktop (AvD) service endpoints over port 443. It supports multiple test methods (Socket, Curl, Ping), optional proxy and header settings, and visualizes latency results with charts and tables.

---

## 🚀 Features

- Test connectivity to predefined Microsoft endpoints
- Optional proxy configuration
- Support for Socket, Curl, and Ping methods
- Latency statistics grouped by domain zone
- Real-time charts with Altair
- Export results to Excel including latency chart and detailed table

---

## 🧪 How to Use

1. Enter your **AvD Username** (required) and **Company** (optional)
2. Select the test method and optional proxy or headers
3. Click **"Run Connectivity Test"**
4. View results, charts, and export to Excel

---

## 📦 Installation

```bash
pip install streamlit pandas aiohttp matplotlib altair xlsxwriter Pillow
```

---

## ▶️ Running the App

```bash
streamlit run connectivity_test.py
```

---

## 📤 Deploy to Streamlit Cloud

1. Push your app to a public GitHub repo
2. Visit [streamlit.io/cloud](https://streamlit.io/cloud)
3. Connect your GitHub and deploy your app

---

## 📁 Files

- `connectivity_test.py` — main Streamlit app
- `requirements.txt` — Python dependencies

---

## 📃 License

MIT License — use, modify, and distribute freely.

---

## 🙏 Acknowledgments

This app uses public Microsoft endpoint references and was inspired by operational needs for Azure Virtual Desktop readiness.
