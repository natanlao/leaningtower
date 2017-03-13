# -*- coding: utf-8 -*-
import logging
import peewee

log = logging.getLogger(__name__)

db = peewee.Proxy()


seasonMapping = {
    "Winter": 'W',
    "Spring": 'S',
    "Summer": 'U',
    "Fall": 'F',
}


class Term(peewee.Model):
    id = peewee.PrimaryKeyField()
    year = peewee.SmallIntegerField()
    season = peewee.FixedCharField(max_length=1)  # seasonMapping

    class Meta:
        database = db


class Course(peewee.Model):
    # TODO: Note term and year
    # Course Description
    classnum = peewee.IntegerField()
    name = peewee.CharField()
    description = peewee.CharField()
    section = peewee.CharField()
    term = peewee.ForeignKeyField(Term)

    # TODO: Create Instructor table
    # Instructor ID
    instructor_first = peewee.CharField(null=True)
    instructor_last = peewee.CharField(null=True)
    instructor_mid = peewee.CharField(null=True)

    location = peewee.CharField(null=True)
    slug = peewee.TextField()

    # Course scheduling
    sun = peewee.BooleanField()
    mon = peewee.BooleanField()
    tue = peewee.BooleanField()
    wed = peewee.BooleanField()
    thr = peewee.BooleanField()
    fri = peewee.BooleanField()
    sat = peewee.BooleanField()
    start_time = peewee.TimeField(null=True, formats=["%I:%M%p"])
    end_time = peewee.TimeField(null=True, formats=["%I:%M%p"])

    # Enrollment statistics
    # UCSC doesn't even have 30k students, so using a smallint *should* be okay
    capacity = peewee.SmallIntegerField()
    enrolled = peewee.SmallIntegerField()
    waitlist = peewee.SmallIntegerField()

    materials_id = peewee.CharField()

    class Meta:
        database = db


class Textbook(peewee.Model):
    course = peewee.ForeignKeyField(Course)
    isbn = peewee.BigIntegerField()

    class Meta:
        database = db
