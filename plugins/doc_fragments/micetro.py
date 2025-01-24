#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2020-2025, Men&Mice, Ton Kersten
# GNU General Public License v3.0
# see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt
"""Ansible Claim IP address module.

Part of the Men&Mice Ansible integration

Module to claim IP addresses in DHCP in the Micetro
"""

class ModuleDocFragment(object):
    """Extend the document class."""

    DOCUMENTATION = r"""
      author:
        - Ton Kersten <t.kersten@atcomputing.nl>
      options:
        mm_provider:
          description: Definition of the Micetro API mm_provider.
          type: dict
          required: True
          suboptions:
            mm_url:
              description: Men&Mice API server to connect to.
              required: True
              type: str
            mm_user:
              description: userid to login with into the API.
              required: True
              type: str
            mm_password:
              description: password to login with into the API.
              required: True
              type: str
              no_log: True
    """
