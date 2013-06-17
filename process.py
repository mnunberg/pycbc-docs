#!/usr/bin/env python
import sys
from cStringIO import StringIO
from multiprocessing import Pool
import glob
import os
import argparse
import subprocess
from lxml import etree

from asciidocapi import AsciiDocAPI, Options

XML_DECL = \
'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE book PUBLIC "-//OASIS//DTD DocBook XML V4.5//EN" "http://www.oasis-open.org/docbook/xml/4.5/docbookx.dtd">
<?asciidoc-toc?>
<?asciidoc-numbered?>
'''

ap = argparse.ArgumentParser()
ap.add_argument('-f', '--formats',
        action='append',
        default=['docbook'],
        help="Formats to generate")

ap.add_argument('-i', '--input',
        metavar='FILES',
        nargs='+')

options = ap.parse_args()
inputs = options.input
if not inputs:
    inputs = glob.glob("*.asciidoc")

def convert_file_pdf(fname):
    cmd = ("a2x", "-f", "pdf", "--fop", "-D", "pdf", fname)
    po = subprocess.Popen(cmd)
    po.communicate()
    assert po.returncode == 0


def convert_file_html(fname):
    target = "html/" + fname.replace(".asciidoc", ".html")
    ai = AsciiDocAPI()
    ai.attributes.update({
            'data-uri' : True,
            'toc' : True,
            'icons' : True,
            'iconsdir' : '/etc/asciidoc/images/icons'
            })
    ai.execute(fname, target)
    for m in ai.messages:
        print m

def convert_file_xml(fname):
    outbuf = StringIO()
    target = "xml/" + fname.replace(".asciidoc", ".xml")

    ai = AsciiDocAPI()
    ai.options.append('--doctype', 'book')
    ai.execute(fname, outfile = outbuf, backend="docbook")

    fp = open(target, "w")
    fp.write(XML_DECL)

    outbuf.seek(0)
    xml = etree.fromstring(outbuf.read())
    chapters = xml.xpath("//chapter")
    for ch in chapters:
        fp.write(etree.tostring(ch))
    
    for m in ai.messages:
        print m


FMT_MAP = {
        'docbook' : convert_file_xml,
        'xml' : convert_file_xml,
        'html' : convert_file_html,
        'pdf' : convert_file_pdf,
        }

p = Pool(processes=16)
results = []
for src in inputs:
    for fmt in options.formats:
        fn = FMT_MAP[fmt]
        print "Scheduling '%s' -> '%s'" % (src,fmt)
        res = p.apply_async(fn, [src])
        results.append(res)

for res in results:
    res.get()
