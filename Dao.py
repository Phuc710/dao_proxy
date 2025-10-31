import requests
import sys
import os
import time
from datetime import datetime

def check_internet_connection():
    """Kiểm tra kết nối internet"""
    try:
        response = requests.get("https://www.google.com/", timeout=5)
        return True
    except requests.ConnectionError:
        print("\n\033[1;31m[!] KHÔNG CÓ KÊT NỐI INTERNET!\033[0m")
        sys.exit(1)

def clear():
    """Clear màn hình"""
    os.system("cls" if os.name == "nt" else "clear")

def print_banner():
    """In banner với màu sắc"""
    banner = """
\033[1;36m

               ADMIN : phucngx
\033[0m"""
    print(banner)

def is_valid_proxy(line):
    """Validate định dạng IP:PORT"""
    if ':' not in line:
        return False
    parts = line.split(':', 1)
    if len(parts) != 2:
        return False
    ip, port = parts
    # Kiểm tra port là số
    if not port.isdigit():
        return False
    # Kiểm tra IP có 4 phần
    ip_parts = ip.split('.')
    if len(ip_parts) != 4:
        return False
    return True

def scrape_proxies():
    """Lấy proxy từ các nguồn"""
    
    # Danh sách nguồn proxy (đã fix thiếu dấu phẩy)
    raw_proxy_sites = [
        "https://api.proxyscrape.com/?request=displayproxies&proxytype=http",
        "https://api.openproxylist.xyz/http.txt",
        "http://worm.rip/http.txt",
        "https://proxy-spider.com/api/proxies.example.txt",
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
        "https://raw.githubusercontent.com/almroot/proxylist/master/list.txt",
        "https://openproxylist.xyz/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/http.txt",
        "http://rootjazz.com/proxies/proxies.txt",
        "https://api.proxyscrape.com/?request=displayproxies&proxytype=https",
        "https://www.proxy-list.download/api/v1/get?type=http",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
        "https://raw.githubusercontent.com/shiftytr/proxy-list/master/proxy.txt",
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
        "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
        "https://raw.githubusercontent.com/opsxcq/proxy-list/master/list.txt",
        # "https://multiproxy.org/txt_all/proxy.txt",  # Commented vì DNS thường lỗi
        "https://proxyspace.pro/https.txt",
        "https://raw.githubusercontent.com/aslisk/proxyhttps/main/https.txt",
        "https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/HTTP.txt",
        "https://raw.githubusercontent.com/hendrikbgr/Free-Proxy-Repo/master/proxy_list.txt",
        "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/http.txt",
        "https://raw.githubusercontent.com/Skiddle-ID/proxylist/refs/heads/main/generated/http_proxies.txt",
        "https://raw.githubusercontent.com/fahimscirex/proxybd/refs/heads/master/proxylist/http.txt",
        "https://raw.githubusercontent.com/yemixzy/proxy-list/refs/heads/main/proxies/http.txt",
        "https://raw.githubusercontent.com/TuanMinPay/live-proxy/refs/heads/master/http.txt",
        "https://raw.githubusercontent.com/TuanMinPay/live-proxy/refs/heads/master/all.txt",
        "https://raw.githubusercontent.com/Vann-Dev/proxy-list/refs/heads/main/proxies/http.txt",
        "https://raw.githubusercontent.com/Vann-Dev/proxy-list/refs/heads/main/proxies/https.txt",
        "https://raw.githubusercontent.com/r00tee/Proxy-List/main/Https.txt",
        "https://github.com/zloi-user/hideip.me/raw/refs/heads/master/http.txt",
        "https://github.com/zloi-user/hideip.me/raw/refs/heads/master/https.txt",
        "https://raw.githubusercontent.com/dpangestuw/Free-Proxy/refs/heads/main/All_proxies.txt",
        "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/refs/heads/master/http.txt",
        "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/refs/heads/master/https.txt",
        "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/refs/heads/main/proxies/http.txt",
        "https://raw.githubusercontent.com/TuanMinPay/live-proxy/refs/heads/master/socks4.txt",
        "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/refs/heads/main/proxies/https.txt",
        "https://raw.githubusercontent.com/yemixzy/proxy-list/refs/heads/main/proxies/unchecked.txt",
        "https://raw.githubusercontent.com/zloi-user/hideip.me/main/http.txt",
        "https://raw.githubusercontent.com/zloi-user/hideip.me/main/https.txt",
        "https://raw.githubusercontent.com/BreakingTechFr/Proxy_Free/main/proxies/http.txt",
        "https://raw.githubusercontent.com/dpangestuw/Free-Proxy/refs/heads/main/http_proxies.txt",
        "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",
        "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/http.txt",
        "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/https.txt",
        "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/http.txt",
        "https://sunny9577.github.io/proxy-scraper/generated/http_proxies.txt",
        "https://raw.githubusercontent.com/proxifly/free-proxy-list/refs/heads/main/proxies/protocols/https/data.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies/http.txt",
        "https://raw.githubusercontent.com/Skiddle-ID/proxylist/refs/heads/main/generated/socks4_proxies.txt",
        "https://raw.githubusercontent.com/yemixzy/proxy-list/refs/heads/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/saisuiu/uiu/main/free.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/https.txt",
        "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
        "https://www.proxy-list.download/api/v1/get?type=https",
        "https://raw.githubusercontent.com/saisuiu/Lionkings-Http-Proxys-Proxies/main/free.txt",
        "https://raw.githubusercontent.com/saisuiu/Lionkings-Http-Proxys-Proxies/main/cnfree.txt",
        "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/http.txt",
        "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies_anonymous/http.txt",
        "https://sunny9577.github.io/proxy-scraper/proxies.txt",  # Fix thiếu dấu phẩy
        "https://vakhov.github.io/fresh-proxy-list/http.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/refs/heads/master/http.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/refs/heads/master/https.txt",
        "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/refs/heads/master/http.txt",
    ]
    
    proxies = set()  # Dùng set để tự động loại trùng
    total_sources = len(raw_proxy_sites)
    
    print(f"\033[1;33m[*] Đang lấy proxy từ {total_sources} nguồn...\033[0m\n")
    
    for idx, site in enumerate(raw_proxy_sites, 1):
        try:
            print(f"\033[1;36m[{idx}/{total_sources}] Đang lấy từ: {site[:60]}...\033[0m", end="")
            response = requests.get(site, timeout=10)
            
            if response.status_code == 200:
                count_before = len(proxies)
                for line in response.text.split('\n'):
                    line = line.strip()
                    if is_valid_proxy(line):
                        # Chỉ lấy IP:PORT, bỏ phần thừa nếu có
                        ip, port = line.split(':', 1)
                        proxies.add(f'{ip}:{port}')
                
                count_after = len(proxies)
                new_proxies = count_after - count_before
                print(f" \033[1;32m✓ (+{new_proxies})\033[0m")
            else:
                print(f" \033[1;31m✗ (HTTP {response.status_code})\033[0m")
                
        except Exception as e:
            print(f" \033[1;31m✗ (Error: {str(e)[:30]}...)\033[0m")
    
    return list(proxies)

def main():
    # Kiểm tra internet
    check_internet_connection()
    
    # Clear và hiện banner
    clear()
    print_banner()
    
    # Hiện thông tin
    now = datetime.now()
    print(f"\033[1;36m           Admin: PHUCNGX \033[1;32m| \033[1;36mThời gian: {now.strftime('%H:%M:%S %d/%m/%Y')}")
    print("\033[1;36m           NOTE: CHỜ ĐỢI LÀ HẠNH PHÚC, HÃY CHỜ THÊM CHÚT NỮA 😇\n\033[0m")
    
    # Bắt đầu scrape
    start_time = time.time()
    proxies = scrape_proxies()
    elapsed = round(time.time() - start_time, 2)
    
    # Thống kê
    print(f"\n\033[1;32m{'='*60}\033[0m")
    print(f"\033[1;33m✅ Tổng proxy thu thập: {len(proxies)}\033[0m")
    print(f"\033[1;33m⏱️  Thời gian: {elapsed}s\033[0m")
    print(f"\033[1;32m{'='*60}\033[0m\n")
    
    # Lưu file
    output_file = "proxy.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        for proxy in sorted(proxies):  # Sort để dễ đọc
            f.write(proxy + '\n')
    
    print(f"\033[1;32m[✓] Đã lưu {len(proxies)} proxy vào file: {output_file}\033[0m")
    
    # Kết thúc
    clear()
    print_banner()
    print("\033[1;36m[*] Hoàn tất! Cảm ơn bạn đã sử dụng! 😊\033[0m\n")
    
    time.sleep(3)

if __name__ == "__main__":
    main()