#!/bin/bash
# Update system packages using dnf 
sudo dnf update -y

# Install Python3, pip
sudo dnf install -y python3 python3-pip

# Install Flask, psutil, and Flask-CORS
sudo pip3 install flask psutil Flask-Cors

# Install the 'stress' tool on Amazon Linux 2023
sudo dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm || true
sudo dnf install -y stress

# Create Flask application directory and app.py
cat << 'EOF' > /home/ec2-user/app.py
from flask import Flask, render_template_string, jsonify
from flask_cors import CORS
import psutil
import subprocess
import multiprocessing

app = Flask(__name__)
CORS(app)

stress_process = None

@app.route('/')
def index():
    hostname = subprocess.check_output(['hostname']).decode('utf-8').strip()
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Milan Rai | Enterprise Cloud Architecture</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;700&display=swap');

        body, html {
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            font-family: 'Inter', sans-serif;
            background-color: #0f172a; /* Deep Slate / Midnight */
            color: #f8fafc;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .dashboard-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 45px 40px;
            max-width: 650px;
            width: 90%;
            text-align: center;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
        }

        .brand-header {
            font-size: 0.8rem;
            letter-spacing: 4px;
            color: #94a3b8;
            text-transform: uppercase;
            font-weight: 500;
            margin-bottom: 12px;
            display: block;
        }

        h1 {
            font-size: 2.4rem;
            margin: 0 0 8px 0;
            font-weight: 700;
            letter-spacing: -0.5px;
            color: #f1f5f9;
        }

        .subtitle {
            font-size: 1.05rem;
            color: #cbd5e1;
            margin-bottom: 35px;
            font-weight: 300;
        }

        .server-metrics {
            background: rgba(0, 0, 0, 0.25);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 35px;
            text-align: left;
        }

        .metric-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .metric-label {
            color: #94a3b8;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .metric-value {
            font-family: monospace;
            font-size: 1.1rem;
            color: #38bdf8;
            background: rgba(56, 189, 248, 0.1);
            padding: 4px 10px;
            border-radius: 6px;
        }

        .meter-bg {
            background: #1e293b;
            border-radius: 20px;
            height: 12px;
            width: 100%;
            overflow: hidden;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
            margin-bottom: 8px;
        }

        .meter-fill {
            height: 100%;
            background: #38bdf8; /* Sleek Tech Blue */
            width: 0%;
            border-radius: 20px;
            transition: width 0.4s ease-out, background-color 0.4s ease;
        }

        #cpu-text {
            font-size: 0.95rem;
            font-weight: 500;
            color: #e2e8f0;
            text-align: right;
            margin: 0;
        }

        .controls {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-bottom: 30px;
        }

        button {
            padding: 12px 24px;
            font-size: 0.9rem;
            font-weight: 500;
            letter-spacing: 0.5px;
            border: 1px solid transparent;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .btn-primary {
            background-color: #f8fafc;
            color: #0f172a;
        }

        .btn-primary:hover {
            background-color: #e2e8f0;
            transform: translateY(-2px);
        }

        .btn-secondary {
            background-color: transparent;
            color: #f8fafc;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .btn-secondary:hover {
            background-color: rgba(255, 255, 255, 0.05);
            border-color: rgba(255, 255, 255, 0.4);
            color: #f87171;
        }

        .footer {
            font-size: 0.85rem;
            color: #64748b;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            padding-top: 20px;
        }

        .footer strong {
            color: #f1f5f9;
            font-weight: 500;
        }
    </style>
</head>
<body onload="updateCpuUsage()">
    <div class="dashboard-card">
        <span class="brand-header">Live Server Telemetry</span>
        <h1>AWS Scalable Architecture</h1>
        <p class="subtitle">Designed for High Availability & Auto Scaling</p>
        
        <div class="server-metrics">
            <div class="metric-row">
                <span class="metric-label">Active Node ID</span>
                <span class="metric-value">{{ hostname }}</span>
            </div>
            
            <div style="margin-top: 20px;">
                <span class="metric-label" style="display: block; margin-bottom: 10px;">Real-Time CPU Load</span>
                <div class="meter-bg">
                    <div id="cpu-percentage-meter" class="meter-fill"></div>
                </div>
                <p id="cpu-text">0.0%</p>
            </div>
        </div>
        
        <div class="controls">
            <button class="btn-primary" onclick="increaseLoad()">Simulate Traffic Spike</button>
            <button class="btn-secondary" onclick="cancelLoad()">Normalize Load</button>
        </div>

        <div class="footer">
            Engineered by <strong>Milan Rai</strong> | Aspiring AWS Cloud Engineer
        </div>
    </div>

    <script>
        function updateCpuUsage() {
            fetch('/cpu_percentage')
                .then(response => response.json())
                .then(data => {
                    const percentage = data.cpu;
                    const meter = document.getElementById('cpu-percentage-meter');
                    meter.style.width = percentage + '%';
                    
                    if(percentage > 80) {
                        meter.style.background = '#ef4444'; // Red
                    } else if(percentage > 50) {
                        meter.style.background = '#eab308'; // Yellow
                    } else {
                        meter.style.background = '#38bdf8'; // Blue
                    }

                    document.getElementById('cpu-text').innerText = percentage.toFixed(1) + '%';
                });
        }

        function increaseLoad() {
            fetch('/increase_load')
                .then(response => response.json())
                .then(data => console.log("Load injected"));
        }

        function cancelLoad() {
            fetch('/cancel_load')
                .then(response => response.json())
                .then(data => console.log("Load normalized"));
        }

        setInterval(updateCpuUsage, 2000);
    </script>
</body>
</html>
    """, hostname=hostname)

@app.route('/cpu_percentage')
def cpu_percentage():
    return jsonify(cpu=psutil.cpu_percent(interval=1))

@app.route('/increase_load')
def increase_load():
    global stress_process
    if not stress_process:
        
        cpu_count = multiprocessing.cpu_count()
        stress_process = subprocess.Popen(['stress', '--cpu', str(cpu_count)])
    return jsonify(status='Load Increased')

@app.route('/cancel_load')
def cancel_load():
    global stress_process
    if stress_process:
        subprocess.run(['pkill', 'stress'])
        stress_process = None
    return jsonify(status='Load Cancelled')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
EOF

# Set proper ownership
sudo chown ec2-user:ec2-user /home/ec2-user/app.py

# Start Flask application in background using nohup as ec2-user
sudo -u ec2-user nohup python3 /home/ec2-user/app.py > /home/ec2-user/app.log 2>&1 &