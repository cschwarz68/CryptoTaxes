#! python3

import pytest
from crypto import *


@pytest.fixture
def lifo():
    policy = "LIFO"
    print(policy)
    crypto = Crypto("CoinbaseTransactionsHistoryReport-Test.csv", policy)
    crypto.clear_cache()
    crypto.clear_output()
    crypto.dispose_all()
    dispos = Disposition(crypto.outfile)
    return dispos


@pytest.fixture
def fifo():
    policy = "FIFO"
    print(policy)
    crypto = Crypto("CoinbaseTransactionsHistoryReport-Test.csv", policy)
    crypto.clear_cache()
    crypto.clear_output()
    crypto.dispose_all()
    dispos = Disposition(crypto.outfile)
    return dispos


@pytest.fixture
def hifo():
    policy = "HIFO"
    print(policy)
    crypto = Crypto("CoinbaseTransactionsHistoryReport-Test.csv", policy)
    crypto.clear_cache()
    crypto.clear_output()
    crypto.dispose_all()
    dispos = Disposition(crypto.outfile)
    return dispos


def test_lifo_btc(lifo):
    coin = "BTC"
    year = 2021
    df = lifo.df
    gains = lifo.gains
    df_year = df[df["year"] == year]
    dfasset = df_year[df_year["Asset"] == coin]
    gains_longterm, gains_shortterm = gains(dfasset)
    assert (
        round(gains_longterm, digits) == 548.464
        and round(gains_shortterm, digits) == -34.974
    )


def test_lifo_xlm(lifo):
    coin = "XLM"
    year = 2021
    df = lifo.df
    gains = lifo.gains
    df_year = df[df["year"] == year]
    dfasset = df_year[df_year["Asset"] == coin]
    gains_longterm, gains_shortterm = gains(dfasset)
    assert (
        round(gains_longterm, digits) == 409.2
        and round(gains_shortterm, digits) == -14.0
    )


def test_lifo_atom(lifo):
    coin = "ATOM"
    year = 2021
    df = lifo.df
    gains = lifo.gains
    df_year = df[df["year"] == year]
    dfasset = df_year[df_year["Asset"] == coin]
    gains_longterm, gains_shortterm = gains(dfasset)
    assert (
        round(gains_longterm, digits) == 0 and round(gains_shortterm, digits) == 59.967
    )


def test_fifo_btc(fifo):
    coin = "BTC"
    year = 2021
    df = fifo.df
    gains = fifo.gains
    df_year = df[df["year"] == year]
    dfasset = df_year[df_year["Asset"] == coin]
    gains_longterm, gains_shortterm = gains(dfasset)
    assert (
        round(gains_longterm, digits) == 763.514 and round(gains_shortterm, digits) == 0
    )


def test_fifo_xlm(fifo):
    coin = "XLM"
    year = 2021
    df = fifo.df
    gains = fifo.gains
    df_year = df[df["year"] == year]
    dfasset = df_year[df_year["Asset"] == coin]
    gains_longterm, gains_shortterm = gains(dfasset)
    assert round(gains_longterm, digits) == 440 and round(gains_shortterm, digits) == 0


def test_fifo_atom(fifo):
    coin = "ATOM"
    year = 2021
    df = fifo.df
    gains = fifo.gains
    df_year = df[df["year"] == year]
    dfasset = df_year[df_year["Asset"] == coin]
    gains_longterm, gains_shortterm = gains(dfasset)
    assert round(gains_longterm, digits) == 0 and round(gains_shortterm, digits) == 130


def test_hifo_btc(hifo):
    coin = "BTC"
    year = 2021
    df = hifo.df
    gains = hifo.gains
    df_year = df[df["year"] == year]
    dfasset = df_year[df_year["Asset"] == coin]
    gains_longterm, gains_shortterm = gains(dfasset)
    assert (
        round(gains_longterm, digits) == 528.458
        and round(gains_shortterm, digits) == -34.974
    )


def test_hifo_xlm(hifo):
    coin = "XLM"
    year = 2021
    df = hifo.df
    gains = hifo.gains
    df_year = df[df["year"] == year]
    dfasset = df_year[df_year["Asset"] == coin]
    gains_longterm, gains_shortterm = gains(dfasset)
    assert (
        round(gains_longterm, digits) == 409.2 and round(gains_shortterm, digits) == -14
    )


def test_hifo_atom(hifo):
    coin = "ATOM"
    year = 2021
    df = hifo.df
    gains = hifo.gains
    df_year = df[df["year"] == year]
    dfasset = df_year[df_year["Asset"] == coin]
    gains_longterm, gains_shortterm = gains(dfasset)
    assert (
        round(gains_longterm, digits) == 0 and round(gains_shortterm, digits) == 59.965
    )
