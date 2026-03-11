"""FastAPI web dashboard for email tracker."""

import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pathlib import Path
from datetime import datetime, timezone

from ..models import EmailStatus
from ..sheets_logger import SheetsLogger

logger = logging.getLogger(__name__)

__all__ = ["EmailTrackerDashboard"]


class EmailTrackerDashboard:
    """FastAPI dashboard for email tracking."""

    def __init__(self, sheets_logger: SheetsLogger, port: int = 8000, scheduler=None):
        """Initialize dashboard.
        
        Args:
            sheets_logger: SheetsLogger instance
            port: Port to run the dashboard on
            scheduler: EmailScheduler instance (optional, for manual processing)
        """
        self.sheets_logger = sheets_logger
        self.scheduler = scheduler
        self.port = port
        self.app = FastAPI(title="Email Tracker Dashboard")
        self._stats_cache = {}
        self._stats_cache_time = None
        self._stats_cache_ttl = 60  # seconds between Sheets API reads
        self.setup_routes()

    def _get_cached_stats(self) -> dict:
        """Return stats from cache; refresh from Sheets only when TTL expires."""
        now = datetime.now(timezone.utc)
        if (
            self._stats_cache_time is None
            or (now - self._stats_cache_time).total_seconds() >= self._stats_cache_ttl
        ):
            self._stats_cache = self.sheets_logger.get_statistics()
            self._stats_cache_time = now
        return self._stats_cache

    def setup_routes(self) -> None:
        """Setup FastAPI routes."""

        @self.app.get("/", response_class=HTMLResponse)
        async def home():
            """Serve dashboard HTML."""
            return self._get_dashboard_html()

        @self.app.get("/api/stats")
        async def get_stats():
            """Get email statistics."""
            stats = self._get_cached_stats()
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "stats": stats,
                "percentages": self._calculate_percentages(stats),
            }

        @self.app.get("/api/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

        @self.app.post("/api/process-now")
        async def process_now():
            """Manually trigger email processing immediately."""
            if not self.scheduler:
                return {
                    "status": "error",
                    "message": "Scheduler not available",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            try:
                logger.info("Manual email processing triggered")
                asyncio.create_task(self.scheduler._process_emails())
                return {
                    "status": "success",
                    "message": "Email processing started",
                    "timestamp": datetime.utcnow().isoformat()
                }
            except Exception as e:
                logger.error(f"Error processing emails: {e}")
                return {
                    "status": "error",
                    "message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }

        @self.app.websocket("/ws/stats")
        async def websocket_stats(websocket: WebSocket):
            """WebSocket endpoint for real-time statistics updates."""
            await websocket.accept()
            try:
                while True:
                    # Send stats every 5 seconds (uses cache to avoid rate limits)
                    stats = self._get_cached_stats()
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
                "ongoing": 0,
                "answered": 0,
                "manual_reply": 0,
                "done": 0,
            }

        return {
            "incoming": round((stats.get("incoming", 0) / total) * 100, 1),
            "pending": round((stats.get("pending", 0) / total) * 100, 1),
            "ongoing": round((stats.get("ongoing", 0) / total) * 100, 1),
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
    <title>UP OAR Email Tracker</title>
    <link href="https://fonts.googleapis.com/css2?family=EB+Garamond:wght@400;600;700&family=Open+Sans:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --maroon: #7B1113;
            --maroon-dark: #5a0c0e;
            --maroon-light: #9e161a;
            --gold: #F0C040;
            --gold-light: #f5d060;
            --white: #ffffff;
            --off-white: #faf8f5;
            --gray-light: #f0eeeb;
            --gray: #888;
            --text-dark: #2c2c2c;
            --shadow: 0 4px 20px rgba(123,17,19,0.10);
            --shadow-hover: 0 8px 32px rgba(123,17,19,0.18);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Open Sans', 'Segoe UI', sans-serif;
            background: #f5f0ee;
            min-height: 100vh;
        }

        /* ── Top banner ── */
        .top-banner {
            background: var(--maroon-dark);
            color: var(--gold);
            text-align: center;
            padding: 6px 20px;
            font-size: 0.78em;
            letter-spacing: 0.08em;
            font-family: 'Open Sans', sans-serif;
            font-weight: 600;
            text-transform: uppercase;
        }

        /* ── Header ── */
        .site-header {
            background: linear-gradient(135deg, var(--maroon-dark) 0%, var(--maroon) 60%, var(--maroon-light) 100%);
            color: white;
            padding: 30px 20px 24px;
            text-align: center;
            border-bottom: 4px solid var(--gold);
            box-shadow: 0 4px 16px rgba(0,0,0,0.25);
        }

        .header-logo-row {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 20px;
            margin-bottom: 14px;
        }

        /* SVG shield placeholder for UP seal */
        .up-seal {
            width: 72px;
            height: 72px;
            flex-shrink: 0;
        }

        .header-titles {
            text-align: left;
        }

        .header-titles .institution {
            font-family: 'Open Sans', sans-serif;
            font-size: 0.78em;
            font-weight: 600;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: var(--gold);
            margin-bottom: 4px;
        }

        .header-titles h1 {
            font-family: 'EB Garamond', Georgia, serif;
            font-size: 2em;
            font-weight: 700;
            color: white;
            line-height: 1.15;
        }

        .header-titles .subtitle {
            font-size: 0.85em;
            color: rgba(255,255,255,0.80);
            margin-top: 4px;
            font-style: italic;
        }

        .header-divider {
            width: 60px;
            height: 3px;
            background: var(--gold);
            margin: 12px auto 0;
            border-radius: 2px;
        }

        #timestamp {
            font-size: 0.8em;
            color: rgba(255,255,255,0.65);
            margin-top: 8px;
        }

        /* ── Page body ── */
        .page-body {
            max-width: 1200px;
            margin: 0 auto;
            padding: 30px 20px 50px;
        }

        /* ── Section label ── */
        .section-label {
            font-family: 'Open Sans', sans-serif;
            font-size: 0.72em;
            font-weight: 700;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: var(--maroon);
            margin-bottom: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .section-label::after {
            content: '';
            flex: 1;
            height: 1px;
            background: rgba(123,17,19,0.15);
        }

        /* ── Action bar ── */
        .action-bar {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 28px;
            flex-wrap: wrap;
        }

        .btn-process {
            background: var(--maroon);
            color: white;
            border: none;
            padding: 11px 28px;
            font-size: 0.92em;
            font-family: 'Open Sans', sans-serif;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.2s, box-shadow 0.2s, transform 0.15s;
            box-shadow: 0 3px 12px rgba(123,17,19,0.30);
            letter-spacing: 0.03em;
        }
        .btn-process:hover {
            background: var(--maroon-dark);
            box-shadow: 0 5px 18px rgba(123,17,19,0.40);
            transform: translateY(-1px);
        }
        .btn-process:active { transform: translateY(0); }
        .btn-process:disabled { opacity: 0.55; cursor: not-allowed; transform: none; }

        #processStatus {
            font-size: 0.88em;
            font-weight: 500;
        }

        /* ── Stat cards ── */
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 18px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: var(--white);
            border-radius: 10px;
            padding: 22px 20px;
            box-shadow: var(--shadow);
            transition: transform 0.25s, box-shadow 0.25s;
            border-top: 4px solid transparent;
        }
        .stat-card:hover {
            transform: translateY(-4px);
            box-shadow: var(--shadow-hover);
        }

        .stat-card.incoming  { border-top-color: #2980b9; }
        .stat-card.pending   { border-top-color: #e67e22; }
        .stat-card.answered  { border-top-color: #27ae60; }
        .stat-card.manual    { border-top-color: #c0392b; }
        .stat-card.done      { border-top-color: var(--maroon); }

        .stat-icon {
            font-size: 1.6em;
            margin-bottom: 8px;
        }

        .stat-label {
            font-size: 0.75em;
            color: var(--gray);
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .stat-value {
            font-family: 'EB Garamond', Georgia, serif;
            font-size: 2.8em;
            font-weight: 700;
            color: var(--text-dark);
            line-height: 1;
            margin-bottom: 4px;
        }

        .stat-percentage {
            font-size: 0.82em;
            color: #aaa;
        }

        /* ── Chart card ── */
        .card {
            background: var(--white);
            border-radius: 10px;
            padding: 24px 26px;
            box-shadow: var(--shadow);
            margin-bottom: 24px;
        }

        .card-title {
            font-family: 'EB Garamond', Georgia, serif;
            font-size: 1.25em;
            font-weight: 700;
            color: var(--maroon);
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(123,17,19,0.12);
        }

        /* ── Bar chart ── */
        .bar-row {
            margin-bottom: 18px;
        }
        .bar-row:last-child { margin-bottom: 0; }

        .bar-meta {
            display: flex;
            justify-content: space-between;
            margin-bottom: 6px;
        }
        .bar-meta-label {
            font-size: 0.88em;
            font-weight: 600;
            color: var(--text-dark);
        }
        .bar-meta-count {
            font-size: 0.85em;
            color: var(--gray);
        }

        .bar-track {
            background: #ede8e4;
            border-radius: 4px;
            height: 14px;
            overflow: hidden;
        }
        .bar-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.6s ease;
        }

        /* ── Status list ── */
        .status-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 0;
            border-bottom: 1px solid #f0eeeb;
        }
        .status-item:last-child { border-bottom: none; }
        .status-item:hover { background: transparent; }

        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 10px;
            flex-shrink: 0;
        }

        .status-name {
            font-weight: 500;
            color: var(--text-dark);
            display: flex;
            align-items: center;
        }

        .status-mini-bar {
            width: 120px;
            height: 6px;
            background: #ede8e4;
            border-radius: 3px;
            overflow: hidden;
            margin: 0 18px;
        }
        .status-mini-fill {
            height: 100%;
            border-radius: 3px;
            transition: width 0.5s ease;
        }

        .status-value {
            font-family: 'EB Garamond', Georgia, serif;
            font-size: 1.35em;
            font-weight: 700;
            color: var(--maroon);
            min-width: 36px;
            text-align: right;
        }

        /* ── Footer ── */
        .site-footer {
            background: var(--maroon-dark);
            color: rgba(255,255,255,0.55);
            text-align: center;
            padding: 14px 20px;
            font-size: 0.78em;
            letter-spacing: 0.04em;
        }
        .site-footer strong { color: var(--gold); }

        /* ── Loading placeholder ── */
        .loading-placeholder {
            color: var(--maroon);
            padding: 40px;
            text-align: center;
            font-family: 'EB Garamond', Georgia, serif;
            font-size: 1.2em;
        }

        @media (max-width: 768px) {
            .header-logo-row { flex-direction: column; gap: 12px; }
            .header-titles { text-align: center; }
            .header-titles h1 { font-size: 1.5em; }
            .dashboard-grid { grid-template-columns: 1fr 1fr; }
            .status-mini-bar { display: none; }
        }
        @media (max-width: 480px) {
            .dashboard-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>

    <div class="top-banner">University of the Philippines &mdash; Office of Alumni Relations</div>

    <header class="site-header">
        <div class="header-logo-row">
            <!-- UP Seal (inline SVG shield) -->
            <svg class="up-seal" viewBox="0 0 72 72" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label="UP Seal">
                <ellipse cx="36" cy="36" r="34" fill="#f0c040" opacity="0.15"/>
                <ellipse cx="36" cy="36" r="34" stroke="#f0c040" stroke-width="2.5"/>
                <ellipse cx="36" cy="36" r="28" stroke="#f0c040" stroke-width="1" stroke-dasharray="3 2"/>
                <text x="36" y="30" text-anchor="middle" font-family="Georgia,serif" font-size="13" font-weight="bold" fill="#f0c040">UP</text>
                <text x="36" y="44" text-anchor="middle" font-family="Georgia,serif" font-size="6.5" fill="#f0c040" letter-spacing="1">MDCCCCVIII</text>
                <text x="36" y="56" text-anchor="middle" font-family="Georgia,serif" font-size="5.5" fill="rgba(240,192,64,0.7)" letter-spacing="0.8">HONOR &amp; EXCELLENCE</text>
            </svg>
            <div class="header-titles">
                <div class="institution">University of the Philippines &bull; OAR</div>
                <h1>Alumni Email Tracker</h1>
                <div class="subtitle">Automated Email Management &amp; Analytics Dashboard</div>
            </div>
        </div>
        <div class="header-divider"></div>
        <div id="timestamp"></div>
    </header>

    <main class="page-body">

        <div class="action-bar">
            <div class="section-label" style="margin-bottom:0; flex:unset;">Actions</div>
            <button id="processBtn" class="btn-process" onclick="processNow()">
                &#9654;&nbsp; Process Emails Now
            </button>
            <div id="processStatus"></div>
        </div>

        <div class="section-label">Overview</div>
        <div class="dashboard-grid" id="statsGrid">
            <div class="loading-placeholder">Loading statistics&hellip;</div>
        </div>

        <div class="section-label">Email Volume by Status</div>
        <div class="card">
            <div class="card-title">Status Breakdown</div>
            <div id="statsChart"></div>
        </div>

        <div class="section-label">Detailed Summary</div>
        <div class="card">
            <div class="card-title">Email Status Summary</div>
            <div id="statusList"></div>
        </div>

    </main>

    <footer class="site-footer">
        <strong>UP Office of Alumni Relations</strong> &mdash; Alumni Email Tracker &copy; 2025
    </footer>

    <script>
        const STATUS_META = [
            { key: 'incoming',     label: 'Incoming',           icon: '&#128386;', color: '#2980b9', cardClass: 'incoming' },
            { key: 'pending',      label: 'Pending Review',      icon: '&#9203;',   color: '#e67e22', cardClass: 'pending'  },
            { key: 'ongoing',      label: 'Opened / Read',       icon: '&#128065;', color: '#16a085', cardClass: 'pending'  },
            { key: 'done',         label: 'Auto Answered',       icon: '&#9989;',   color: '#27ae60', cardClass: 'answered' },
            { key: 'manual_reply', label: 'Needs Manual Reply',  icon: '&#9997;',   color: '#c0392b', cardClass: 'manual'   },
        ];

        async function updateStats() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();
                updateTimestamp(data.timestamp);
                updateStatCards(data.stats, data.percentages);
                updateChart(data.stats);
                updateStatusList(data.stats, data.percentages);
            } catch (error) {
                console.error('Error fetching stats:', error);
                document.getElementById('statsGrid').innerHTML =
                    '<div style="color:#c0392b; padding:20px;">Error loading statistics: ' + error.message + '</div>';
            }
        }

        function updateTimestamp(ts) {
            const d = new Date(ts);
            document.getElementById('timestamp').textContent = 'Last updated: ' + d.toLocaleString();
        }

        function updateStatCards(stats, percentages) {
            const cards = STATUS_META.filter(m => ['incoming','pending','done','manual_reply'].includes(m.key));
            const html = cards.map(m => `
                <div class="stat-card ${m.cardClass}">
                    <div class="stat-icon">${m.icon}</div>
                    <div class="stat-label">${m.label}</div>
                    <div class="stat-value">${stats[m.key] || 0}</div>
                    <div class="stat-percentage">${percentages[m.key] || 0}% of total</div>
                </div>
            `).join('');
            document.getElementById('statsGrid').innerHTML = html;
        }

        function updateChart(stats) {
            const container = document.getElementById('statsChart');
            if (!container) return;
            const total = Math.max(stats.total || 1, 1);
            container.innerHTML = STATUS_META.map(m => {
                const count = stats[m.key] || 0;
                const pct = (count / total * 100).toFixed(1);
                return `
                    <div class="bar-row">
                        <div class="bar-meta">
                            <span class="bar-meta-label">${m.icon} ${m.label}</span>
                            <span class="bar-meta-count">${count} &nbsp;(${pct}%)</span>
                        </div>
                        <div class="bar-track">
                            <div class="bar-fill" style="width:${pct}%; background:${m.color};"></div>
                        </div>
                    </div>`;
            }).join('');
        }

        function updateStatusList(stats, percentages) {
            const html = STATUS_META.map(m => `
                <div class="status-item">
                    <span class="status-name">
                        <span class="status-dot" style="background:${m.color};"></span>
                        ${m.label}
                    </span>
                    <div class="status-mini-bar">
                        <div class="status-mini-fill" style="width:${percentages[m.key]||0}%; background:${m.color};"></div>
                    </div>
                    <div class="status-value">${stats[m.key] || 0}</div>
                </div>
            `).join('');
            document.getElementById('statusList').innerHTML = html;
        }

        async function processNow() {
            const btn = document.getElementById('processBtn');
            const statusDiv = document.getElementById('processStatus');
            btn.disabled = true;
            statusDiv.innerHTML = '<span style="color:#e67e22;">&#8987; Processing&hellip;</span>';
            try {
                const response = await fetch('/api/process-now', { method: 'POST' });
                const data = await response.json();
                if (data.status === 'success') {
                    statusDiv.innerHTML = '<span style="color:#27ae60;">&#10003; Processing completed!</span>';
                    setTimeout(updateStats, 1200);
                } else {
                    statusDiv.innerHTML = '<span style="color:#c0392b;">&#10007; ' + data.message + '</span>';
                }
            } catch (err) {
                statusDiv.innerHTML = '<span style="color:#c0392b;">&#10007; ' + err.message + '</span>';
            } finally {
                btn.disabled = false;
                setTimeout(() => { statusDiv.innerHTML = ''; }, 6000);
            }
        }

        function connectWebSocket() {
            const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
            const ws = new WebSocket(proto + '//' + location.host + '/ws/stats');
            ws.onmessage = e => {
                const data = JSON.parse(e.data);
                updateTimestamp(data.timestamp);
                updateStatCards(data.stats, data.percentages);
                updateChart(data.stats);
                updateStatusList(data.stats, data.percentages);
            };
            ws.onerror = () => console.log('WS error, using polling');
            ws.onclose = () => setTimeout(connectWebSocket, 3000);
        }

        updateStats();
        setTimeout(updateStats, 1000);
        setInterval(updateStats, 10000);
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
