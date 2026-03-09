"""FastAPI web dashboard for email tracker."""

import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pathlib import Path
from datetime import datetime

from ..models import EmailStatus
from ..sheets_logger import SheetsLogger

logger = logging.getLogger(__name__)

__all__ = ["EmailTrackerDashboard"]


class EmailTrackerDashboard:
    """FastAPI dashboard for email tracking."""

    def __init__(self, sheets_logger: SheetsLogger, port: int = 8000):
        """Initialize dashboard.
        
        Args:
            sheets_logger: SheetsLogger instance
            port: Port to run the dashboard on
        """
        self.sheets_logger = sheets_logger
        self.port = port
        self.app = FastAPI(title="Email Tracker Dashboard")
        self.setup_routes()

    def setup_routes(self) -> None:
        """Setup FastAPI routes."""

        @self.app.get("/", response_class=HTMLResponse)
        async def home():
            """Serve dashboard HTML."""
            return self._get_dashboard_html()

        @self.app.get("/api/stats")
        async def get_stats():
            """Get email statistics."""
            stats = self.sheets_logger.get_statistics()
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "stats": stats,
                "percentages": self._calculate_percentages(stats),
            }

        @self.app.get("/api/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

        @self.app.websocket("/ws/stats")
        async def websocket_stats(websocket: WebSocket):
            """WebSocket endpoint for real-time statistics updates."""
            await websocket.accept()
            try:
                while True:
                    # Send stats every 5 seconds
                    stats = self.sheets_logger.get_statistics()
                    await websocket.send_json({
                        "timestamp": datetime.utcnow().isoformat(),
                        "stats": stats,
                        "percentages": self._calculate_percentages(stats),
                    })
                    await asyncio.sleep(5)
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.close()

    def _calculate_percentages(self, stats: dict) -> dict:
        """Calculate status percentages."""
        total = stats.get("total", 0)
        if total == 0:
            return {
                "incoming": 0,
                "pending": 0,
                "answered": 0,
                "manual_reply": 0,
                "done": 0,
            }

        return {
            "incoming": round((stats.get("incoming", 0) / total) * 100, 1),
            "pending": round((stats.get("pending", 0) / total) * 100, 1),
            "answered": round((stats.get("answered", 0) / total) * 100, 1),
            "manual_reply": round((stats.get("manual_reply", 0) / total) * 100, 1),
            "done": round((stats.get("done", 0) / total) * 100, 1),
        }

    def _get_dashboard_html(self) -> str:
        """Get dashboard HTML."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Tracker Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }

        .timestamp {
            font-size: 0.9em;
            color: rgba(255, 255, 255, 0.7);
            margin-top: 10px;
        }

        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
        }

        .stat-label {
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }

        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }

        .stat-percentage {
            font-size: 0.85em;
            color: #999;
        }

        .stat-card.incoming { border-left: 5px solid #3498db; }
        .stat-card.pending { border-left: 5px solid #f39c12; }
        .stat-card.answered { border-left: 5px solid #27ae60; }
        .stat-card.manual { border-left: 5px solid #e74c3c; }
        .stat-card.done { border-left: 5px solid #9b59b6; }

        .chart-container {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
        }

        .chart-wrapper {
            position: relative;
            width: 100%;
            padding: 20px 0;
        }
        
        #statsChart {
            width: 100%;
        }

        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(900px, 1fr));
            gap: 20px;
        }

        .status-list {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }

        .status-list h3 {
            margin-bottom: 20px;
            color: #333;
            font-size: 1.3em;
        }

        .status-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            border-bottom: 1px solid #eee;
            transition: background 0.2s ease;
        }

        .status-item:last-child {
            border-bottom: none;
        }

        .status-item:hover {
            background: #f9f9f9;
        }

        .status-name {
            font-weight: 500;
            color: #333;
        }

        .status-value {
            font-size: 1.3em;
            font-weight: bold;
            color: #667eea;
        }

        .status-bar {
            width: 150px;
            height: 8px;
            background: #eee;
            border-radius: 4px;
            overflow: hidden;
        }

        .status-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.5s ease;
        }

        .loading {
            text-align: center;
            color: white;
            font-size: 1.1em;
        }

        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.8em;
            }

            .dashboard-grid {
                grid-template-columns: 1fr;
            }

            .status-grid {
                grid-template-columns: 1fr;
            }

            .stat-value {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📧 Email Tracker Dashboard</h1>
            <p>Automated Email Management & Analytics</p>
            <div class="timestamp" id="timestamp"></div>
        </div>

        <div class="dashboard-grid" id="statsGrid">
            <div style="color: white; padding: 40px; text-align: center;">
                <h2>Loading Dashboard...</h2>
                <p>If data doesn't appear, check the browser console (F12)</p>
                <div id="dataDisplay" style="margin-top: 20px; color: #fff; font-family: monospace; font-size: 12px; white-space: pre-wrap; background: rgba(0,0,0,0.5); padding: 20px; border-radius: 5px; text-align: left;"></div>
            </div>
        </div>

        <div class="chart-container">
            <h2 style="margin-bottom: 20px; color: #333;">Email Statistics</h2>
            <div class="chart-wrapper">
                <div id="statsChart"></div>
            </div>
        </div>

        <div class="status-grid">
            <div class="status-list">
                <h3>Email Status Summary</h3>
                <div id="statusList"></div>
            </div>
        </div>
    </div>

    <script>
        let chart = null;

        function displayData(data) {
            // Display raw JSON in debug area for reference
            const debugArea = document.getElementById('dataDisplay');
            if (debugArea) {
                debugArea.textContent = JSON.stringify(data, null, 2);
            }
        }

        async function updateStats() {
            try {
                console.log('Fetching stats from /api/stats...');
                const response = await fetch('/api/stats');
                console.log('Response status:', response.status);
                const data = await response.json();
                console.log('Received data:', data);
                
                // Display the raw data
                displayData(data);

                updateTimestamp(data.timestamp);
                updateStatCards(data.stats, data.percentages);
                updateChart(data.stats);
                updateStatusList(data.stats, data.percentages);
                console.log('Stats updated successfully');
            } catch (error) {
                console.error('Error fetching stats:', error);
                // Show error in UI
                document.getElementById('statsGrid').innerHTML = 
                    '<div style="color: red; text-align: center; padding: 20px;">Error loading statistics: ' + error.message + '</div>';
            }
        }

        function updateTimestamp(timestamp) {
            const date = new Date(timestamp);
            document.getElementById('timestamp').textContent =
                `Last updated: ${date.toLocaleString()}`;
        }

        function updateStatCards(stats, percentages) {
            console.log('Updating stat cards with:', stats, percentages);
            const cards = [
                { key: 'incoming', label: 'Incoming', class: 'incoming' },
                { key: 'pending', label: 'Pending', class: 'pending' },
                { key: 'answered', label: 'Auto Answered', class: 'answered' },
                { key: 'manual_reply', label: 'Need Manual Reply', class: 'manual' },
                { key: 'done', label: 'Completed', class: 'done' },
            ];

            const html = cards.map(card => `
                <div class="stat-card ${card.class}">
                    <div class="stat-label">${card.label}</div>
                    <div class="stat-value">${stats[card.key] || 0}</div>
                    <div class="stat-percentage">${percentages[card.key] || 0}%</div>
                </div>
            `).join('');

            document.getElementById('statsGrid').innerHTML = html;
            console.log('Stat cards updated');
        }

        function updateChart(stats) {
            // Create a simple HTML-based bar chart without requiring Chart.js
            const total = stats.total || 100;
            const chartContainer = document.getElementById('statsChart');
            
            if (!chartContainer) {
                console.warn('Chart container not found');
                return;
            }
            
            // Clear existing content
            chartContainer.innerHTML = '';
            chartContainer.style.width = '100%';
            chartContainer.style.height = 'auto';
            
            // Create bars for each status
            const statuses = [
                { key: 'incoming', label: 'Incoming', color: '#3498db' },
                { key: 'pending', label: 'Pending Review', color: '#f39c12' },
                { key: 'answered', label: 'Auto Answered', color: '#27ae60' },
                { key: 'manual_reply', label: 'Need Manual Reply', color: '#e74c3c' },
                { key: 'done', label: 'Completed', color: '#9b59b6' }
            ];
            
            statuses.forEach(status => {
                const count = stats[status.key] || 0;
                const percentage = total > 0 ? (count / total * 100) : 0;
                
                const barHtml = `
                    <div style="margin-bottom: 20px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                            <span style="font-weight: 500; color: #333;">${status.label}</span>
                            <span style="color: #666;">${count} (${percentage.toFixed(1)}%)</span>
                        </div>
                        <div style="background: #e0e0e0; border-radius: 4px; height: 20px; overflow: hidden;">
                            <div style="background: ${status.color}; height: 100%; width: ${percentage}%; transition: width 0.5s ease;"></div>
                        </div>
                    </div>
                `;
                chartContainer.innerHTML += barHtml;
            });
        }

        function updateStatusList(stats, percentages) {
            const items = [
                { label: 'Incoming', key: 'incoming', color: '#3498db' },
                { label: 'Pending Review', key: 'pending', color: '#f39c12' },
                { label: 'Auto Answered', key: 'answered', color: '#27ae60' },
                { label: 'Need Manual Reply', key: 'manual_reply', color: '#e74c3c' },
                { label: 'Completed', key: 'done', color: '#9b59b6' },
            ];

            const html = items.map(item => `
                <div class="status-item">
                    <div>
                        <div class="status-name">${item.label}</div>
                        <div class="status-bar">
                            <div class="status-bar-fill"
                                 style="width: ${percentages[item.key]}%; background: ${item.color};"></div>
                        </div>
                    </div>
                    <div class="status-value">${stats[item.key] || 0}</div>
                </div>
            `).join('');

            document.getElementById('statusList').innerHTML = html;
        }

        // Initial load - show some data immediately
        console.log('Dashboard loaded, starting initial data load...');
        updateStats();
        
        // Also try to load immediately with cached/saved data
        setTimeout(() => {
            console.log('Attempting immediate stats update...');
            updateStats();
        }, 1000);

        // Update stats every 10 seconds
        setInterval(updateStats, 10000);

        // Try WebSocket connection for real-time updates
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const ws = new WebSocket(`${protocol}//${window.location.host}/ws/stats`);

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateTimestamp(data.timestamp);
                updateStatCards(data.stats, data.percentages);
                updateChart(data.stats);
                updateStatusList(data.stats, data.percentages);
            };

            ws.onerror = (error) => {
                console.log('WebSocket error, falling back to polling', error);
            };

            ws.onclose = () => {
                // Reconnect after 3 seconds
                setTimeout(connectWebSocket, 3000);
            };
        }

        connectWebSocket();
    </script>
</body>
</html>
        """

    def run(self) -> None:
        """Run the dashboard server."""
        import uvicorn

        logger.info(f"Starting Email Tracker Dashboard on http://localhost:{self.port}")
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)
