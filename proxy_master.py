import sys
import requests
import concurrent.futures
import time
import json
from datetime import datetime
from collections import defaultdict
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
                             QLabel, QLineEdit, QComboBox, QSpinBox, QProgressBar,
                             QTextEdit, QTabWidget, QGroupBox, QMessageBox, QFileDialog,
                             QHeaderView, QCheckBox)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QColor, QFont
import threading


class ProxyScrapeThread(QThread):
    """Thread để scrape proxies"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(set)
    
    def __init__(self, sources):
        super().__init__()
        self.sources = sources
        self.proxies = set()
        self.lock = threading.Lock()
        
    def is_valid_proxy(self, line):
        if ':' not in line:
            return False
        parts = line.split(':', 1)
        if len(parts) != 2:
            return False
        ip, port = parts
        if not port.isdigit():
            return False
        ip_parts = ip.split('.')
        if len(ip_parts) != 4:
            return False
        for part in ip_parts:
            if not part.isdigit() or not 0 <= int(part) <= 255:
                return False
        return True
    
    def fetch_source(self, url):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                count = 0
                for line in response.text.split('\n'):
                    line = line.strip()
                    if self.is_valid_proxy(line):
                        with self.lock:
                            self.proxies.add(line)
                        count += 1
                self.progress.emit(f"✓ {url[:60]}... (+{count})")
                return count
        except Exception as e:
            self.progress.emit(f"✗ {url[:60]}... (Error)")
        return 0
    
    def run(self):
        self.progress.emit(f"Starting scrape from {len(self.sources)} sources...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            list(executor.map(self.fetch_source, self.sources))
        self.progress.emit(f"\n✓ Scraped {len(self.proxies)} unique proxies!")
        self.finished.emit(self.proxies)


class ProxyCheckThread(QThread):
    """Thread để check proxies"""
    progress = pyqtSignal(dict)
    status = pyqtSignal(str)
    finished = pyqtSignal(list)
    
    def __init__(self, proxies, timeout, protocol):
        super().__init__()
        self.proxies = list(proxies)
        self.timeout = timeout
        self.protocol = protocol
        self.live_proxies = []
        self.lock = threading.Lock()
        self.checked = 0
        
    def check_proxy(self, proxy):
        try:
            if self.protocol == "SOCKS5":
                proxies_dict = {
                    "http": f"socks5://{proxy}",
                    "https": f"socks5://{proxy}"
                }
            else:
                proxies_dict = {
                    "http": f"http://{proxy}",
                    "https": f"http://{proxy}"
                }
            
            start = time.time()
            response = requests.get(
                "http://ip-api.com/json",
                proxies=proxies_dict,
                timeout=self.timeout,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            ping = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                result = {
                    "proxy": proxy,
                    "host": proxy.split(':')[0],
                    "port": proxy.split(':')[1],
                    "country": data.get("country", "Unknown"),
                    "city": data.get("city", "Unknown"),
                    "isp": data.get("isp", "Unknown"),
                    "ping": ping,
                    "protocol": self.protocol,
                    "status": "LIVE"
                }
                
                with self.lock:
                    self.live_proxies.append(result)
                    self.checked += 1
                
                self.progress.emit(result)
                return result
                
        except Exception as e:
            pass
        
        with self.lock:
            self.checked += 1
        
        self.status.emit(f"Checked: {self.checked}/{len(self.proxies)}")
        return None
    
    def run(self):
        self.status.emit(f"Checking {len(self.proxies)} proxies...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=150) as executor:
            futures = [executor.submit(self.check_proxy, proxy) for proxy in self.proxies]
            concurrent.futures.wait(futures)
        self.finished.emit(self.live_proxies)


class ProxyToolGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.proxies = set()
        self.live_proxies = []
        self.filtered_proxies = []
        self.init_ui()
        self.load_sources()
        
    def init_ui(self):
        self.setWindowTitle("🚀 Ultimate Proxy Scraper & Checker v3.0 - by PHUCNGX")
        self.setGeometry(100, 100, 1400, 800)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
            }
            QWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: 'Segoe UI', Arial;
                font-size: 10pt;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #74c7ec;
            }
            QPushButton:pressed {
                background-color: #89dceb;
            }
            QPushButton:disabled {
                background-color: #45475a;
                color: #6c7086;
            }
            QLineEdit, QSpinBox, QComboBox {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 5px;
                color: #cdd6f4;
            }
            QTableWidget {
                background-color: #313244;
                border: 1px solid #45475a;
                gridline-color: #45475a;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #89b4fa;
                color: #1e1e2e;
            }
            QHeaderView::section {
                background-color: #45475a;
                color: #cdd6f4;
                padding: 5px;
                border: 1px solid #313244;
                font-weight: bold;
            }
            QTextEdit {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 4px;
                color: #cdd6f4;
            }
            QProgressBar {
                border: 1px solid #45475a;
                border-radius: 4px;
                text-align: center;
                background-color: #313244;
            }
            QProgressBar::chunk {
                background-color: #a6e3a1;
                border-radius: 3px;
            }
            QGroupBox {
                border: 2px solid #45475a;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
                color: #89b4fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QTabWidget::pane {
                border: 1px solid #45475a;
                background-color: #1e1e2e;
            }
            QTabBar::tab {
                background-color: #313244;
                color: #cdd6f4;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #89b4fa;
                color: #1e1e2e;
            }
            QLabel {
                color: #cdd6f4;
            }
        """)
        
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # Header
        header = QLabel("🚀 ULTIMATE PROXY SCRAPER & CHECKER v3.0")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 18pt; font-weight: bold; color: #89b4fa; padding: 10px;")
        main_layout.addWidget(header)
        
        # Tabs
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        
        # Tab 1: Scrape & Check
        tab1 = QWidget()
        tab1_layout = QVBoxLayout(tab1)
        
        # Control Panel
        control_group = QGroupBox("⚙️ Control Panel")
        control_layout = QVBoxLayout()
        
        # Row 1: Protocol, Timeout, Threads
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Protocol:"))
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(["HTTP", "HTTPS", "SOCKS5"])
        row1.addWidget(self.protocol_combo)
        
        row1.addWidget(QLabel("Timeout (s):"))
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 30)
        self.timeout_spin.setValue(10)
        row1.addWidget(self.timeout_spin)
        
        row1.addWidget(QLabel("Threads:"))
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(10, 500)
        self.threads_spin.setValue(150)
        row1.addWidget(self.threads_spin)
        
        control_layout.addLayout(row1)
        
        # Row 2: Buttons
        row2 = QHBoxLayout()
        self.scrape_btn = QPushButton("🔍 Scrape Proxies")
        self.scrape_btn.clicked.connect(self.start_scrape)
        row2.addWidget(self.scrape_btn)
        
        self.check_btn = QPushButton("✅ Check Proxies")
        self.check_btn.clicked.connect(self.start_check)
        self.check_btn.setEnabled(False)
        row2.addWidget(self.check_btn)
        
        self.stop_btn = QPushButton("⛔ Stop")
        self.stop_btn.setEnabled(False)
        row2.addWidget(self.stop_btn)
        
        self.clear_btn = QPushButton("🗑️ Clear All")
        self.clear_btn.clicked.connect(self.clear_all)
        row2.addWidget(self.clear_btn)
        
        control_layout.addLayout(row2)
        control_group.setLayout(control_layout)
        tab1_layout.addWidget(control_group)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        tab1_layout.addWidget(self.progress_bar)
        
        # Status Label
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("color: #a6e3a1; font-weight: bold;")
        tab1_layout.addWidget(self.status_label)
        
        # Log Output
        log_group = QGroupBox("📋 Activity Log")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        tab1_layout.addWidget(log_group)
        
        tabs.addTab(tab1, "🔧 Scrape & Check")
        
        # Tab 2: Results
        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)
        
        # Filter Panel
        filter_group = QGroupBox("🔍 Filters")
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Country:"))
        self.country_filter = QLineEdit()
        self.country_filter.setPlaceholderText("e.g. Indonesia, Vietnam...")
        filter_layout.addWidget(self.country_filter)
        
        filter_layout.addWidget(QLabel("Max Ping (ms):"))
        self.ping_filter = QSpinBox()
        self.ping_filter.setRange(0, 10000)
        self.ping_filter.setValue(5000)
        filter_layout.addWidget(self.ping_filter)
        
        self.apply_filter_btn = QPushButton("Apply Filter")
        self.apply_filter_btn.clicked.connect(self.apply_filters)
        filter_layout.addWidget(self.apply_filter_btn)
        
        self.reset_filter_btn = QPushButton("Reset")
        self.reset_filter_btn.clicked.connect(self.reset_filters)
        filter_layout.addWidget(self.reset_filter_btn)
        
        filter_group.setLayout(filter_layout)
        tab2_layout.addWidget(filter_group)
        
        # Export Panel
        export_group = QGroupBox("💾 Export Options")
        export_layout = QHBoxLayout()
        
        self.export_txt_btn = QPushButton("📄 Export TXT")
        self.export_txt_btn.clicked.connect(lambda: self.export_proxies("txt"))
        export_layout.addWidget(self.export_txt_btn)
        
        self.export_json_btn = QPushButton("📋 Export JSON")
        self.export_json_btn.clicked.connect(lambda: self.export_proxies("json"))
        export_layout.addWidget(self.export_json_btn)
        
        self.export_csv_btn = QPushButton("📊 Export CSV")
        self.export_csv_btn.clicked.connect(lambda: self.export_proxies("csv"))
        export_layout.addWidget(self.export_csv_btn)
        
        export_group.setLayout(export_layout)
        tab2_layout.addWidget(export_group)
        
        # Results Table
        results_group = QGroupBox("📊 Live Proxies")
        results_layout = QVBoxLayout()
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels([
            "Status", "Host", "Port", "Country", "City", "ISP", "Ping (ms)", "Protocol"
        ])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setAlternatingRowColors(True)
        
        # Auto-resize columns
        header = self.results_table.horizontalHeader()
        for i in range(8):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        results_layout.addWidget(self.results_table)
        results_group.setLayout(results_layout)
        tab2_layout.addWidget(results_group)
        
        # Stats
        self.stats_label = QLabel("Total: 0 | Live: 0 | Dead: 0 | Success Rate: 0%")
        self.stats_label.setStyleSheet("font-weight: bold; color: #f9e2af; font-size: 11pt;")
        self.stats_label.setAlignment(Qt.AlignCenter)
        tab2_layout.addWidget(self.stats_label)
        
        tabs.addTab(tab2, "📊 Results")
        
        # Footer
        footer = QLabel("Admin: PHUCNGX | Tool v3.0 | " + datetime.now().strftime("%d/%m/%Y %H:%M"))
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #6c7086; font-size: 9pt; padding: 5px;")
        main_layout.addWidget(footer)
        
    def load_sources(self):
        """Load proxy sources"""
        self.sources = [
            "https://api.proxyscrape.com/?request=displayproxies&proxytype=http",
            "https://api.openproxylist.xyz/http.txt",
            "http://worm.rip/http.txt",
            "https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/http.txt",
            "https://proxyspace.pro/http.txt",
            "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-https.txt",
            "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
            "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
            "https://raw.githubusercontent.com/mmpx12/proxy-list/master/https.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/https.txt",
            "https://openproxylist.xyz/http.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/http.txt",
            "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
            "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
            "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
            "https://proxyspace.pro/https.txt",
            "https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/HTTP.txt",
            "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/http.txt",
        ]
    
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
    def start_scrape(self):
        """Start scraping proxies"""
        self.log("🔍 Starting proxy scraping...")
        self.scrape_btn.setEnabled(False)
        self.check_btn.setEnabled(False)
        self.status_label.setText("Status: Scraping proxies...")
        self.status_label.setStyleSheet("color: #f9e2af; font-weight: bold;")
        
        self.scrape_thread = ProxyScrapeThread(self.sources)
        self.scrape_thread.progress.connect(self.log)
        self.scrape_thread.finished.connect(self.on_scrape_finished)
        self.scrape_thread.start()
        
    def on_scrape_finished(self, proxies):
        """Handle scrape completion"""
        self.proxies = proxies
        self.log(f"✅ Scraping completed! Found {len(proxies)} proxies")
        self.status_label.setText(f"Status: Ready - {len(proxies)} proxies scraped")
        self.status_label.setStyleSheet("color: #a6e3a1; font-weight: bold;")
        self.scrape_btn.setEnabled(True)
        self.check_btn.setEnabled(True)
        
    def start_check(self):
        """Start checking proxies"""
        if not self.proxies:
            QMessageBox.warning(self, "Warning", "No proxies to check! Please scrape first.")
            return
            
        self.log(f"✅ Starting proxy check for {len(self.proxies)} proxies...")
        self.check_btn.setEnabled(False)
        self.scrape_btn.setEnabled(False)
        self.status_label.setText("Status: Checking proxies...")
        self.status_label.setStyleSheet("color: #f9e2af; font-weight: bold;")
        self.progress_bar.setMaximum(len(self.proxies))
        self.progress_bar.setValue(0)
        
        protocol = self.protocol_combo.currentText()
        timeout = self.timeout_spin.value()
        
        self.live_proxies = []
        self.results_table.setRowCount(0)
        
        self.check_thread = ProxyCheckThread(self.proxies, timeout, protocol)
        self.check_thread.progress.connect(self.on_proxy_checked)
        self.check_thread.status.connect(self.log)
        self.check_thread.finished.connect(self.on_check_finished)
        self.check_thread.start()
        
    def on_proxy_checked(self, result):
        """Update table when proxy is checked"""
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        # Status with color
        status_item = QTableWidgetItem("✓ LIVE")
        status_item.setForeground(QColor("#a6e3a1"))
        status_item.setFont(QFont("Arial", 10, QFont.Bold))
        self.results_table.setItem(row, 0, status_item)
        
        self.results_table.setItem(row, 1, QTableWidgetItem(result["host"]))
        self.results_table.setItem(row, 2, QTableWidgetItem(result["port"]))
        self.results_table.setItem(row, 3, QTableWidgetItem(result["country"]))
        self.results_table.setItem(row, 4, QTableWidgetItem(result["city"]))
        self.results_table.setItem(row, 5, QTableWidgetItem(result["isp"]))
        
        # Ping with color coding
        ping_item = QTableWidgetItem(str(result["ping"]))
        if result["ping"] < 300:
            ping_item.setForeground(QColor("#a6e3a1"))  # Green
        elif result["ping"] < 1000:
            ping_item.setForeground(QColor("#f9e2af"))  # Yellow
        else:
            ping_item.setForeground(QColor("#f38ba8"))  # Red
        self.results_table.setItem(row, 6, ping_item)
        
        self.results_table.setItem(row, 7, QTableWidgetItem(result["protocol"]))
        
        self.progress_bar.setValue(self.progress_bar.value() + 1)
        
    def on_check_finished(self, live_proxies):
        """Handle check completion"""
        self.live_proxies = live_proxies
        self.filtered_proxies = live_proxies.copy()
        
        total = len(self.proxies)
        live = len(live_proxies)
        dead = total - live
        rate = round(live / total * 100, 2) if total > 0 else 0
        
        self.stats_label.setText(f"Total: {total} | Live: {live} | Dead: {dead} | Success Rate: {rate}%")
        self.log(f"✅ Check completed! Live: {live}/{total} ({rate}%)")
        self.status_label.setText(f"Status: Completed - {live} live proxies found")
        self.status_label.setStyleSheet("color: #a6e3a1; font-weight: bold;")
        
        self.check_btn.setEnabled(True)
        self.scrape_btn.setEnabled(True)
        
        QMessageBox.information(self, "Success", 
                               f"Check completed!\n\nLive: {live}\nDead: {dead}\nSuccess Rate: {rate}%")
        
    def apply_filters(self):
        """Apply filters to results"""
        country = self.country_filter.text().strip().lower()
        max_ping = self.ping_filter.value()
        
        self.filtered_proxies = [
            p for p in self.live_proxies
            if (not country or country in p["country"].lower()) and p["ping"] <= max_ping
        ]
        
        self.results_table.setRowCount(0)
        for result in self.filtered_proxies:
            self.on_proxy_checked(result)
            
        self.log(f"🔍 Filter applied: {len(self.filtered_proxies)} proxies match criteria")
        
    def reset_filters(self):
        """Reset filters"""
        self.country_filter.clear()
        self.ping_filter.setValue(5000)
        self.filtered_proxies = self.live_proxies.copy()
        
        self.results_table.setRowCount(0)
        for result in self.live_proxies:
            self.on_proxy_checked(result)
            
        self.log("🔄 Filters reset")
        
    def export_proxies(self, format_type):
        """Export proxies to file"""
        if not self.filtered_proxies:
            QMessageBox.warning(self, "Warning", "No proxies to export!")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == "txt":
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save File", f"live_proxies_{timestamp}.txt", "Text Files (*.txt)"
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    for p in sorted(self.filtered_proxies, key=lambda x: x["ping"]):
                        f.write(f"{p['proxy']} | {p['country']} | {p['ping']}ms | {p['protocol']}\n")
                self.log(f"💾 Exported {len(self.filtered_proxies)} proxies to {filename}")
                QMessageBox.information(self, "Success", f"Exported to {filename}")
                
        elif format_type == "json":
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save File", f"live_proxies_{timestamp}.json", "JSON Files (*.json)"
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.filtered_proxies, f, indent=2)
                self.log(f"💾 Exported {len(self.filtered_proxies)} proxies to {filename}")
                QMessageBox.information(self, "Success", f"Exported to {filename}")
                
        elif format_type == "csv":
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save File", f"live_proxies_{timestamp}.csv", "CSV Files (*.csv)"
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("Host,Port,Country,City,ISP,Ping,Protocol\n")
                    for p in sorted(self.filtered_proxies, key=lambda x: x["ping"]):
                        f.write(f"{p['host']},{p['port']},{p['country']},{p['city']},{p['isp']},{p['ping']},{p['protocol']}\n")
                self.log(f"💾 Exported {len(self.filtered_proxies)} proxies to {filename}")
                QMessageBox.information(self, "Success", f"Exported to {filename}")
                
    def clear_all(self):
        """Clear all data"""
        reply = QMessageBox.question(
            self, "Confirm", "Clear all data?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.proxies = set()
            self.live_proxies = []
            self.filtered_proxies = []
            self.results_table.setRowCount(0)
            self.log_text.clear()
            self.progress_bar.setValue(0)
            self.stats_label.setText("Total: 0 | Live: 0 | Dead: 0 | Success Rate: 0%")
            self.status_label.setText("Status: Ready")
            self.log("🗑️ All data cleared")


def main():
    app = QApplication(sys.argv)
    window = ProxyToolGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()