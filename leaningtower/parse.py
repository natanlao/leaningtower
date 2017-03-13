# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import imp
import logging
import re
from urlparse import parse_qs

from .models import Course, db, seasonMapping, Term, Textbook

log = logging.getLogger(__name__)
logging.basicConfig()

try:
    import serek as phpserialize
    log.info("Using serek for php deserialization")
except ImportError:
    import phpserialize
    log.info("Using phpserialize for php deserialization")

PARSER = "html.parser"
try:
    imp.find_module("lxml")
    PARSER = "lxml"
    log.info("Using lxml for HTML parsing")
except ImportError:
    log.info("Using html.parser for HTML parsing")

days = [
    ('sun', 'Sn'),
    ('mon', 'M'),
    ('tue', 'Tu'),
    ('wed', 'W'),
    ('thr', 'Th'),
    ('fri', 'F'),
    ('sat', 'St')
]


def parse_classdata(classdata, href):
    """Takes a Pisa class_data argument and parses it into a dictionary in
    the form of :class:`Course`."""
    data = phpserialize.loads(classdata.decode('base64'))

    attributes = {
        'classnum': data['CLASS_NBR'],
        'name': "%s %s" % (data['SUBJECT'], data['CATALOG_NBR'].strip()),
        'description': data['DESCR'],
        'section': data['CLASS_SECTION'],
        'term': Term.get(Term.id == data['STRM']),
        'instructor_first': data['FIRST_NAME'],
        'instructor_last': data['LAST_NAME'],
        'instructor_mid': data['MIDDLE_NAME'],
        'location': data['FAC_DESCR'],
        'slug': href,
        'sun': data['SUN'],
        'mon': data['MON'],
        'tue': data['TUES'],
        'wed': data['WED'],
        'thr': data['THURS'],
        'fri': data['FRI'],
        'sat': data['SAT'],
        'start_time': data['START_TIME'],
        'end_time': data['END_TIME'],
        'capacity': data['ENRL_CAP'],
        'enrolled': data['ENRL_TOT'],
        'waitlist': data['WAIT_TOT']
    }

    # LALS 194Q has a special character in its description that Peewee chokes on
    # during parsing.
    if attributes['name'] == "LALS 194Q":
        attributes['description'] = ''.join(c for c in attributes['description'] if c.isalnum())

    return attributes


def parse_html(handle):
    """Takes content of a dump of the schedule of classes from Pisa."""
    log.info("Parsing data for %s", handle.name)
    s = BeautifulSoup(handle.read(), PARSER)
    # Get hrefs of each course's details page (it has a lot of data in it
    # encoded in base64 and it's super cool!)
    links = [e for e in s.find_all("div", class_="panel-heading-custom")]

    courses = []
    for link in links:
        classdata = parse_qs(link.h2.a['href'])['class_data'][0]
        materials_id = link.next_sibling.next_sibling.find(class_="hide-print").a['href'].split("=")[1].split('.')[0]
        rv = parse_classdata(classdata, link.h2.a['href'])
        rv.update({'materials_id': materials_id})
        courses.append(rv)

    log.info("Beginning db insert")
    with db.atomic():
        # Maybe split this insert up into chunks?
        Course.insert_many(courses).execute()


def parse_terms(handle):
    s = BeautifulSoup(handle.read(), PARSER)
    terms = []

    # Need to use .findAll("option") because .find picks up some newline artifacts
    for option in s.find("select", id="term_dropdown").findAll("option"):
        year, season, _ = option.text.split(" ")
        terms.append({
            'id': int(option['value']),
            'year': int(year),
            'season': seasonMapping[season],
        })

    with db.atomic():
        Term.insert_many(terms).execute()


def parse_books(handle, course_id):
    isbns = set()  # ISBNs can be listed multiple times in the same page - ensure no repeats
    isbn_pattern = r'"isbn":"((\\"|[^"]|)*)"'  # Matches isbn
    for i, _ in re.findall(isbn_pattern, handle.read()):
        log.debug("Adding ISBN %s for course %d", i, course_id)
        isbns.add(int(i))

    for isbn in isbns:
        with db.atomic():
            Textbook.get_or_create(course=course_id, isbn=isbn)
