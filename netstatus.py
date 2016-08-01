#!/usr/bin/python

import re
import requests

login_url = 'http://192.168.1.1/cgi-bin/webproc'
status_url = 'http://192.168.1.1/cgi-bin/webproc?getpage=html/index.html&var:menu=status&var:page=deviceinfo'

# yea yea yea .. its hardcoded. deal with it.
username = 'admin'
password = 'admin'

s = requests.Session()

def init_session():
    first_response = s.get(login_url)
    return first_response.cookies['sessionid']

def perform_login(session_id):
    form_data = {
        'getpage': 'html/index.html',
        'errorpage': 'html/main.html',
        'var:menu':   'setup',
        'var:page':   'wizard',
        'obj-action': 'auth',
        ':username':  'admin',
        ':password':  'admin',
        ':action':    'login',
    }
    form_data[':sessionid'] = session_id

    headers = {
        'Content-Type':'application/x-www-form-urlencoded',
    }

    login_response = s.post(login_url, data=form_data, headers=headers)
    if login_response.status_code == 302:
        return True

    # figure out error code which is on 38th line
    lines = login_response.iter_lines()
    # Save the first line for later or just skip it
    first_line = next(lines)
    line_number = 1
    # skip upto 37th line
    while line_number < 37:
        next(lines)
        line_number += 1
    error_code = next(lines)
    print "error code line: ", error_code

    return False

def perform_logout(session_id):
    form_data = {
        'getpage':'html/main.html',
        'obj-action':'auth',
        ':action':'logout',
    }
    form_data[':sessionid'] = session_id

    headers = {
        'Content-Type':'application/x-www-form-urlencoded',
    }

    logout_response = s.post(login_url, data=form_data, headers=headers)
    return logout_response.status_code == 200

def get_status():
    """
        grab page
        extract info from specific line number instead of parsing html etc
        its deterministic enough for my use case
    """
    status_response = s.get(status_url)

    lines = status_response.iter_lines()
    # Save the first line for later or just skip it
    first_line = next(lines)
    line_number = 1

    # skip upto 96th line
    while line_number < 96:
        next(lines)
        line_number += 1

    dsl_uprate = next(lines) #97th line
    dsl_downrate = next(lines) #98th line
    line_number += 2

    # skip upto 118th line
    while line_number < 118:
        next(lines)
        line_number += 1

    dsl_ipaddr = next(lines) #119
    line_number += 1

    # skip upto 124th line
    while line_number < 124:
        next(lines)
        line_number += 1

    dsl_uptime = next(lines) #125
    line_number += 1

    # grab what is needed
    m = re.search('([0-9])\w+', dsl_uprate)
    uprate = m.group(0)

    m = re.search('([0-9])\w+', dsl_downrate)
    downrate = m.group(0)

    m = re.search('([0-9])\w+', dsl_uptime)
    uptime = m.group(0)

    # extra dot '.' for ip address
    m = re.search('([0-9.])+', dsl_ipaddr)
    ipaddr = m.group(0)

    return (uprate, downrate, uptime, ipaddr)

def main():
    sid = init_session()
    #print "SessionId: ", sid

    success = perform_login(sid)
    if not success:
        print 'login failed'
        return

    uprate, downrate, uptime, ipaddr = get_status()

    print "Downrate: %s, Uprate: %s" % (downrate, uprate)

    seconds = int(uptime)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    print "Up for %d:%02d:%02d" % (h, m, s)

    print "IP Address: %s " % ipaddr

    perform_logout(sid)


if __name__ == '__main__':
    main()

