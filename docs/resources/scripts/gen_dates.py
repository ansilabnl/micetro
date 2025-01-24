#!/usr/bin/env python3
"""Generate all dates for Asciidoctor."""

import sys
import os
import calendar
import time
import locale

def setdates(usedate=None, r_lang='english'):
    """Convert all dates to document format."""
    docdate = {}

    # If the replacement-date is defined, make sure we
    # have all other date / time parts as well
    if r_lang == 'dutch':
        try:
            locale.setlocale(locale.LC_ALL, 'nl_NL.utf8')
        except locale.Error:
            locale.setlocale(locale.LC_ALL, 'nl_NL')
    else:
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.utf8')
        except locale.Error:
            locale.setlocale(locale.LC_ALL, 'en_US')

    # If no document date found, use today
    if not usedate:
        usedate = time.strftime('%Y-%m-%d')

    curdate = time.strptime(usedate, '%Y-%m-%d')
    curdate = time.localtime(calendar.timegm(curdate))

    docdate['r_year'] = {}
    docdate['r_year']['desc']           = 'Year in 4 digits'
    docdate['r_year']['val']            = "%04d" % curdate.tm_year

    docdate['r_month'] = {}
    docdate['r_month']['desc']          = 'Month in 2 digits'
    docdate['r_month']['val']           = "%02d" % curdate.tm_mon

    docdate['r_mday'] = {}
    docdate['r_mday']['desc']           = 'Day in the month in 2 digits'
    docdate['r_mday']['val']            = "%02d" % curdate.tm_mday

    docdate['r_dayname'] = {}
    docdate['r_dayname']['desc']        = 'Full name of the day'
    docdate['r_dayname']['val']         = calendar.day_name[curdate.tm_wday]

    docdate['r_daynameshort'] = {}
    docdate['r_daynameshort']['desc']   = 'Short name of the day'
    docdate['r_daynameshort']['val']    = calendar.day_abbr[curdate.tm_wday]

    docdate['r_monthname'] = {}
    docdate['r_monthname']['desc']      = 'Full name of the month'
    docdate['r_monthname']['val']       = calendar.month_name[curdate.tm_mon]

    docdate['r_monthnameshort'] = {}
    docdate['r_monthnameshort']['desc'] = 'Short name of the month'
    docdate['r_monthnameshort']['val']  = calendar.month_abbr[curdate.tm_mon]

    docdate['r_weekday'] = {}
    docdate['r_weekday']['desc']        = 'Day number in week.'
    docdate['r_weekday']['val']         = str(curdate.tm_wday + 1)

    docdate['r_yearday'] = {}
    docdate['r_yearday']['desc']        = 'Day number in year'
    docdate['r_yearday']['val']         = str(curdate.tm_yday)

    docdate['r_weekno'] = {}
    docdate['r_weekno']['desc']         = 'ISO 8601 week number'
    docdate['r_weekno']['val']          = str(time.strftime('%V', curdate))

    docdate['r_epoch'] = {}
    docdate['r_epoch']['desc']          = 'Time in epoch (from date)'
    docdate['r_epoch']['val']           = str(calendar.timegm(curdate))

    docdate['r_tz'] = {}
    docdate['r_tz']['desc']             = 'Timezone (CET or CEST)'
    docdate['r_tzlong'] = {}
    docdate['r_tzlong']['desc']         = 'Timezone long format'
    docdate['r_tz_offset'] = {}
    docdate['r_tz_offset']['desc']      = 'Timezone offset to UTC'

    if curdate.tm_isdst == 1:
        docdate['r_tz']['val']         = 'CEST'
        docdate['r_tzlong']['val']     = 'W. Europe Standard Time'
        docdate['r_tz_offset']['val']  = '+02:00'
    else:
        docdate['r_tz']['val']         = 'CET'
        docdate['r_tzlong']['val']     = 'W. Europe Time'
        docdate['r_tz_offset']['val']  = '+01:00'

    return docdate

# Start of main program
prname = os.path.basename(sys.argv[0])

# First parameter should be the file containing the docdate
if len(sys.argv) < 2:
    sys.exit("Syntax: %s fname [english|dutch]" % prname)

# Check file
if not os.path.exists(sys.argv[1]):
    sys.exit("%s: File %s does not exist" % (prname, sys.argv[1]))

# And read it
with open(sys.argv[1], 'rt', encoding='utf8') as f:
    content = f.readlines()

# Check if a revdate is there
revdate = None
for line in content:
    if line.startswith(':revdate:'):
        revdate = line.split()[1]

# Check if a language is requested
if len(sys.argv) < 3:
    r_lang = 'english'
else:
    r_lang = sys.argv[2]

# Get all date formats
docdate = setdates(revdate, r_lang)

# Find longest key
ml = 0
for k in docdate:
    ml = max(ml, len(k))

# Print comment header
print("""//
// This file is auto-generated by the '%s' script
//
// This is a list of defined variables you can use in your
// document, to ensure it doesn't get to stale (e.g. code output)
//""" % prname)

# Show all available keys
fstr = '// %-{0}s -> %s'.format(ml)
for k in sorted(docdate):
    print(fstr % (k, docdate[k]['desc']))
print('//')

# Show all defined variables
for k in sorted(docdate):
    print(':%s: %s' % (k, docdate[k]['val']))

sys.exit(0)
