#!/usr/bin/env python3

import concurrent.futures
import html
import re
import time
import requests

from urllib.parse import urljoin, urlparse

WEBSITE = "https://www.dhmo.org/research.html"

def download(url):
    '''download the HTML from a webpage'''
    ### requests!
    response = requests.get(
        url,
        headers={"User-Agent": "DHMOResearchProject/1.0"},
        timeout=15
    )
    response.raise_for_status()
    response.encoding = "utf-8"
    return response.text


def find_reports():
    '''find the links to research reports'''
    webpage = download(WEBSITE)

    ## find all links in the HTML
    addresses = re.findall(
        r'href=["\']([^"\']+)["\']',
        webpage,
        re.IGNORECASE
    )

    # convert links into full URLs (using map/functional programming!)
    addresses = list(map(
        lambda address: urljoin(WEBSITE, html.unescape(address)),
        addresses
    ))

    # keep only links to research reports (with a filter/functional programming!)
    reports = list(filter(
        lambda address: urlparse(address).path.startswith("/reports/")
        and urlparse(address).path.endswith(".html")
        and urlparse(address).hostname in ("dhmo.org", "www.dhmo.org"),
        addresses
    ))

    return list(dict.fromkeys(reports))

def read_report(address):
    '''retrieve the title of a research report'''
    try:
        webpage = download(address)

        title = re.search(
            r"<h2[^>]*>(.*?)</h2>",
            webpage,
            re.IGNORECASE | re.DOTALL
        )

        if title:
            clean_title = re.sub(r"<[^>]+>", "", title.group(1))
            return html.unescape(clean_title.strip())

    except requests.RequestException as error:
        print(f"Could not read {address}: {error}")

    return None

def collect_reports(addresses, threads):
    '''scrape report titles with a specified number of threads'''
    ### performance measurement!
    start = time.perf_counter()

    ### concurrent.futures!
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as pool:
        results = list(pool.map(read_report, addresses))
    
    #### functional programming!
    titles = list(filter(lambda title: title is not None, results))

    duration = time.perf_counter() - start

    return titles, duration


def main():
    try:
        addresses = find_reports()
    except requests.RequestException as error:
        print(f"Could not access the research archive: {error}")
        return

    print(f"Found {len(addresses)} research reports.")

    if not addresses:
        print("No report links were found.")
        return

    measurements = []

    for threads in (1, 4):
        titles, duration = collect_reports(addresses, threads)
        measurements.append(duration)

        print(f"\n--- Results with {threads} thread(s) ---")

        for title in titles:
            print(f"- {title}")

        print(f"\nReports retrieved: {len(titles)}")
        print(f"Time: {duration:.3f} seconds")

    if measurements[1] > 0:
        ratio = measurements[0] / measurements[1]
        print(f"\nSpeedup with 4 threads: {ratio:.2f}x")


if __name__ == "__main__":
    main()

