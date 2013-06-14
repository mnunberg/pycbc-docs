#!/bin/sh
asciidoc -v -a data-uri -a toc -a icons -a iconsdir=/etc/asciidoc/images/icons $@
