P1tr - The Next Generation
==========================

![P1tr logo](https://raw.github.com/howard/p1tr-tng/master/logo/logo128.png)

[![Build Status](https://secure.travis-ci.org/howard/p1tr-tng.png?branch=master)](http://travis-ci.org/howard/p1tr-tng)

P1tr is a highly modular, configurable IRC bot. This is a complete remake of the
[original P1tr](https://github.com/AustrianGeekForce/p1tr-legacy), created by
the AustrianGeekForce and contributors.

Current version: 0.1alpha
Requires: Python 3.2, oyoyo

What's new?
-----------

P1tr TNG aims to be harder, better, faster, and stronger than the old P1tr.
Although it's not finished yet (there are still lots of plugins left to port),
P1tr TNG brings the following improvements over the old P1tr:

* Uses Python 3
* Integrated support for unit-testing plugins
* Lightweight oyoyo instead of heavyweight Twisted Words as IRC library
* Optional NickServ-based authorization module

How to install?
---------------

* Via git:
    1. Install Python 3.2 and oyoyo
    2. `$ git clone git://github.com/AustrianGeekForce/p1tr-legacy.git`
* Via easy_install: `$ easy_install3 P1tr`
* Via pip: `$ pip install P1tr`

Afterwards, just run the `p1tr` command, or in case if install via git, run
`$ python3.2 p1tr/p1tr.py` from the cloned P1tr directory.
