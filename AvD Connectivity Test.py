import streamlit as st
import socket
import time
import pandas as pd
import asyncio
import aiohttp
import subprocess
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
import os
import altair as alt  # ✅ Add it here


st.set_page_config(page_title="Port 443 Connectivity Tester for AvD", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="css"] {
        background-color: #f9f9f9;
    }
    </style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.markdown("## 🌐 Connectivity Tester with Proxy, Port, Auth & Tool Options")

with col1:
    st.markdown("""
<div style='margin-bottom: 1em; padding: 1em; border-left: 5px solid #0072CE; font-size: 16px;'>
    <strong>Note:</strong> Any device on which you use one of the <strong>Remote Desktop clients</strong> to connect to <strong>Azure Virtual Desktop</strong> must have access to the following <strong>FQDNs</strong> and endpoints. 
    Allowing these FQDNs and endpoints is essential for a reliable client experience. Blocking access to these FQDNs and endpoints isn't supported and affects service functionality.<br><br>
    🔗 <a href='https://learn.microsoft.com/en-us/azure/virtual-desktop/safe-url-list' target='_blank'>View official Microsoft documentation</a>
</div>
""", unsafe_allow_html=True)



# Default test endpoints
default_hosts = [
    "login.microsoftonline.com",
    "rdweb.wvd.microsoft.com",
    "go.microsoft.com",
    "aka.ms",
    "learn.microsoft.com",
    "privacy.microsoft.com",
    "ajax.aspnetcdn.com",
    "graph.microsoft.com",
    "windows.cloud.microsoft",
    "windows365.microsoft.com",
    "ecs.office.com"
]

with col1:
    st.subheader("🧾 Default Hosts to be Tested on Port 443")
    st.table(pd.DataFrame({"Host": default_hosts, "Port": 443}))
    st.markdown("Customize endpoints, proxy, port, auth headers, and tool for testing.")

with col1:
    # Editable fields before running the test
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    if not st.session_state.submitted:
        username = st.text_input("👤 Your AvD Username (required):")
        st.session_state.username = username
        company = st.text_input("🏢 Your Company:")
        st.session_state.company = company
        if username == "":
            st.warning("Username is required to proceed.")
    else:
        st.text_input("👤 Your AvD Username (required):", value=st.session_state.username, disabled=True)
        st.text_input("🏢 Your Company:", value=st.session_state.company, disabled=True)

    tool = st.selectbox("Test Method", ["Socket", "Curl", "Ping"])
    proxy = st.text_input("Proxy (Optional, e.g., http://proxy:port):", "")

with col1:
    st.subheader("🔐 Optional API Headers")
    headers_raw = st.text_area("Enter headers (one per line, format: Key: Value)")
    headers_list = [line.strip() for line in headers_raw.splitlines() if ':' in line]
    headers = []
    for h in headers_list:
        key, value = h.split(':', 1)
        headers.append("-H")
        headers.append(f"{key.strip()}: {value.strip()}")

# Async method using socket
async def check_socket(host, port):
    try:
        start = time.time()
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: socket.create_connection((host, port), timeout=5))
        latency = round((time.time() - start) * 1000, 2)
        return host, "✅ Reachable", latency, None
    except Exception as e:
        return host, "❌ Failed", None, str(e)

# Curl method
def check_curl(host, port, proxy, headers):
    url = f"https://{host}:{port}"
    curl_cmd = ["curl", "--connect-timeout", "5", "-s", "-o", "/dev/null", "-w", "%{time_total}", url]
    if proxy:
        curl_cmd.extend(["-x", proxy])
    if headers:
        curl_cmd.extend(headers)
    try:
        output = subprocess.check_output(curl_cmd, stderr=subprocess.STDOUT, universal_newlines=True)
        latency = round(float(output.strip()) * 1000, 2)
        return host, "✅ Reachable", latency, f"{latency} ms"
    except subprocess.CalledProcessError as e:
        return host, "❌ Failed", None, e.output.strip()

# Ping method
import platform

def check_ping(host):
    count_flag = "-n" if platform.system().lower() == "windows" else "-c"
    ping_cmd = ["ping", count_flag, "2", host]
    try:
        output = subprocess.check_output(ping_cmd, stderr=subprocess.STDOUT, universal_newlines=True)
        lines = output.splitlines()
        if platform.system().lower() == "windows":
            latency_line = next((line for line in lines if "Average" in line), "")
            latency = float(latency_line.split("Average = ")[-1].replace("ms", "").strip()) if "Average = " in latency_line else None
        else:
            latency_line = next((line for line in lines if "avg" in line or "mdev" in line), "")
            latency = float(latency_line.split("/")[4]) if "/" in latency_line else None
        return host, "✅ Reachable", latency, "Ping succeeded"
    except subprocess.CalledProcessError as e:
        return host, "❌ Failed", None, e.output.strip().splitlines()[-1]
    except subprocess.CalledProcessError as e:
        return host, "❌ Failed", None, e.output.strip().splitlines()[-1]

# Hosts and port setup
hosts_to_test = default_hosts
port = 443

if not st.session_state.submitted and st.session_state.username and st.button("🚀 Run Connectivity Test"):
    st.session_state.submitted = True
    with col2:
        data = []
        with st.spinner("Testing... please wait"):
          if tool == "Socket":
              loop = asyncio.new_event_loop()
              asyncio.set_event_loop(loop)
              tasks = [check_socket(host, port) for host in hosts_to_test]
              results = loop.run_until_complete(asyncio.gather(*tasks))
          else:
              executor = ThreadPoolExecutor(max_workers=10)
              if tool == "Curl":
                  results = list(executor.map(lambda h: check_curl(h, port, proxy, headers), hosts_to_test))
              else:
                  results = list(executor.map(check_ping, hosts_to_test))

        for host, status, latency, detail in results:
            zone = ".".join(host.split(".")[-2:])
            data.append({"Host": host, "Zone": zone, "Port": port, "Status": status, "Latency (ms)": latency, "Detail": detail})

        df = pd.DataFrame(data)
        st.success("✅ Test complete!")

        # Log unavailable tools

        # Show results table
        st.subheader("📋 Full Results Table")
        st.table(df)

        # Show latency chart by domain
        st.subheader("📊 Latency per Domain")
        if not df[df["Status"] == "✅ Reachable"].empty:
            grouped = df[df["Status"] == "✅ Reachable"].groupby("Zone")["Latency (ms)"].mean().reset_index()
            st.bar_chart(grouped.set_index("Zone"))

        # Group by domain zone
        st.subheader("📊 Min/Max Latency per Domain Zone")
        if not df[df["Status"] == "✅ Reachable"].empty:
            latency_stats = df[df["Status"] == "✅ Reachable"].groupby("Zone")["Latency (ms)"].agg(["min", "max", "mean"]).reset_index()
            latency_stats.columns = ["Zone", "Min Latency (ms)", "Max Latency (ms)", "Avg Latency (ms)"]
            st.dataframe(latency_stats)

            # Add visual with color gradient based on avg latency
            st.subheader("📈 Latency Summary Chart")
            chart = alt.Chart(latency_stats).mark_bar().encode(
                x=alt.X("Zone", sort="-y"),
                y=alt.Y("Avg Latency (ms)", title="Avg Latency (ms)"),
                color=alt.Color("Avg Latency (ms)", scale=alt.Scale(domain=[0, 100, 300], range=['green', 'yellow', 'red'])),
                tooltip=["Zone", "Min Latency (ms)", "Max Latency (ms)", "Avg Latency (ms)"]
            ).properties(height=400)

            error_bars = alt.Chart(latency_stats).mark_errorbar(extent='iqr').encode(
                x=alt.X("Zone", sort="-y"),
                y=alt.Y("Min Latency (ms)", title="Latency Range (ms)"),
                y2="Max Latency (ms)"
            )

            labels = alt.Chart(latency_stats).mark_text(align="center", dy=-10, fontSize=12).encode(
                x="Zone",
                y="Avg Latency (ms)",
                text=alt.Text("Avg Latency (ms)", format=".0f")
            )

            st.altair_chart(chart + error_bars + labels, use_container_width=True)

# Download button
        import io
        import xlsxwriter
        from PIL import Image
        import matplotlib.pyplot as plt

        # Create chart image from latency_stats
        if not df[df["Status"] == "✅ Reachable"].empty:
            chart_fig, ax = plt.subplots(figsize=(8, 4))
            latency_stats.plot(kind='bar', x='Zone', y='Avg Latency (ms)', ax=ax, color='skyblue')
            ax.set_title("Avg Latency per Domain Zone")
            ax.set_ylabel("Latency (ms)")
            plt.tight_layout()

            # Save chart to BytesIO
            chart_img_io = io.BytesIO()
            plt.savefig(chart_img_io, format='png')
            chart_img_io.seek(0)

        excel_io = io.BytesIO()
        with pd.ExcelWriter(excel_io, engine="xlsxwriter") as writer:
            df.insert(0, "AvD Username", st.session_state.username)
            df.insert(1, "Company", st.session_state.company)
            df.to_excel(writer, sheet_name="Results", index=False)
            latency_stats.to_excel(writer, sheet_name="Latency Stats", index=False)
            workbook  = writer.book
            worksheet = writer.sheets["Results"]
            stats_sheet = writer.sheets["Latency Stats"]

            if not df[df["Status"] == "✅ Reachable"].empty:
                image_cell = f"B{len(df) + 5}"
                stats_sheet.insert_image("B5", "latency_chart.png", {"image_data": chart_img_io, "x_scale": 0.75, "y_scale": 0.75})

        excel_io.seek(0)
        st.download_button(
            "📄 Download Results as Excel",
            data=excel_io,
            file_name="connectivity_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
