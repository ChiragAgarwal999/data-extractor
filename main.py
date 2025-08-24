from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

app = Flask(__name__)
app.secret_key = "secret"

OUTPUT_FOLDER = "generated"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/")
def index():
    file_url = request.args.get("file")   # pass file name if exists
    return render_template("index.html", current_year=2025, file_url=file_url)

@app.route("/search", methods=["POST"])
def search():
    shop = request.form.get("shop", "").strip()
    location = request.form.get("location", "").strip()

    if not shop or not location:
        flash("Please enter both shop and location.", "error")
        return redirect(url_for("index"))
    
    flash(f"Searching for '{shop}' near '{location}' …", "success")
    file_name = generate_excel(shop, location)

    if not file_name:
        flash("Data not available")
        return redirect(url_for("index"))
    
    # Redirect back to index with file link
    return redirect(url_for("index", file=file_name))

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

    if(len(df) > 1):
        xlsx_file = f"{shop}_{location}.xlsx"
        filepath = os.path.join(OUTPUT_FOLDER, xlsx_file)
        df.to_excel(filepath, index=False)

        print("Data scraping complete and saved.")
        return xlsx_file   # return only file name
    else:
        return False


@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

# app.run(debug=True)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render sets PORT
    app.run(host="0.0.0.0", port=port, debug=False)