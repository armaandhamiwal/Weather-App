from flask import Flask, render_template, request, flash, redirect
import requests
import pyodbc

app = Flask(__name__)
app.secret_key = "armaan_secret_key"

API_KEY = "bd3fb4d93b3b59d2f82799d4e9c9731a"

CONN_STR = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=DEVILSEYE\\SQLEXPRESS;"
    "Database=Weatherdb;"
    "Trusted_Connection=yes;"
)

def get_db_conn():
    return pyodbc.connect(CONN_STR)

@app.route("/", methods=["GET", "POST"])
def index():
    latest_weather = None
    history_data = []

    lat = request.args.get("lat")
    lon = request.args.get("lon")

    if lat and lon:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()
        if data.get("cod") == 200:
            latest_weather = {
                "city": data["name"],
                "temperature": data["main"]["temp"],
                "weather": data["weather"][0]["description"].title(),
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "feels_like": data["main"]["feels_like"],
                "wind_speed": data["wind"]["speed"],
                "icon": data["weather"][0]["icon"]
            }

    if request.method == "POST":
        city = request.form["city"].strip()
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()

        if data.get("cod") == 200:
            weather_info = {
                "city": data["name"],
                "temperature": data["main"]["temp"],
                "weather": data["weather"][0]["description"].title(),
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "feels_like": data["main"]["feels_like"],
                "wind_speed": data["wind"]["speed"],
                "icon": data["weather"][0]["icon"]
            }

            
            conn = get_db_conn()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO WeatherData (City, Temperature, Weather, Humidity) VALUES (?, ?, ?, ?)",
                (weather_info["city"], weather_info["temperature"], weather_info["weather"], weather_info["humidity"])
            )
            conn.commit()

            cursor.execute("""
                DELETE FROM WeatherData
                WHERE City NOT IN (SELECT TOP 5 City FROM WeatherData ORDER BY ID DESC)
            """)
            conn.commit()
            conn.close()

            latest_weather = weather_info
            flash(f"✅ Weather for {city.title()} fetched successfully!", "success")
        else:
            flash("❌ City not found! Try again.", "error")
            return redirect("/")

    
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TOP 5 City, Temperature, Weather, Humidity
        FROM WeatherData
        ORDER BY ID DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    for r in rows:
        history_data.append({
            "city": r[0],
            "temperature": r[1],
            "weather": r[2],
            "humidity": r[3]
        })

    if not latest_weather and history_data:
        latest_weather = history_data[0]

    return render_template("index.html", latest_weather=latest_weather, history=history_data)

if __name__ == "__main__":
    app.run(debug=True)
