from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from io import BytesIO

app = Flask(__name__)
app.secret_key = "secret"

@app.route("/")
def index():
    return render_template("index.html", current_year=2025)

@app.route("/search", methods=["POST"])
def search():
    shop = request.form.get("shop", "").strip()
    location = request.form.get("location", "").strip()

    if not shop or not location:
        flash("Please enter both shop and location.", "error")
        return redirect(url_for("index"))

    flash(f"Searching for '{shop}' near '{location}' …", "success")

    excel_file = generate_excel(shop, location)

    if not excel_file:
        flash("Data not available")
        return redirect(url_for("index"))

    return send_file(
        excel_file,
        as_attachment=True,
        download_name=f"{shop}_{location}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def generate_excel(shop, location):
    cleanData = {"Name": [], "Address": [], "Phone": [], "Location": []}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            search_url = f"https://www.google.com/maps/search/{shop}+{location}"
            page.goto(search_url, wait_until="networkidle")
            time.sleep(5)  # let results load

            # scroll a few times to load more results
            for _ in range(5):
                page.mouse.wheel(0, 2000)
                time.sleep(2)

            soup = BeautifulSoup(page.content(), "html.parser")
            rawData = soup.select("div.Nv2PK")

            for rD in rawData:
                try:
                    name = rD.select("div.qBF1Pd")[0].text if rD.select("div.qBF1Pd") else "N/A"
                    address = rD.select("div.W4Efsd")[1].find_all('span')[2].text[3:] if len(rD.select("div.W4Efsd")) > 1 else "N/A"
                    phone = rD.select("span.UsdlK")[0].text if rD.select("span.UsdlK") else "N/A"

                    cleanData["Name"].append(name)
                    cleanData["Address"].append(address)
                    cleanData["Phone"].append(phone)
                    cleanData["Location"].append(location)
                except Exception:
                    continue

            browser.close()

    except Exception as e:
        print(f"Failed for city {location}: {e}")

    df = pd.DataFrame(cleanData)
    df = df.dropna(subset=["Phone"])
    df = df[df["Phone"].str.strip() != "N/A"]
    df = df.reset_index(drop=True)

    if len(df) > 1:
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        return output
    else:
        return None

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
