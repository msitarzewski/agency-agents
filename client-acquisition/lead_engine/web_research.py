"""Public-web evidence collection for local client research."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from html.parser import HTMLParser
import re
from typing import List, Optional
from urllib.parse import parse_qs, quote_plus, unquote, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from .search_provider import ProviderResult, search_api

USER_AGENT = "ClientAcquisitionOS/0.3 (+public-research; local operator tool)"
SEARCH_ENDPOINTS = (
    ("bing_rss", "https://www.bing.com/search?format=rss&q="),
    ("duckduckgo_html", "https://html.duckduckgo.com/html/?q="),
    ("duckduckgo_lite", "https://lite.duckduckgo.com/lite/?q="),
)

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str = ""
    provider: str = "unknown"

@dataclass
class EvidenceItem:
    claim_context: str
    source_url: str
    source_title: str
    snippet: str
    source_type: str = "public_web"

class _SearchParser(HTMLParser):
    RESULT_LINK_CLASSES = {"result__a", "result-link"}
    SNIPPET_CLASSES = {"result__snippet", "result-snippet"}
    def __init__(self) -> None:
        super().__init__(); self.results=[]; self._href=None; self._title_parts=[]; self._snippet_parts=[]; self._in_title=False; self._in_snippet=False; self._snippet_target=None
    def handle_starttag(self, tag, attrs):
        a=dict(attrs); classes=set((a.get("class") or "").split())
        if tag == "a" and classes & self.RESULT_LINK_CLASSES:
            self._href=a.get("href"); self._title_parts=[]; self._in_title=True; return
        if classes & self.SNIPPET_CLASSES:
            self._snippet_parts=[]; self._snippet_target=self.results[-1] if self.results else None; self._in_snippet=True
    def handle_endtag(self, tag):
        if tag == "a" and self._in_title:
            if self._href: self.results.append(SearchResult(" ".join(self._title_parts).strip(), self._href))
            self._href=None; self._in_title=False; return
        if self._in_snippet and tag in {"a","div","td","p"}:
            snippet=" ".join(self._snippet_parts).strip()
            if snippet and self._snippet_target is not None: self._snippet_target.snippet=snippet
            self._snippet_parts=[]; self._snippet_target=None; self._in_snippet=False
    def handle_data(self, data):
        text=" ".join(data.split())
        if text and self._in_title: self._title_parts.append(text)
        if text and self._in_snippet: self._snippet_parts.append(text)

class _GenericLinkParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.results=[]; self._href=None; self._parts=[]
    def handle_starttag(self, tag, attrs):
        if tag != "a": return
        href=dict(attrs).get("href")
        if href and href.startswith(("http://","https://","/")): self._href=href; self._parts=[]
    def handle_endtag(self, tag):
        if tag == "a" and self._href:
            title=" ".join(self._parts).strip()
            if title: self.results.append(SearchResult(title,self._href))
            self._href=None; self._parts=[]
    def handle_data(self, data):
        if self._href:
            text=" ".join(data.split())
            if text: self._parts.append(text)

def _clean_ddg_url(url):
    parsed=urlparse(url)
    if parsed.path.startswith("/l/"):
        target=parse_qs(parsed.query).get("uddg",[None])[0]
        if target: return unquote(target)
    return url

def _parse_search_html(html, max_results):
    parser=_SearchParser(); parser.feed(html); parsed=parser.results
    if not parsed:
        generic=_GenericLinkParser(); generic.feed(html); parsed=generic.results
    results=[]; seen=set()
    for result in parsed:
        clean=_clean_ddg_url(result.url)
        if clean.startswith("/"): clean="https://www.bing.com"+clean
        if not urlparse(clean).netloc or clean in seen: continue
        seen.add(clean); result.url=clean; results.append(result)
        if len(results)>=max_results: break
    return results

def _parse_bing_rss(xml_text, max_results):
    root=ET.fromstring(xml_text); results=[]; seen=set()
    for item in root.findall(".//item"):
        title=" ".join((item.findtext("title") or "").split()); url=(item.findtext("link") or "").strip(); snippet=" ".join((item.findtext("description") or "").split())
        if not title or not url or url in seen: continue
        seen.add(url); results.append(SearchResult(title,url,snippet,"bing_rss"))
        if len(results)>=max_results: break
    return results

def _fetch_search_endpoint(endpoint, query, timeout):
    request=Request(endpoint+quote_plus(query),headers={"User-Agent":USER_AGENT,"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language":"en-US,en;q=0.9"})
    with urlopen(request,timeout=timeout) as response:
        body=response.read().decode("utf-8",errors="replace"); content_type=response.headers.get("Content-Type","").lower()
    if endpoint.startswith("https://www.bing.com") or "xml" in content_type:
        try: return _parse_bing_rss(body,50)
        except ET.ParseError: return []
    return _parse_search_html(body,50)

_BLOCKED_HOSTS={"maps.google.com","streetviewstudio.maps.google.com","contentpartners.maps.google.com"}

def _identity_terms(query):
    return [term.strip() for term in re.findall(r'"([^"]+)"',query.lower()) if len(term.strip())>=3]

def _is_relevant_result(result,query):
    host=urlparse(result.url).netloc.lower().split(":",1)[0]
    if host in _BLOCKED_HOSTS or host.endswith(".googleusercontent.com"): return False
    terms=_identity_terms(query)
    return not terms or any(term in " ".join((result.title,result.url,result.snippet)).lower() for term in terms)

def _filter_relevant_results(results,query,max_results):
    filtered=[]; seen=set()
    for result in results:
        if _is_relevant_result(result,query) and result.url not in seen:
            seen.add(result.url); filtered.append(result)
            if len(filtered)>=max_results: break
    return filtered

def search_public_web(query,max_results=5,timeout=12):
    """Prefer configured JSON search API, then use legacy public-search fallbacks."""
    errors=[]
    try:
        api_results=search_api(query,max_results=max_results,timeout=max(timeout,20))
        normalized=[SearchResult(r.title,r.url,r.snippet,r.provider) for r in api_results]
        relevant=_filter_relevant_results(normalized,query,max_results)
        if relevant: return relevant
        errors.append("search_api: no relevant results")
    except Exception as exc:
        errors.append(f"search_api: {exc}")
    for provider,endpoint in SEARCH_ENDPOINTS:
        try:
            results=[SearchResult(r.title,r.url,r.snippet,provider) for r in _fetch_search_endpoint(endpoint,query,timeout)]
            relevant=_filter_relevant_results(results,query,max_results)
            if relevant: return relevant
            errors.append(f"{provider}: response had no relevant parseable results")
        except Exception as exc: errors.append(f"{provider}: {exc}")
    raise RuntimeError(f"public search unavailable for query {query!r}: {'; '.join(errors)}")

class _PageTextParser(HTMLParser):
    BLOCK_TAGS={"p","div","li","h1","h2","h3","h4","article","section","br"}; IGNORE_TAGS={"script","style","noscript","svg","nav","footer"}
    def __init__(self): super().__init__(); self.parts=[]; self._ignored=0
    def handle_starttag(self,tag,attrs):
        if tag in self.IGNORE_TAGS: self._ignored+=1
        elif not self._ignored and tag in self.BLOCK_TAGS: self.parts.append("\n")
    def handle_endtag(self,tag):
        if tag in self.IGNORE_TAGS and self._ignored: self._ignored-=1
        elif not self._ignored and tag in self.BLOCK_TAGS: self.parts.append("\n")
    def handle_data(self,data):
        if not self._ignored:
            text=" ".join(data.split())
            if text: self.parts.append(text)

def fetch_public_page(url,max_chars=9000,timeout=12):
    request=Request(url,headers={"User-Agent":USER_AGENT})
    with urlopen(request,timeout=timeout) as response:
        content_type=response.headers.get("Content-Type","")
        if "text/html" not in content_type and "text/plain" not in content_type: return ""
        raw=response.read(1_500_000).decode("utf-8",errors="replace")
    parser=_PageTextParser(); parser.feed(raw)
    return re.sub(r"\n{3,}","\n\n","\n".join(parser.parts)).strip()[:max_chars]

def build_queries(company,contact=None):
    queries=[f'"{company}" ecommerce operations',f'"{company}" Shopify Unicommerce',f'"{company}" hiring operations manager',f'"{company}" inventory fulfilment RTO',f'"{company}" careers']
    if contact: queries.append(f'"{contact}" "{company}"')
    return queries

def research_company(company,contact=None,max_sources=8):
    results=[]; seen_urls=set(); errors=[]
    for query in build_queries(company,contact):
        try:
            for item in search_public_web(query,max_results=8):
                if item.url not in seen_urls: seen_urls.add(item.url); results.append(item)
                if len(results)>=max_sources: break
        except Exception as exc: errors.append(f"search failed for {query!r}: {exc}")
        if len(results)>=max_sources: break
    evidence=[]; pages=[]
    for result in results:
        try: text=fetch_public_page(result.url)
        except Exception as exc: errors.append(f"fetch failed for {result.url}: {exc}"); text=""
        if text:
            pages.append({"title":result.title,"url":result.url,"text":text}); evidence.append(EvidenceItem(f"Public page discovered for {company}",result.url,result.title,text[:2500]))
        elif result.snippet: evidence.append(EvidenceItem(f"Search result mentioning {company}",result.url,result.title,result.snippet))
    return {"company":company,"contact":contact,"queries":build_queries(company,contact),"sources_found":len(results),"sources_fetched":len(pages),"evidence":[asdict(item) for item in evidence],"pages":pages,"errors":errors}
