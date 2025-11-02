from flask import Flask, request, jsonify, send_file, render_template
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import io

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Database configuration
DATABASE_PATH = 'weather_data.db'

# database functions 

def init_database():
    """
    Initialize the SQLite database and create the weather_readings table
    if it doesn't exist. Also populates with sample data on first run.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            pressure REAL NOT NULL,
            air_quality INTEGER NOT NULL,
            wind_speed REAL NOT NULL,
            wind_direction REAL NOT NULL,
            rainfall REAL NOT NULL
        )
    """)

    # Check if table is empty
    cursor.execute("SELECT COUNT(*) FROM weather_readings")
    count = cursor.fetchone()[0]

    

def get_db_connection():
    """
    Create and return a database connection with row factory for dict access
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# API ENDPOINTS


@app.route('/')
def home():
    """Home page"""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Weather Monitoring Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                background: linear-gradient(-45deg, #667eea, #764ba2, #f093fb, #4facfe);
                background-size: 400% 400%;
                animation: gradientShift 15s ease infinite;
                min-height: 100vh;
                padding: 20px;
                position: relative;
                overflow-x: hidden;
            }}

            @keyframes gradientShift {{
                0% {{ background-position: 0% 50%; }}
                50% {{ background-position: 100% 50%; }}
                100% {{ background-position: 0% 50%; }}
            }}

            body::before {{
                content: '';
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-image: 
                    radial-gradient(circle at 20% 50%, rgba(255, 255, 255, 0.15) 0%, transparent 50%),
                    radial-gradient(circle at 80% 80%, rgba(255, 255, 255, 0.15) 0%, transparent 50%),
                    radial-gradient(circle at 40% 20%, rgba(255, 255, 255, 0.1) 0%, transparent 50%);
                pointer-events: none;
                z-index: 0;
            }}

            .container {{
                max-width: 1400px;
                margin: 0 auto;
                position: relative;
                z-index: 1;
            }}

            header {{
                text-align: center;
                color: white;
                margin-bottom: 30px;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            }}

            h1 {{
                font-size: 2.5em;
                margin-bottom: 10px;
                animation: fadeInDown 0.8s ease-out;
            }}

            @keyframes fadeInDown {{
                from {{
                    opacity: 0;
                    transform: translateY(-20px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}

            nav {{
                background: rgba(255, 255, 255, 0.15);
                backdrop-filter: blur(10px);
                padding: 15px;
                border-radius: 15px;
                margin-bottom: 30px;
                display: flex;
                justify-content: center;
                gap: 20px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}

            nav a {{
                color: white;
                text-decoration: none;
                padding: 12px 24px;
                border-radius: 10px;
                background: rgba(255, 255, 255, 0.2);
                transition: all 0.3s;
                font-weight: 500;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}

            nav a:hover {{
                background: rgba(255, 255, 255, 0.35);
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            }}

            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}

            .stat-card {{
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                padding: 25px;
                border-radius: 20px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                text-align: center;
                transition: transform 0.3s, box-shadow 0.3s;
                border: 1px solid rgba(255, 255, 255, 0.5);
                animation: fadeInUp 0.6s ease-out;
            }}

            .stat-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3);
            }}

            @keyframes fadeInUp {{
                from {{
                    opacity: 0;
                    transform: translateY(20px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}

            .stat-title {{
                color: #666;
                font-size: 0.9em;
                margin-bottom: 10px;
                font-weight: 600;
            }}

            .stat-value {{
                font-size: 2.5em;
                font-weight: bold;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}

            .stat-unit {{
                font-size: 0.5em;
                color: #999;
            }}

            .latest-reading {{
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                padding: 30px;
                border-radius: 20px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                margin-bottom: 30px;
                border: 1px solid rgba(255, 255, 255, 0.5);
            }}

            .latest-reading h2 {{
                color: #333;
                margin-bottom: 20px;
            }}

            .reading-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
            }}

            .reading-item {{
                padding: 15px;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                border-radius: 12px;
                border-left: 4px solid #667eea;
                transition: transform 0.2s;
            }}

            .reading-item:hover {{
                transform: scale(1.05);
            }}

            .reading-label {{
                font-size: 0.9em;
                color: #666;
                margin-bottom: 5px;
                font-weight: 500;
            }}

            .reading-value {{
                font-size: 1.5em;
                font-weight: bold;
                color: #333;
            }}

            .actions {{
                display: flex;
                gap: 15px;
                justify-content: center;
                margin-bottom: 30px;
                flex-wrap: wrap;
            }}

            button {{
                padding: 15px 30px;
                font-size: 1em;
                border: none;
                border-radius: 12px;
                background: rgba(255, 255, 255, 0.95);
                color: #667eea;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s;
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
                border: 2px solid rgba(102, 126, 234, 0.3);
            }}

            button:hover {{
                transform: translateY(-3px);
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
                background: white;
                border-color: #667eea;
            }}

            button:active {{
                transform: translateY(-1px);
            }}

            .db-info {{
                background: rgba(255, 255, 255, 0.15);
                backdrop-filter: blur(10px);
                color: white;
                padding: 20px;
                border-radius: 15px;
                text-align: center;
                margin-top: 30px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            }}

            .timestamp {{
                color: #666;
                font-size: 0.9em;
                margin-top: 10px;
            }}

            @media (max-width: 768px) {{
                h1 {{
                    font-size: 2em;
                }}

                nav {{
                    flex-direction: column;
                    gap: 10px;
                }}

                .actions {{
                    flex-direction: column;
                }}

                button {{
                    width: 100%;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🌤️ Weather Monitoring Dashboard</h1>
                <p>Real-time Weather Data Logging & Analysis</p>
            </header>

            <nav>
                <a href="/">🏠 Home</a>
                <a href="/logs">📊 Data Logs</a>
                <a href="/graphs">📈 Graphs</a>
            </nav>

            <div id="stats-section" class="stats-grid">
                <!-- Stats will be loaded here -->
            </div>

            <div class="latest-reading">
                <h2>📡 Latest Reading</h2>
                <div id="latest-reading" class="reading-grid">
                    <!-- Latest reading will be loaded here -->
                </div>
                <div class="timestamp" id="last-update">Loading...</div>
            </div>

            <div class="actions">
                <button onclick="refreshData()">🔄 Refresh Now</button>
                <button onclick="exportCSV()">💾 Export CSV</button>
                <button onclick="location.href='/graphs'">📈 View Charts</button>
            </div>

            <div class="db-info">
                <strong>📁 Database:</strong> ./{DATABASE_PATH}<br>
                <strong>📝 Total Records:</strong> <span id="record-count">0</span>
            </div>
        </div>

        <script>
            // Fetch and display statistics
            async function loadStats() {{
                try {{
                    const response = await fetch('/api/stats');
                    const stats = await response.json();

                    const statsHTML = `
                        <div class="stat-card" style="animation-delay: 0.1s">
                            <div class="stat-title">Average Temperature</div>
                            <div class="stat-value">
                                ${{stats.avg_temperature.toFixed(1)}}
                                <span class="stat-unit">°C</span>
                            </div>
                        </div>
                        <div class="stat-card" style="animation-delay: 0.2s">
                            <div class="stat-title">Average Humidity</div>
                            <div class="stat-value">
                                ${{stats.avg_humidity.toFixed(1)}}
                                <span class="stat-unit">%</span>
                            </div>
                        </div>
                        <div class="stat-card" style="animation-delay: 0.3s">
                            <div class="stat-title">Max Wind Speed</div>
                            <div class="stat-value">
                                ${{stats.max_wind_speed.toFixed(1)}}
                                <span class="stat-unit">km/h</span>
                            </div>
                        </div>
                        <div class="stat-card" style="animation-delay: 0.4s">
                            <div class="stat-title">Total Rainfall</div>
                            <div class="stat-value">
                                ${{stats.total_rainfall.toFixed(1)}}
                                <span class="stat-unit">mm</span>
                            </div>
                        </div>
                    `;

                    document.getElementById('stats-section').innerHTML = statsHTML;
                }} catch (error) {{
                    console.error('Error loading stats:', error);
                }}
            }}

            // Fetch and display latest reading
            async function loadLatest() {{
                try {{
                    const response = await fetch('/api/latest');
                    const data = await response.json();

                    const readingHTML = `
                        <div class="reading-item">
                            <div class="reading-label">🌡️ Temperature</div>
                            <div class="reading-value">${{data.temperature}}°C</div>
                        </div>
                        <div class="reading-item">
                            <div class="reading-label">💧 Humidity</div>
                            <div class="reading-value">${{data.humidity}}%</div>
                        </div>
                        <div class="reading-item">
                            <div class="reading-label">🎈 Pressure</div>
                            <div class="reading-value">${{data.pressure}} hPa</div>
                        </div>
                        <div class="reading-item">
                            <div class="reading-label">💨 Air Quality</div>
                            <div class="reading-value">${{data.air_quality}} AQI</div>
                        </div>
                        <div class="reading-item">
                            <div class="reading-label">🌪️ Wind Speed</div>
                            <div class="reading-value">${{data.wind_speed}} km/h</div>
                        </div>
                        <div class="reading-item">
                            <div class="reading-label">🧭 Wind Direction</div>
                            <div class="reading-value">${{data.wind_direction}}°</div>
                        </div>
                        <div class="reading-item">
                            <div class="reading-label">🌧️ Rainfall</div>
                            <div class="reading-value">${{data.rainfall}} mm</div>
                        </div>
                    `;

                    document.getElementById('latest-reading').innerHTML = readingHTML;
                    document.getElementById('last-update').textContent = 
                        `Last updated: ${{new Date(data.timestamp).toLocaleString()}}`;
                }} catch (error) {{
                    console.error('Error loading latest data:', error);
                }}
            }}

            // Get total record count
            async function loadRecordCount() {{
                try {{
                    const response = await fetch('/api/data');
                    const data = await response.json();
                    document.getElementById('record-count').textContent = data.length;
                }} catch (error) {{
                    console.error('Error loading record count:', error);
                }}
            }}

            // Refresh all data
            function refreshData() {{
                loadStats();
                loadLatest();
                loadRecordCount();
            }}

            // Export CSV
            function exportCSV() {{
                window.location.href = '/api/export';
            }}

            // Auto-refresh every 5 seconds
            setInterval(refreshData, 5000);

            // Initial load
            refreshData();
        </script>
    </body>
    </html>
    """

@app.route('/logs')
def logs():
    """Data logs page"""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Weather Data Logs</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                background: linear-gradient(-45deg, #667eea, #764ba2, #f093fb, #4facfe);
                background-size: 400% 400%;
                animation: gradientShift 15s ease infinite;
                min-height: 100vh;
                padding: 20px;
                position: relative;
                overflow-x: hidden;
            }}

            @keyframes gradientShift {{
                0% {{ background-position: 0% 50%; }}
                50% {{ background-position: 100% 50%; }}
                100% {{ background-position: 0% 50%; }}
            }}

            body::before {{
                content: '';
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-image: 
                    radial-gradient(circle at 20% 50%, rgba(255, 255, 255, 0.15) 0%, transparent 50%),
                    radial-gradient(circle at 80% 80%, rgba(255, 255, 255, 0.15) 0%, transparent 50%),
                    radial-gradient(circle at 40% 20%, rgba(255, 255, 255, 0.1) 0%, transparent 50%);
                pointer-events: none;
                z-index: 0;
            }}

            .container {{
                max-width: 1600px;
                margin: 0 auto;
                position: relative;
                z-index: 1;
            }}

            header {{
                text-align: center;
                color: white;
                margin-bottom: 30px;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            }}

            h1 {{
                font-size: 2.5em;
                margin-bottom: 10px;
            }}

            nav {{
                background: rgba(255, 255, 255, 0.15);
                backdrop-filter: blur(10px);
                padding: 15px;
                border-radius: 15px;
                margin-bottom: 30px;
                display: flex;
                justify-content: center;
                gap: 20px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}

            nav a {{
                color: white;
                text-decoration: none;
                padding: 12px 24px;
                border-radius: 10px;
                background: rgba(255, 255, 255, 0.2);
                transition: all 0.3s;
                font-weight: 500;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}

            nav a:hover {{
                background: rgba(255, 255, 255, 0.35);
                transform: translateY(-2px);
            }}

            .table-container {{
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                padding: 30px;
                border-radius: 20px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                overflow-x: auto;
                border: 1px solid rgba(255, 255, 255, 0.5);
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
            }}

            th {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px;
                text-align: left;
                font-weight: bold;
                position: sticky;
                top: 0;
            }}

            td {{
                padding: 12px 15px;
                border-bottom: 1px solid #eee;
            }}

            tr:hover {{
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 30%);
            }}

            .actions {{
                text-align: center;
                margin-bottom: 20px;
            }}

            button {{
                padding: 12px 25px;
                font-size: 1em;
                border: none;
                border-radius: 12px;
                background: rgba(255, 255, 255, 0.95);
                color: #667eea;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s;
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
                border: 2px solid rgba(102, 126, 234, 0.3);
            }}

            button:hover {{
                transform: translateY(-3px);
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
                background: white;
            }}

            .db-info {{
                background: rgba(255, 255, 255, 0.15);
                backdrop-filter: blur(10px);
                color: white;
                padding: 20px;
                border-radius: 15px;
                text-align: center;
                margin-top: 30px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>📊 Weather Data Logs</h1>
                <p>Complete historical weather readings</p>
            </header>

            <nav>
                <a href="/">🏠 Home</a>
                <a href="/logs">📊 Data Logs</a>
                <a href="/graphs">📈 Graphs</a>
            </nav>

            <div class="actions">
                <button onclick="refreshTable()">🔄 Refresh</button>
            </div>

            <div class="table-container">
                <table id="data-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Timestamp</th>
                            <th>Temperature (°C)</th>
                            <th>Humidity (%)</th>
                            <th>Pressure (hPa)</th>
                            <th>Air Quality (AQI)</th>
                            <th>Wind Speed (km/h)</th>
                            <th>Wind Direction (°)</th>
                            <th>Rainfall (mm)</th>
                        </tr>
                    </thead>
                    <tbody id="table-body">
                        <!-- Data will be loaded here -->
                    </tbody>
                </table>
            </div>

            <div class="db-info">
                <strong>📁 Database:</strong> ./{DATABASE_PATH}<br>
                <strong>📝 Total Records:</strong> <span id="record-count">0</span>
            </div>
        </div>

        <script>
            async function loadTableData() {{
                try {{
                    const response = await fetch('/api/data');
                    const data = await response.json();

                    const tbody = document.getElementById('table-body');
                    tbody.innerHTML = '';

                    // Reverse to show newest first
                    data.reverse().forEach(row => {{
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td>${{row.id}}</td>
                            <td>${{new Date(row.timestamp).toLocaleString()}}</td>
                            <td>${{row.temperature}}</td>
                            <td>${{row.humidity}}</td>
                            <td>${{row.pressure}}</td>
                            <td>${{row.air_quality}}</td>
                            <td>${{row.wind_speed}}</td>
                            <td>${{row.wind_direction}}</td>
                            <td>${{row.rainfall}}</td>
                        `;
                        tbody.appendChild(tr);
                    }});

                    document.getElementById('record-count').textContent = data.length;
                }} catch (error) {{
                    console.error('Error loading table data:', error);
                }}
            }}

            function refreshTable() {{
                loadTableData();
            }}

            // Initial load
            loadTableData();

            // Auto-refresh every 10 seconds
            setInterval(loadTableData, 10000);
        </script>
    </body>
    </html>
    """

@app.route('/graphs')
def graphs():
    """Graphs page"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Weather Graphs</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                background: linear-gradient(-45deg, #667eea, #764ba2, #f093fb, #4facfe);
                background-size: 400% 400%;
                animation: gradientShift 15s ease infinite;
                min-height: 100vh;
                padding: 20px;
                position: relative;
                overflow-x: hidden;
            }

            @keyframes gradientShift {
                0% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }

            body::before {
                content: '';
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-image: 
                    radial-gradient(circle at 20% 50%, rgba(255, 255, 255, 0.15) 0%, transparent 50%),
                    radial-gradient(circle at 80% 80%, rgba(255, 255, 255, 0.15) 0%, transparent 50%),
                    radial-gradient(circle at 40% 20%, rgba(255, 255, 255, 0.1) 0%, transparent 50%);
                pointer-events: none;
                z-index: 0;
            }

            .container {
                max-width: 1600px;
                margin: 0 auto;
                position: relative;
                z-index: 1;
            }

            header {
                text-align: center;
                color: white;
                margin-bottom: 30px;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            }

            h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }

            nav {
                background: rgba(255, 255, 255, 0.15);
                backdrop-filter: blur(10px);
                padding: 15px;
                border-radius: 15px;
                margin-bottom: 30px;
                display: flex;
                justify-content: center;
                gap: 20px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }

            nav a {
                color: white;
                text-decoration: none;
                padding: 12px 24px;
                border-radius: 10px;
                background: rgba(255, 255, 255, 0.2);
                transition: all 0.3s;
                font-weight: 500;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }

            nav a:hover {
                background: rgba(255, 255, 255, 0.35);
                transform: translateY(-2px);
            }

            .charts-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }

            .chart-card {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                padding: 25px;
                border-radius: 20px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.5);
                transition: transform 0.3s;
            }

            .chart-card:hover {
                transform: translateY(-5px);
            }

            .chart-card h3 {
                margin-bottom: 15px;
                color: #333;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }

            canvas {
                max-height: 300px;
            }

            .db-info {
                background: rgba(255, 255, 255, 0.15);
                backdrop-filter: blur(10px);
                color: white;
                padding: 20px;
                border-radius: 15px;
                text-align: center;
                margin-top: 30px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }

            @media (max-width: 768px) {
                .charts-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>📈 Weather Graphs</h1>
                <p>Real-time interactive charts (auto-updates every 5 seconds)</p>
            </header>

            <nav>
                <a href="/">🏠 Home</a>
                <a href="/logs">📊 Data Logs</a>
                <a href="/graphs">📈 Graphs</a>
            </nav>

            <div class="charts-grid">
                <div class="chart-card">
                    <h3>🌡️ Temperature</h3>
                    <canvas id="tempChart"></canvas>
                </div>

                <div class="chart-card">
                    <h3>💧 Humidity</h3>
                    <canvas id="humidityChart"></canvas>
                </div>

                <div class="chart-card">
                    <h3>🎈 Pressure</h3>
                    <canvas id="pressureChart"></canvas>
                </div>

                <div class="chart-card">
                    <h3>💨 Air Quality</h3>
                    <canvas id="airQualityChart"></canvas>
                </div>

                <div class="chart-card">
                    <h3>🌪️ Wind Speed</h3>
                    <canvas id="windSpeedChart"></canvas>
                </div>

                <div class="chart-card">
                    <h3>🌧️ Rainfall</h3>
                    <canvas id="rainfallChart"></canvas>
                </div>

                <div class="chart-card">
                    <h3>🧭 Wind Direction</h3>
                    <canvas id="windDirectionChart"></canvas>
                </div>
            </div>

            <div class="db-info">
                Auto-updating every 5 seconds | Last 50 readings displayed
            </div>
        </div>

        <script>
            // Chart configurations with smooth animations
            const tempChart = new Chart(document.getElementById('tempChart'), {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Temperature (°C)',
                        data: [],
                        borderColor: '#FF6384',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            display: true
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false
                        }
                    }
                }
            });

            const humidityChart = new Chart(document.getElementById('humidityChart'), {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Humidity (%)',
                        data: [],
                        borderColor: '#36A2EB',
                        backgroundColor: 'rgba(54, 162, 235, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });

            const pressureChart = new Chart(document.getElementById('pressureChart'), {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Pressure (hPa)',
                        data: [],
                        borderColor: '#9966FF',
                        backgroundColor: 'rgba(153, 102, 255, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    scales: {
                        y: {
                            beginAtZero: false
                        }
                    }
                }
            });

            const airQualityChart = new Chart(document.getElementById('airQualityChart'), {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Air Quality (AQI)',
                        data: [],
                        backgroundColor: '#4BC0C0'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });

            const windSpeedChart = new Chart(document.getElementById('windSpeedChart'), {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Wind Speed (km/h)',
                        data: [],
                        borderColor: '#FF9F40',
                        backgroundColor: 'rgba(255, 159, 64, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });

            const rainfallChart = new Chart(document.getElementById('rainfallChart'), {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Rainfall (mm)',
                        data: [],
                        backgroundColor: '#1E88E5'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });

            const windDirectionChart = new Chart(document.getElementById('windDirectionChart'), {
                type: 'radar',
                data: {
                    labels: ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'],
                    datasets: [{
                        label: 'Wind Direction Frequency',
                        data: [0, 0, 0, 0, 0, 0, 0, 0],
                        backgroundColor: 'rgba(38, 166, 154, 0.2)',
                        borderColor: '#26A69A',
                        pointBackgroundColor: '#26A69A'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    scales: {
                        r: {
                            beginAtZero: true
                        }
                    }
                }
            });

            // Update all charts
            async function updateCharts() {
                try {
                    const response = await fetch('/api/data');
                    const data = await response.json();

                    // Get last 50 readings
                    const recent = data.slice(-50);

                    // Extract data
                    const labels = recent.map(r => new Date(r.timestamp).toLocaleTimeString());
                    const temps = recent.map(r => r.temperature);
                    const humidity = recent.map(r => r.humidity);
                    const pressure = recent.map(r => r.pressure);
                    const airQuality = recent.map(r => r.air_quality);
                    const windSpeed = recent.map(r => r.wind_speed);
                    const rainfall = recent.map(r => r.rainfall);

                    // Update line/bar charts
                    tempChart.data.labels = labels;
                    tempChart.data.datasets[0].data = temps;
                    tempChart.update('none');

                    humidityChart.data.labels = labels;
                    humidityChart.data.datasets[0].data = humidity;
                    humidityChart.update('none');

                    pressureChart.data.labels = labels;
                    pressureChart.data.datasets[0].data = pressure;
                    pressureChart.update('none');

                    airQualityChart.data.labels = labels;
                    airQualityChart.data.datasets[0].data = airQuality;
                    airQualityChart.update('none');

                    windSpeedChart.data.labels = labels;
                    windSpeedChart.data.datasets[0].data = windSpeed;
                    windSpeedChart.update('none');

                    rainfallChart.data.labels = labels;
                    rainfallChart.data.datasets[0].data = rainfall;
                    rainfallChart.update('none');

                    // Update wind direction chart (frequency distribution)
                    const directionBins = [0, 0, 0, 0, 0, 0, 0, 0];
                    recent.forEach(r => {
                        const dir = r.wind_direction;
                        const bin = Math.floor(dir / 45) % 8;
                        directionBins[bin]++;
                    });

                    windDirectionChart.data.datasets[0].data = directionBins;
                    windDirectionChart.update('none');

                } catch (error) {
                    console.error('Error updating charts:', error);
                }
            }

            // Initial update
            updateCharts();

            // Auto-update every 5 seconds
            setInterval(updateCharts, 5000);
        </script>
    </body>
    </html>
    """

# Continue with API endpoints (same as before)
@app.route('/api/data', methods=['GET', 'POST'])

def api_data():
    """GET: Return all weather readings / POST: Insert new reading"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            required_fields = ['temperature', 'humidity', 'pressure', 
                             'air_quality', 'wind_speed', 'wind_direction', 'rainfall']

            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400

            # Use IST time for timestamp
            if 'timestamp' not in data:
                IST = timedelta(hours=5, minutes=30)
                data['timestamp'] = (datetime.utcnow() + IST).isoformat()

            df = pd.DataFrame([data])
            conn = sqlite3.connect(DATABASE_PATH)
            df.to_sql('weather_readings', conn, if_exists='append', index=False)
            conn.close()

            return jsonify({
                'success': True,
                'message': 'Data inserted successfully',
                'data': data
            }), 201


        except Exception as e:
            return jsonify({'error': str(e)}), 500

    else:
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            df = pd.read_sql_query("SELECT * FROM weather_readings ORDER BY timestamp", conn)
            conn.close()
            data = df.to_dict('records')
            return jsonify(data), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/latest', methods=['GET'])
def api_latest():
    """Return the most recent weather reading"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        df = pd.read_sql_query(
            "SELECT * FROM weather_readings ORDER BY timestamp DESC LIMIT 1",
            conn
        )
        conn.close()

        if len(df) == 0:
            return jsonify({'error': 'No data available'}), 404

        data = df.to_dict('records')[0]
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['GET'])
def api_export():
    """Export all weather data as CSV file"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        df = pd.read_sql_query("SELECT * FROM weather_readings ORDER BY timestamp", conn)
        conn.close()

        output = io.BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'weather_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Return summary statistics of weather data"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        df = pd.read_sql_query("SELECT * FROM weather_readings", conn)
        conn.close()

        if len(df) == 0:
            return jsonify({'error': 'No data available'}), 404

        stats = {
            'total_readings': len(df),
            'avg_temperature': float(df['temperature'].mean()),
            'min_temperature': float(df['temperature'].min()),
            'max_temperature': float(df['temperature'].max()),
            'avg_humidity': float(df['humidity'].mean()),
            'min_humidity': float(df['humidity'].min()),
            'max_humidity': float(df['humidity'].max()),
            'avg_pressure': float(df['pressure'].mean()),
            'min_pressure': float(df['pressure'].min()),
            'max_pressure': float(df['pressure'].max()),
            'avg_air_quality': float(df['air_quality'].mean()),
            'min_air_quality': int(df['air_quality'].min()),
            'max_air_quality': int(df['air_quality'].max()),
            'avg_wind_speed': float(df['wind_speed'].mean()),
            'min_wind_speed': float(df['wind_speed'].min()),
            'max_wind_speed': float(df['wind_speed'].max()),
            'total_rainfall': float(df['rainfall'].sum()),
            'avg_rainfall': float(df['rainfall'].mean())
        }

        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Initializing Weather Monitoring System...")
    init_database()
    print(f"Database: {os.path.abspath(DATABASE_PATH)}")
    print("Starting Flask server...")
    print("Access the enhanced dashboard at: http://localhost:5000")

    app.run(debug=True, host='0.0.0.0', port=5000)
