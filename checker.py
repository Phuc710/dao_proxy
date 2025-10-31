import requests
import concurrent.futures
import time
import argparse
import os
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
import threading

console = Console()

# Stats
stats = {
    "total": 0,
    "checked": 0,
    "live": 0,
    "die": 0,
    "start_time": time.time()
}
lock = threading.Lock()

# Results storage
live_proxies = []

def update_stat(key):
    """Update statistics thread-safe"""
    with lock:
        stats[key] += 1
        stats["checked"] += 1

def get_proxy_info(proxy, timeout=10):
    """Check proxy and get detailed information"""
    try:
        proxies = {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}"
        }
        
        start_time = time.time()
        response = requests.get(
            "http://ip-api.com/json",
            proxies=proxies,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        delay = round((time.time() - start_time) * 1000)
        
        if response.status_code == 200:
            data = response.json()
            
            # Determine protocol
            port = proxy.split(":")[-1]
            if port in ["1080", "1081"]:
                protocol = "SOCKS5"
            elif port in ["1082", "1083", "1085"]:
                protocol = "SOCKS4"
            elif port in ["443", "8443"]:
                protocol = "HTTPS"
            else:
                protocol = "HTTP"
            
            result = {
                "proxy": proxy,
                "ip": proxy.split(":")[0],
                "port": port,
                "ipv": "IPV4",  # Default, could be enhanced
                "protocol": protocol,
                "country": data.get("country", "Unknown"),
                "city": data.get("city", "Unknown"),
                "isp": data.get("isp", "Unknown")[:20] + "...",
                "org": data.get("org", "Unknown")[:15] + "...",
                "asn": data.get("as", "Unknown")[:15] + "...",
                "anonymity": "High" if data.get("proxy") == "true" else "Elite",
                "delay": f"{delay}ms",
                "working": "YES",
                "status": "LIVE"
            }
            
            update_stat("live")
            with lock:
                live_proxies.append(result)
            
            return result
        else:
            update_stat("die")
            return None
            
    except Exception as e:
        update_stat("die")
        return None

def create_results_table():
    """Create rich table with results"""
    table = Table(show_header=True, header_style="bold cyan", border_style="blue")
    
    # Add columns matching the image
    table.add_column("IP", style="white", width=15)
    table.add_column("Host", style="white", width=15)
    table.add_column("Port", style="cyan", width=6)
    table.add_column("IPV", style="magenta", width=6)
    table.add_column("Proto", style="green", width=7)
    table.add_column("Country", style="yellow", width=8)
    table.add_column("City", style="white", width=12)
    table.add_column("ISP", style="cyan", width=20)
    table.add_column("Org", style="white", width=15)
    table.add_column("ASN", style="white", width=15)
    table.add_column("Anony", style="green", width=10)
    table.add_column("Delay", style="yellow", width=8)
    table.add_column("Work", style="green", width=6)
    
    # Add rows (last 20 results)
    for proxy in live_proxies[-20:]:
        # Get country flag emoji
        country_flag = get_flag(proxy["country"])
        
        table.add_row(
            proxy["ip"],
            proxy["ip"],
            proxy["port"],
            proxy["ipv"],
            proxy["protocol"],
            f"{country_flag} {proxy['country'][:6]}",
            proxy["city"][:12],
            proxy["isp"],
            proxy["org"],
            proxy["asn"],
            proxy["anonymity"],
            proxy["delay"],
            "[green]YES[/green]"
        )
    
    return table

def get_flag(country):
    """Get flag emoji for country"""
    flags = {
        "Vietnam": "🇻🇳", "Indonesia": "🇮🇩", "India": "🇮🇳",
        "Ukraine": "🇺🇦", "United States": "🇺🇸", "Philippines": "🇵🇭",
        "Bangladesh": "🇧🇩", "Venezuela": "🇻🇪", "Dominican Republic": "🇩🇴",
        "Unknown": "🏴"
    }
    return flags.get(country, "🌍")

def create_stats_panel():
    """Create statistics panel"""
    elapsed = time.time() - stats["start_time"]
    cpm = int(stats["checked"] / elapsed * 60) if elapsed > 0 else 0
    
    stats_text = f"""
[cyan]Total:[/cyan] [white]{stats['total']}[/white]  |  [cyan]Checked:[/cyan] [yellow]{stats['checked']}/{stats['total']}[/yellow]
[green]✓ Live:[/green] [green]{stats['live']}[/green]  |  [red]✗ Die:[/red] [red]{stats['die']}[/red]
[cyan]Speed:[/cyan] [yellow]{cpm} CPM[/yellow]  |  [cyan]Time:[/cyan] [white]{int(elapsed)}s[/white]
    """
    return Panel(stats_text, title="[bold cyan]Statistics[/bold cyan]", border_style="cyan")

def load_proxies(file_path):
    """Load proxies from file"""
    proxies = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and ":" in line:
                    parts = line.split(":")
                    if len(parts) >= 2 and parts[1].isdigit():
                        proxies.append(line)
        return proxies
    except Exception as e:
        console.print(f"[red][!] Error loading file: {e}[/red]")
        return []

def save_results(live_proxies):
    """Save live proxies to files"""
    # Save all live proxies
    with open("live_proxies.txt", "w", encoding="utf-8") as f:
        for proxy in live_proxies:
            f.write(f"{proxy['proxy']}\n")
    
    # Save by protocol
    protocols = {}
    for proxy in live_proxies:
        proto = proxy["protocol"].lower()
        if proto not in protocols:
            protocols[proto] = []
        protocols[proto].append(proxy["proxy"])
    
    for proto, proxies in protocols.items():
        with open(f"live_{proto}.txt", "w", encoding="utf-8") as f:
            for proxy in proxies:
                f.write(f"{proxy}\n")
    
    # Save by country
    countries = {}
    for proxy in live_proxies:
        country = proxy["country"]
        if country not in countries:
            countries[country] = []
        countries[country].append(proxy["proxy"])
    
    for country, proxies in countries.items():
        safe_country = country.replace(" ", "_")
        with open(f"live_{safe_country}.txt", "w", encoding="utf-8") as f:
            for proxy in proxies:
                f.write(f"{proxy}\n")

def main():
    os.system("cls" if os.name == "nt" else "clear")
    
    # Banner
    banner = """
[cyan]╔══════════════════════════════════════════════════════════╗
║                                                          ║
║           [bold magenta]ADVANCED PROXY CHECKER v2.0[/bold magenta]              ║
║                                                          ║
║     [yellow]Developer:[/yellow] [white]@thuannodejs[/white]                           ║
║     [yellow]Channel:[/yellow] [white]https://t.me/humanpcc[/white]                 ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝[/cyan]
    """
    console.print(banner)
    
    # Arguments
    parser = argparse.ArgumentParser(description="Advanced Proxy Checker")
    parser.add_argument("--file", "-f", required=True, help="Input proxy file")
    parser.add_argument("--threads", "-t", type=int, default=100, help="Threads (default: 100)")
    parser.add_argument("--timeout", type=int, default=10, help="Timeout (default: 10s)")
    args = parser.parse_args()
    
    # Load proxies
    console.print(f"[cyan][*] Loading proxies from {args.file}...[/cyan]")
    proxy_list = load_proxies(args.file)
    
    if not proxy_list:
        console.print("[red][!] No valid proxies found![/red]")
        return
    
    stats["total"] = len(proxy_list)
    console.print(f"[green][✓] Loaded {len(proxy_list)} proxies[/green]\n")
    
    # Start checking
    console.print(f"[cyan][*] Starting check with {args.threads} threads...[/cyan]\n")
    
    with Live(console=console, refresh_per_second=2) as live:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
            futures = [executor.submit(get_proxy_info, proxy, args.timeout) for proxy in proxy_list]
            
            for future in concurrent.futures.as_completed(futures):
                # Update display
                table = create_results_table()
                stats_panel = create_stats_panel()
                
                from rich.layout import Layout
                layout = Layout()
                layout.split_column(
                    Layout(stats_panel, size=5),
                    Layout(table)
                )
                live.update(layout)
    
    # Final results
    console.print("\n" + "="*60)
    console.print(f"[green]✅ DONE![/green]")
    console.print(f"[cyan]Total Checked:[/cyan] [yellow]{stats['checked']}[/yellow]")
    console.print(f"[green]✓ Live:[/green] [green]{stats['live']}[/green]")
    console.print(f"[red]✗ Die:[/red] [red]{stats['die']}[/red]")
    console.print(f"[cyan]Success Rate:[/cyan] [yellow]{round(stats['live']/stats['total']*100, 2)}%[/yellow]")
    console.print("="*60 + "\n")
    
    # Save results
    if live_proxies:
        console.print("[cyan][*] Saving results...[/cyan]")
        save_results(live_proxies)
        console.print("[green][✓] Results saved:[/green]")
        console.print("  • live_proxies.txt (all)")
        console.print("  • live_http.txt, live_https.txt, live_socks4.txt, live_socks5.txt")
        console.print("  • live_[Country].txt")
    
    console.print("\n[cyan]Thank you for using! 🚀[/cyan]")

if __name__ == "__main__":
    main()