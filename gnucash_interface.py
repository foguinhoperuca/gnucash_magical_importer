#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Meant to be reuseable interface with gnucash
'''

import os
import logging
import configparser
import datetime
from decimal import Decimal

from gnucash import Session, Transaction, Split, GncNumeric
from util import Util

# FIXME curr = Util().DEFAULT_CURRENCY do not work...
# def get_currency(book, curr = Util().DEFAULT_CURRENCY):
def get_currency(book, curr = 'BRL'):
    commod_tab = book.get_table()
    # currency = commod_tab.lookup('ISO4217', curr)  # FIXME curr isn't working.
    currency = commod_tab.lookup('ISO4217', 'BRL') # works!!!

    # curr_local = Util().DEFAULT_CURRENCY
    # currency = commod_tab.lookup('ISO4217', curr_local)
    # curr_local2 = 'BRL'
    # currency = commod_tab.lookup('ISO4217', curr_local2)

    # logging.info('*****************************************')
    # logging.debug('XXXXXXXXXXXX curr INSIDE get_currency')
    # logging.debug('XXXXXXXXXXXX commod_tab: type => {commod_type}, value => {value}'.format(commod_type = type(commod_tab), value = commod_tab))
    # logging.debug('XXXXXXXXXXXX currency: type => {curr_type}, value => {value}'.format(curr_type = type(currency), value = currency))
    # logging.info('*****************************************')

    return currency

# Extracted from https://github.com/hjacobs/gnucash-qif-import/blob/master/import.py#lookup_account_by_path(root, path)
def get_account_by_path(root, path): # FIXME this method isn't working fine anymore...
    acc = None
    if not root == None:
        acc = root.lookup_by_name(path[0])
        # logging.debug("========================================================")
        # logging.debug("root.....: {a}".format(a = root))
        # logging.debug("path[0]..: {p}".format(p = path[0]))
        # logging.debug("acc......: {a}".format(a = acc))
        # logging.debug("========================================================")

        # # FIXME test isn't not working anymore
        # if acc.get_instance() == None:
        #     raise Exception('NO Good: account path not found --> %s' % (path[0]))

        if len(path) > 1:
            get_account_by_path(acc, path[1:])

    return acc

def get_account(book, acc_name):
    return get_account_by_path(book.get_root_account(), acc_name.split(':'))

def create_gnucash_tansaction(book, item, curr, account_from, account_to):
    if curr is None:
        # FIXME default currency is hard-coded inside get_currency
        curr = get_currency(book, Util().DEFAULT_CURRENCY)

    if item is None:
        raise Exception("Could not create a gnucash transaction: missing item!!")

    if book is None:
        raise Exception("Could not create a gnucash transaction: missing book!!")

    acc_from = get_account(book, account_from)
    acc_to = get_account(book, account_to)
    # amount = int(Decimal(item.split_amount.replace(',', '.')) * curr.get_fraction()) # FIXME need it yet?
    amount = int(Decimal(item.amount) * curr.get_fraction())
    
    logging.debug("::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
    logging.debug("book...............: {b}".format(b = book))
    logging.debug("account_name_from..: {a}".format(a = account_from))
    logging.debug("account_name_to....: {a}".format(a = account_to))
    logging.debug("acc_from...........: {account}".format(account = acc_from))
    logging.debug("acc_to.............: {account}".format(account = acc_to))
    logging.debug("[create_gnucash_transaction] amount: {amount} :: get_mnemonic: {mnemonic} :: curr: {curr}".format(amount = amount, curr = curr, mnemonic = curr.get_mnemonic()))
    
    tx = Transaction(book)
    # show_methods(tx)

    tx.BeginEdit()
    tx.SetCurrency(curr)
    # tx.SetDateEnteredTS(datetime.datetime.now())
    tx.SetDateEnteredSecs(datetime.datetime.now())
    # tx.SetDatePostedTS(item.date)
    tx.SetDatePostedSecs(item.date)
    tx.SetDescription(item.memo)

    split_from = Split(book)
    split_from.SetParent(tx)
    split_from.SetAccount(acc_from)
    split_from.SetValue(GncNumeric(amount, curr.get_fraction()))
    split_from.SetAmount(GncNumeric(amount, curr.get_fraction()))

    split_to = Split(book)
    split_to.SetParent(tx)
    split_to.SetAccount(acc_to)
    split_to.SetValue(GncNumeric(amount, curr.get_fraction()))
    split_to.SetAmount(GncNumeric(amount, curr.get_fraction()))

    tx.CommitEdit()

    logging.debug("::::::::::::::::::::::::::::::::::::::::::::::::::::::::")

# Helper to discovery API of an object
def show_methods(obj):
    logging.debug("_______________________________________________________")
    for method in [method_name for method_name in dir(obj) if callable(getattr(obj, method_name))]:
        print(method)
    logging.debug("_______________________________________________________")
    
# FIXME receive items or gnucash transaction?
def write_to_gnucash_file(account, dry_run = True, gnucash_file = Util().DEFAULT_GNUCASH_FILE, curr = Util().DEFAULT_CURRENCY):
    session = Session(gnucash_file)
    book = session.book
    currency = get_currency(book, curr)
    imported_items = set()
    
    items = account.get_items(account, os.path.splitext(account.account_src_file)[1])

    # for item in account.get_items(account, os.path.splitext(account.account_src_file)[1]):
    for item in items:
        # if item.as_tuple() in imported_items:
        if item in imported_items:
            logging.info("Skipped because it already was imported!!!")
            continue

        # logging.info('############### CONTENT for item XXX ###############')
        # logging.debug("amount: {amount} :: date: {date} :: memo: {memo}".format(amount = item.amount, date = item.date, memo = item.memo.encode('iso-8859-1')))

        # logging.debug("----------------------------- SHOW currency before call create_gnucash_tansaction()")
        # logging.debug(currency)
        # logging.debug(Util().DEFAULT_CURRENCY)
        # logging.debug("----------------------------- SHOW currency before call create_gnucash_tansaction()")
        create_gnucash_tansaction(book, item, currency, account.account_from, account.to)
        # imported_items.add(item.as_tuple())
        imported_items.add(item)

        if dry_run:
            logging.info('############### DRY-RUN ###############')
        else:
            logging.info('Saving GNUCash file..')
            session.save()

    session.end()