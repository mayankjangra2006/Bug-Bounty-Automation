# commands.py
# Centralized commands mapping for Recon to Master GUI (upgraded)
# Keep commands exactly as provided in the checklist. Use placeholders like {target}, {cidr}, {asn}, etc.

COMMANDS = {
    "Recon - Subdomain Enumeration": {
        "subfinder (all recursive)": "subfinder -d {target} -all -recursive -o subfinder.txt",
        "assetfinder": "assetfinder --subs-only {target} > assetfinder.txt",
        "findomain": "findomain -t {target} | tee findomain.txt",
        "amass passive": "amass enum -passive -d {target} | cut -d']' -f 2 | awk '{print $1}' | sort -u > amass.txt",
        "amass active": "amass enum -active -d {target} | cut -d']' -f 2 | awk '{print $1}' | sort -u > amass.txt",
    },

    "Recon - Public Sources": {
        "crt.sh (curl + jq)": "curl -s https://crt.sh\\?q\\={target}\\&output\\=json | jq -r '.[].name_value' | grep -Po '(\\\\w+\\\\.\\\\w+\\\\.\\\\w+)$' >crtsh.txt",
        "wayback (archive)": "curl -s \\\"http://web.archive.org/cdx/search/cdx?url=*.{target}/*&output=text&fl=original&collapse=urlkey\\\" |sort| sed -e 's_https*://__' -e \\\"s/\\\\/.*//\\\" -e 's/:.*//' -e 's/^www\\.//' | sort -u > wayback.txt",
        "virustotal domain siblings": "curl -s \\\"https://www.virustotal.com/vtapi/v2/domain/report?apikey=[api-key]&domain={target}\\\" | jq -r '.domain_siblings[]' >virustotal.txt",
    },

    "Recon - GitHub & Merging": {
        "github-subdomains": "github-subdomains -d {target} -t [github_token]",
        "merge all txts": "cat *.txt | sort -u > final.txt",
    },

    "Recon - Permutation & DNS": {
        "subfinder | alterx | dnsx": "subfinder -d {target} | alterx | dnsx",
        "alterx enrich": "echo {target} | alterx -enrich | dnsx",
        "alterx permutation": "echo {target} | alterx -pp word=/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt | dnsx",
    },

    "Bruteforce": {
        "ffuf subdomain brute": "ffuf -u \\\"https://FUZZ.{target}\\\" -w wordlist.txt -mc 200,301,302",
    },

    "ASN & IP Discovery": {
        "asnmap": "asnmap -d {target} | dnsx -silent -resp-only",
    },

    "Amass Intel": {
        "amass intel org": "amass intel -org \\\"{target}\\\"",
        "amass intel active cidr": "amass intel -active -cidr {cidr}",
        "amass intel asn": "amass intel -active -asn {asn}",
    },

    "IP Harvesting": {
        "vt ip addresses": "curl -s \\\"https://www.virustotal.com/vtapi/v2/domain/report?domain={target}&apikey=[api-key]\\\" | jq -r '.. | .ip_address? // empty' | grep -Eo '([0-9]{1,3}\\\\.){3}[0-9]{1,3}'",
        "otx ip addresses": "curl -s \\\"https://otx.alienvault.com/api/v1/indicators/hostname/{target}/url_list?limit=500&page=1\\\" | jq -r '.url_list[]?.result?.urlworker?.ip // empty' | grep -Eo '([0-9]{1,3}\\\\.){3}[0-9]{1,3}'",
        "urlscan ips": "curl -s \\\"https://urlscan.io/api/v1/search/?q=domain:{target}&size=10000\\\" | jq -r '.results[]?.page?.ip // empty' | grep -Eo '([0-9]{1,3}\\\\.){3}[0-9]{1,3}'",
        "shodan ssl search": "shodan search Ssl.cert.subject.CN:\\\"{target}\\\" 200 --fields ip_str | httpx-toolkit -sc -title -server -td",
    },

    "Live Hosts": {
        "httpx-toolkit probe": "cat subdomain.txt | httpx-toolkit -ports 80,443,8080,8000,8888 -threads 200 > subdomains_alive.txt",
    },

    "Visual Recon": {
        "aquatone basic": "cat hosts.txt | aquatone",
        "aquatone ports": "cat hosts.txt | aquatone -ports 80,443,8000,8080,8443",
    },

    "URL Collection": {
        "katana crawl": "katana -u livesubdomains.txt -d 2 -o urls.txt",
        "hakrawler from urls": "cat urls.txt | hakrawler -u > urls3.txt",
        "gau passive": "cat livesubdomains.txt | gau | sort -u > urls2.txt",
        "urlfinder": "urlfinder -d {target} | sort -u > urls3.txt",
    },

    "GF & Patterns": {
        "gf sqli": "cat allurls.txt | gf sqli",
    },

    "Nuclei Scanning": {
        "nuclei single": "nuclei -u https://{target} -bs 50 -c 30",
        "nuclei batch": "nuclei -l live_domains.txt -bs 50 -c 30",
    },

    "Sensitive Files": {
        "find sensitive ext": "cat allurls.txt | grep -E '\\\\.(xls|xml|xlsx|json|pdf|sql|doc|docx|pptx|txt|zip|tar\\\\.gz|tgz|bak|7z|rar|log|cache|secret|db|backup|yml|gz|config|csv|yaml|md|md5)$'",
    },

    "Params & Arjun": {
        "arjun passive": "arjun -u https://{target}/endpoint -oT arjun_output.txt -t 10 --rate-limit 10 --passive -m GET,POST --headers \\\"User-Agent: Mozilla/5.0\\\"",
    },

    "Brute & Dir": {
        "dirsearch deep": "dirsearch -u https://{target} --full-url --deep-recursive -r",
        "ffuf dirsearch": "ffuf -w seclists/Discovery/Web-Content/directory-list-2.3-big.txt -u https://{target}/FUZZ -fc 400,401,402,403,404,429,500,501,502,503 -recursion -recursion-depth 2 -e .html,.php,.txt,.pdf,.js,.css,.zip,.bak,.old,.log,.json,.xml,.config,.env -ac -c -H \\\"User-Agent: Mozilla/5.0\\\" -r -t 60 -o results.json",
    },

    "JS Recon": {
        "katana js": "echo {target} | katana -d 3 | grep -E \\\"\\\\.js$\\\" | nuclei -t /home/coffinxp/nuclei-templates/http/exposures/ -c 30",
        "grep secrets js": "cat jsfiles.txt | grep -r -E \\\"aws_access_key|aws_secret_key|api key|passwd|pwd|heroku|slack|firebase|swagger|aws_secret_key|aws key|password|ftp password|jdbc|db|sql|secret jet|config|admin|pwd|json|gcp|htaccess|.env|ssh key|.git|access key|secret token|oauth_token|oauth_token_secret\\\"",
    },

    "Content-Type Filtering": {
        "html filter": "echo {target} | gau | grep -Eo '(\\\\/[^\\\\/]+)\\\\.(php|asp|aspx|jsp|jsf|cfm|pl|perl|cgi|htm|html)$' | httpx -status-code -mc 200 -content-type | grep -E 'text/html|application/xhtml+xml'",
        "js filter": "echo {target} | gau | grep '\\\\.js$' | httpx -status-code -mc 200 -content-type | grep 'application/javascript'",
    },

    "WordPress": {
        "wpscan full": "wpscan --url https://{target} --disable-tls-checks --api-token <here> -e at -e ap -e u --enumerate ap --plugins-detection aggressive --force",
    },

    "Network Recon": {
        "naabu": "naabu -list ip.txt -c 50 -nmap-cli 'nmap -sV -SC' -o naabu-full.txt",
        "nmap full": "nmap -p- --min-rate 1000 -T4 -A {target} -oA fullscan",
        "masscan": "masscan -p0-65535 {target} --rate 100000 -oG masscan-results.txt",
    },

    "Vuln Discovery": {
        "sqli tech detect": "subfinder -dL subdomains.txt -all -silent | httpx-toolkit -td -sc -silent | grep -Ei 'asp|php|jsp|jspx|aspx'",
        "sqli endpoints": "echo http://{target} | gau | uro | grep -E \\\".php|.asp|.aspx|.jspx|.jsp\\\" | grep -E '\\\\?[^=]+=.+$'",
    },

    "XSS": {
        "quick xss pipe": "echo \\\"{target}\\\" | gau | gf xss | uro | httpx -silent | Gxss -p Rxss | dalfox",
        "ffuf xss request": "ffuf -request xss -request-proto https -w /root/wordlists/xss-payloads.txt -c -mr \\\"<script>alert('XSS')</script>\\\"",
    },

    "LFI": {
        "nuclei lfi": "nuclei -l subs.txt -t /root/nuclei-templates/http/vulnerabilities/generic/generic-linux-lfi.yaml -c 30",
        "ffuf lfi fuzz": "echo \\\"https://{target}/\\\" | gau | gf lfi | uro | sed 's/=.*//=' | qsreplace \\\"FUZZ\\\" | xargs -I{} ffuf -u {} -w payloads/lfi.txt -c -mr \\\"root:(x|\\\\*|\\\\$[^:]*):0:0:\\\" -v",
    },

    "CORS": {
        "manual cors check": "curl -H \\\"Origin: http://example.com\\\" -I https://{target}/wp-json/",
        "cors headers grep": "curl -H \\\"Origin: http://example.com\\\" -I https://{target}/wp-json/ | grep -i -e \\\"access-control-allow-origin\\\" -e \\\"access-control-allow-methods\\\" -e \\\"access-control-allow-credentials\\\"",
        "nuclei cors": "cat example.coms.txt | httpx -silent | nuclei -t nuclei-templates/vulnerabilities/cors/ -o cors_results.txt",
    },

    "Subdomain Takeover": {
        "subzy": "subzy run --targets subdomains.txt --concurrency 100 --hide_fails --verify_ssl",
    },

    "Git Disclosure": {
        "git exposure probe": "cat domains.txt | grep \\\"SUCCESS\\\" | gf urls | httpx-toolkit -sc -server -cl -path \\\"/.git/\\\" -mc 200 -location -ms \\\"Index of\\\" -probe",
    },

    "SSRF": {
        "ssrf param grep": "cat urls.txt | grep -E 'url=|uri=|redirect=|next=|data=|path=|dest=|proxy=|file=|img=|out=|continue=' | sort -u",
        "ssrf nuclei": "cat urls.txt | nuclei -t nuclei-templates/vulnerabilities/ssrf/",
        "ssrf local": "curl \\\"https://{target}/page?url=http://127.0.0.1:80/\\\"",
    },

    "Open Redirect": {
        "find redirect params": "cat final.txt | grep -Pi \\\"returnUrl=|continue=|dest=|destination=|forward=|go=|goto=|login\\\\?to=|login_url=|logout=|next=|next_page=|out=|g=|redir=|redirect_to=|redirect_uri=|redirect_url=|return=|returnTo=|return_path=|return_to=|return_url=|rurl=|site=|target=|to=|uri=|url=|qurl=|rit_url=|jump=|jump_url=|originUrl=|origin=|Url=|desturl=|u=|Redirect=|location=|ReturnUrl=|redirect_url=|redirect_to=|forward_to=|forward_url=|destination_url=|jump_to=|go_to=|goto_url=|target_url=|redirect_link=\\\" | tee redirect_params.txt",
        "qsreplace evil": "cat redirect_params.txt | qsreplace \\\"https://evil.com\\\" | httpx-toolkit -silent -fr -mr \\\"evil.com\\\"",
    },

    "Final Notes": {
        "about": "echo \\\"This GUI was generated from the provided reconnaissance checklist. Always ensure you have authorization before testing targets.\\\"",
    }
}
