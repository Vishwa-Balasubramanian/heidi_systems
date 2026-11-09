import hashlib
import ipaddress
import json
import re
import socket
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser
import requests
from bs4 import BeautifulSoup

AGENT = 'HeidiResearchBot/1.0'


def public_url(url):
    p = urlsplit(url)
    if p.scheme not in ('http', 'https') or not p.hostname or p.username or p.port not in (None, 80, 443):
        raise ValueError('Unsupported public URL')
    for result in socket.getaddrinfo(p.hostname, p.port or 443):
        if not ipaddress.ip_address(result[4][0]).is_global:
            raise ValueError('Non-public address blocked')


def text_and_links(html, url):
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style', 'noscript', 'svg']):
        tag.decompose()
    links = []
    for a in soup.find_all('a', href=True):
        target = urljoin(url, a['href']).split('#')[0]
        if urlsplit(target).hostname == urlsplit(url).hostname and re.search(
                r'leistung|verwaltung|service|unternehmen|ueber|über|impressum|kontakt',
                a.get_text(' ', strip=True) + ' ' + target, re.I):
            if target not in links and target != url:
                links.append(target)
    return re.sub(r'\s+', ' ', soup.get_text(' ', strip=True)), links


class Fetcher:
    _host_lock = threading.Lock()
    _host_next = {}
    def __init__(self, config, mode):
        self.config, self.mode = config, mode
        self.root = Path(config['cache'])
        self.root.mkdir(parents=True, exist_ok=True)
        self.robots = {}
        self.last = {}

    def request(self, url, robots=False):
        for _ in range(6):
            public_url(url)
            host = urlsplit(url).netloc
            delay = self.config['request_delay']
            if host in self.robots:
                delay = max(delay, self.robots[host].crawl_delay(AGENT) or 0)
            # Reserve request slots across all concurrent company fetchers.
            with self._host_lock:
                slot = max(time.monotonic(), self._host_next.get(host, 0))
                self._host_next[host] = slot + delay
            time.sleep(max(0, slot-time.monotonic()))
            r = requests.get(url, headers={'User-Agent': AGENT}, timeout=self.config['request_timeout'],
                             allow_redirects=False)
            if r.is_redirect:
                url = urljoin(url, r.headers['Location'])
                if not robots:
                    self.allowed(url)
                continue
            return r
        raise ValueError('Too many redirects')

    def allowed(self, url):
        p = urlsplit(url)
        if p.netloc not in self.robots:
            robots_url = f'{p.scheme}://{p.netloc}/robots.txt'
            r = self.request(robots_url, robots=True)
            rp = RobotFileParser(robots_url)
            if r.status_code in (404, 410):
                rp.parse([])
            else:
                r.raise_for_status()
                if '<html' in r.text[:500].lower():
                    raise ValueError('Cannot establish robots policy')
                rp.parse(r.text.splitlines())
            self.robots[p.netloc] = rp
        if not self.robots[p.netloc].can_fetch(AGENT, url):
            raise ValueError('robots.txt disallows URL')

    def fetch(self, url):
        key = hashlib.sha256(url.encode()).hexdigest()
        pointer = self.root / (key + '.json')
        if self.mode == 'snapshot':
            if not pointer.exists():
                raise FileNotFoundError('No saved source snapshot')
            return json.loads(pointer.read_text(encoding='utf-8'))
        self.allowed(url)
        r = self.request(url)
        r.raise_for_status()
        if 'html' not in r.headers.get('Content-Type', ''):
            raise ValueError('Non-HTML response')
        if len(r.content) > 4_000_000:
            raise ValueError('Page exceeds 4 MB')
        # requests defaults to Latin-1 on some sites; honor HTML/meta detection.
        html = BeautifulSoup(r.content, 'html.parser')
        text, links = text_and_links(str(html), r.url)
        if len(text) < 100 or re.search(r'just a moment|verify you are human|checking your browser', text, re.I):
            raise ValueError('Empty page or access challenge')
        digest = hashlib.sha256(r.content).hexdigest()
        result = dict(source_url=r.url, requested_url=url, retrieved_at=datetime.now(timezone.utc).isoformat(),
                      content_hash=digest, text=text, links=links)
        (self.root / (digest + '.html')).write_bytes(r.content)
        serialized = json.dumps(result, ensure_ascii=False)
        (self.root / (digest + '.json')).write_text(serialized, encoding='utf-8')
        pointer.write_text(serialized, encoding='utf-8')
        return result
