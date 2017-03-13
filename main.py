# -*- coding: utf-8 -*-
import logging
import peewee
import os

from leaningtower.fetch import fetch_book_page, fetch_classes_page, fetch_terms
from leaningtower.models import Course, db, Term, Textbook
from leaningtower.parse import parse_books, parse_html, parse_terms

log = logging.getLogger('leaningtower')
logging.basicConfig(level=logging.DEBUG)

peewee_log = logging.getLogger('peewee')
peewee_log.setLevel(logging.DEBUG)
peewee_log.addHandler(logging.StreamHandler())

DB_NAME = "leaningtower.db"

if __name__ == "__main__":
    db.initialize(peewee.SqliteDatabase(DB_NAME))
    if not os.path.exists(DB_NAME):
        # If the database doesn't exist, create it.
        log.info("Didn't find database '%s', will create it.", DB_NAME)
        db.create_tables([Course, Term, Textbook])

        log.info("Fetching term data")
        with fetch_terms() as f:
            parse_terms(f)

        for term in Term.select():
            log.info("Inserting for term %d", term.id)
            with fetch_classes_page(term.id) as f:
                parse_html(f)
    else:
        cnt = Course.select().count()
        curr = 1
        for course in Course.select().order_by(Course.id.desc()):
           log.info("%d/%d", curr, cnt)
           with fetch_book_page(course.materials_id) as f:
               parse_books(f, course.id)
           curr += 1
