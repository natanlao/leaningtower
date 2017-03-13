# -*- coding: utf-8 -*-
import logging
import requests

from .util import cache, limit_rate

log = logging.getLogger(__name__)

# Most of Pisa's search interface revolves around this one page, which makes
# things a little simpler.
AIS_URL = "https://pisa.ucsc.edu/class_search/index.php"

# This is the base URL for the bookstore / comparison page for each course.
BOOKSTORE_URL = "http://ucsc.verbacompare.com/comparison?id="

# Pisa uses an old, insecure cipher, which Requests rightfully chokes on by default.
# To get around this, we need to identify the cipher as safe for the time being.
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ":EDH-RSA-DES-CBC3-SHA"

# Pisa also blocks crawlers by default, so let's pretend to be Chrome.
headers = requests.utils.default_headers()
headers.update({
    'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36",
})


@cache("term", 0, inherit_filename=True)
@limit_rate(10)
def fetch_classes_page(term_number, filename=None):
    logging.info("Fetching classes for term %d.", term_number)
    initial_query = {
        'action': ["results"],
        'binds[:term]': [term_number],
        'binds[:reg_status]': ["all"],
        'binds[:subject]': '',
        'binds[:catalog_nbr_op]': ["="],
        'binds[:catalog_nbr]': '',
        'binds[:title]': '',
        'binds[:instr_name_op]': ["="],
        'binds[:instructor]': '',
        'binds[:ge]': '',
        'binds[:crse_units_op]': ["="],
        'binds[:crse_units_from]': '',
        'binds[:crse_units_to]': '',
        'binds[:crse_units_exact]': '',
        'binds[:days]': '',
        'binds[:times]': '',
        'binds[:acad_career]': '',
    }

    update_query = {
        'action': ['update_segment'],
        'Rec_Dur': ['10000']
    }

    with requests.Session() as s:
        s.headers.update(headers)
        s.headers.update({'Content-Type': "application/x-www-form-urlencoded"})
        # Make the initial search query
        s.post(AIS_URL, data=initial_query)
        # Get all the search results on one page.
        s.headers.update({
            'Origin': "https://pisa.ucsc.edu",
            'Referer': "https://pisa.ucsc.edu/class_search/index.php"
        })

        # These files are generally somewhat large (Winter 2017 is almost 7
        # million characters!) so the file is written incrementally.
        # http://stackoverflow.com/a/14114741
        with open(filename, "wb") as f:
            r = s.post(AIS_URL, data=update_query, stream=True)
            for block in r.iter_content(1024):
                f.write(block)

    return open(filename)


@cache("", "terms.html", inherit_filename=False)
def fetch_terms(filename=None):
    log.info("Downloading term data from Pisa.")
    r = requests.get(AIS_URL, headers=headers)
    with open(filename, "wb") as f:
        f.write(r.content)

    return open(filename, "r")


# TODO: use grequests?
@cache("books", 0, inherit_filename=True)
@limit_rate(2)
def fetch_book_page(book_id, filename=None):
    log.info("Downloading book page for %s", book_id)
    r = requests.get(BOOKSTORE_URL + book_id)
    with open(filename, "wb") as f:
        f.write(r.content)

    return open(filename, "r")
