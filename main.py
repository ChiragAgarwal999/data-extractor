from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from selenium import webdriver
from selenium.webdriver.common.by import By
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

    # Return the file directly instead of saving
    return send_file(
        excel_file,
        as_attachment=True,
        download_name=f"{shop}_{location}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def generate_excel(shop, location):
    driver = webdriver.Chrome()
    cleanData = {"Name": [], "Address": [], "Phone": [], "Location": []}

    try:
        search_url = f"https://www.google.com/maps/search/{shop}+{location}"
        driver.get(search_url)
        time.sleep(10)

        for _ in range(10):
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(2)

            soup = BeautifulSoup(driver.page_source, 'html.parser')
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
    except Exception as e:
        print(f"Failed for city {location}: {e}")

    driver.quit()

    df = pd.DataFrame(cleanData)
    df = df.dropna(subset=['Phone'])
    df = df[df['Phone'].str.strip() != 'N/A']
    df = df.reset_index(drop=True)

    if len(df) > 1:
          # Create Excel in memory
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        return output
    else:
        return None

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Railway sets PORT
    app.run(host="0.0.0.0", port=port, debug=False)
