#! python3

import argparse
import dateutil
import glob
import pyinputplus as pyip
import os
import pandas as pd
from pathlib import Path
import logging
import sys

# logging
logging.basicConfig(
    level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s"
)

digits = 6
epsilon = 1.0e-5
formatstr = "%12.6f"


class Asset:
    """
    Dataframe for a single crpto asset.
    This class will modify the main crypto dataframe, so df must be returned from dispos_all()
    Inputs are the main crypto dataframe (df), the asset type (coin), and the disposition policy (policy)
    Outputs are in the form of cache and output files 
    """

    def __init__(self, df, coin, policy):
        """
        Initialize asset class.
        Known transaction types are classified into buys and sells.
        There are certainly other transaction types unknown to me yet.
        """
        self.df = df
        self.asset = coin
        self.policy = policy
        df_asset = df[df["Asset"] == coin]
        self.df_asset = df_asset
        self.sells = self.get_sells()
        self.buys = self.get_buys()
        self.idx_sell = 0
        self.idx_buy = 0

    def get_sells(self):
        """return all sells of an asset"""
        is_sell = self.df_asset["Transaction Type"] == "Sell"
        is_ats = self.df_asset["Transaction Type"] == "Advanced Trade Sell"
        sells = self.df_asset[is_sell | is_ats]
        return sells

    def get_buys(self):
        """return all buys of an asset"""
        is_buy = self.df_asset["Transaction Type"] == "Buy"
        is_atb = self.df_asset["Transaction Type"] == "Advanced Trade Buy"
        is_income = self.df_asset["Transaction Type"] == "Rewards Income"
        is_earned = self.df_asset["Transaction Type"] == "Coinbase Earn"
        is_received = self.df_asset["Transaction Type"] == "Receive"
        buys = self.df_asset[is_buy | is_atb | is_income | is_earned | is_received]
        return buys

    def unused(self, row):
        """return unused amount of a transaction, buy or sell"""
        unused = round(self.df.loc[row, "Quantity Transacted"], digits) - round(
            self.df.loc[row, "Used"], digits
        )
        return unused

    def allused(self, row):
        """
        Test whether a row's transations have been used up.
        This will be the case if the Used column equals the quantity transacted
        Allow a small margin to account for roundoff error
        """
        unused = self.unused(row)
        if unused <= epsilon:
            return True
        else:
            logging.debug(
                "not yet all used. unused = "
                + str(unused)
                + "Quantity Transaction = "
                + str(round(self.df.loc[row, "Quantity Transacted"], digits))
                + ", Used = "
                + str(round(self.df.loc[row, "Used"], digits))
            )
            return False

    def getrows(self, df):
        """Return the index values for a Pandas dataframe"""
        rows = df.index.values
        return rows

    def find_next_sell(self):
        """Return the row index of the next sell that is not all used"""
        sellrows = self.getrows(self.sells)
        sellrow = sellrows[self.idx_sell]
        while self.allused(sellrow):
            self.idx_sell = self.idx_sell + 1
            if self.idx_sell == len(sellrows):
                break
            sellrow = sellrows[self.idx_sell]
        return sellrow

    def find_nex_buy(self, buys):
        """Return the row index of the next buy that is not all used"""
        buyrows = self.getrows(buys)
        buyrow = buyrows[self.idx_buy]
        while self.allused(buyrow):
            self.idx_buy = self.idx_buy + 1
            if self.idx_buy == len(buyrows):
                break
            buyrow = buyrows[self.idx_buy]
        return buyrow

    def match_transaction(self, sellrow, buyrow):
        """
        Given a sell row and buy row, use up the smaller of
        the unused portion of the buy or the unused portion of the sell.
        Update the Used column for both rows.
        Returns a dataframe row for the disposition
        """
        available = self.unused(buyrow)
        needed = self.unused(sellrow)
        if available == needed:
            self.df.loc[buyrow, "Used"] = self.df.loc[buyrow, "Quantity Transacted"]
            self.df.loc[sellrow, "Used"] = self.df.loc[sellrow, "Quantity Transacted"]
            boughtfor = self.df.loc[buyrow, "Spot Price at Transaction"] * available
            soldfor = self.df.loc[sellrow, "Spot Price at Transaction"] * needed
        elif available < needed:
            self.df.loc[buyrow, "Used"] = self.df.loc[buyrow, "Quantity Transacted"]
            self.df.loc[sellrow, "Used"] = self.df.loc[sellrow, "Used"] + available
            boughtfor = self.df.loc[buyrow, "Spot Price at Transaction"] * available
            soldfor = self.df.loc[sellrow, "Spot Price at Transaction"] * available
        else:
            self.df.loc[sellrow, "Used"] = self.df.loc[sellrow, "Quantity Transacted"]
            self.df.loc[buyrow, "Used"] = self.df.loc[buyrow, "Used"] + needed
            boughtfor = self.df.loc[buyrow, "Spot Price at Transaction"] * needed
            soldfor = self.df.loc[sellrow, "Spot Price at Transaction"] * needed
        heldfor = self.df.loc[sellrow, "datetime"] - self.df.loc[buyrow, "datetime"]
        d = {
            "Asset": self.asset,
            "Date Acquired": self.df.loc[buyrow, "datetime"],
            "Date Disposed": self.df.loc[sellrow, "datetime"],
            "Sale Price": soldfor,
            "Basis": boughtfor,
            "Gain": soldfor - boughtfor,
        }
        df_dispos = pd.DataFrame(data=d, index=[0])
        return df_dispos

    def get_oldbuys(self, sellrow):
        """
        Find all buys older than the current sellrow.
        Apply the desired policy to sort the oldbuys in order of:
          purchase (FIFO, default)
          sale (LIFO)
          amount (HIFO)
        Returns a sorted oldbuys dataframe
        """
        oldbuys = self.buys[self.buys["datetime"] < self.sells.loc[sellrow].datetime]
        if self.policy == "LIFO":
            oldbuys.sort_values(by="datetime", ascending=False, inplace=True)
        elif self.policy == "HIFO":
            oldbuys.sort_values(
                by="Spot Price at Transaction", ascending=False, inplace=True
            )
        elif self.policy == "FIFO":
            # no action needed for FIFO
            pass
        else:
            # raise an exception for unknown policy
            pass
        return oldbuys

    def match_one_sell(self, df_dispos, sellrow):
        """
        Match all buys necessary to use up the current sell row.
        It may be that less than one complete buy is needed.
        Return an updated disposition dataframe.
        """
        oldbuys = self.get_oldbuys(sellrow)
        self.idx_buy = 0
        buyrow = self.find_nex_buy(oldbuys)
        while self.idx_buy < len(oldbuys) and not self.allused(sellrow):
            logging.debug(
                self.asset + ": sellrow = " + str(sellrow) + ", buyrow = " + str(buyrow)
            )
            df_tmp = self.match_transaction(sellrow, buyrow)
            df_dispos = df_dispos.append(df_tmp)
            buyrow = self.find_nex_buy(oldbuys)
        return df_dispos

    def dispose(self):
        """
        Loop through all sell rows and match it with old buys.
        Each match becomes a row in a disposition dataframe.
        """
        df_dispos = pd.DataFrame()
        if len(self.sells) == 0:
            return self.df, df_dispos
        sellrow = self.find_next_sell()
        while self.idx_sell < len(self.sells):
            df_dispos = self.match_one_sell(df_dispos, sellrow)
            sellrow = self.find_next_sell()
        return self.df, df_dispos


class Crypto:
    """
    A class for holding a complete report of cryptocurrenty transactions.
    Inputs are a file (assumed to be in the data folder), and a disposition policy.
    The main methods are dispos_all() which creates output and dispos files,
    and dispos_summary() which prints a gain/loss summary.
    """

    def __init__(self, file, policy):
        self.infile = os.path.join("../data", file)
        self.cachefile = os.path.join(
            "../data", "cache", Path(file).stem + "_cache.csv"
        )
        self.outfile = os.path.join("../output", Path(file).stem + "_report.csv")
        self.policy = policy

    def clear_cache(self):
        """clear the cache associated with the provided input file"""
        if os.path.exists(self.cachefile):
            os.remove(self.cachefile)
            logging.info("cleared " + self.cachefile)

    def clear_output(self):
        """remove disposition file associated with the provided input file"""
        if os.path.exists(self.outfile):
            os.remove(self.outfile)

    def readfile(self):
        """
        Read a csv report of cryptocurrency transactions.
        Currently assume that there are enough buys to completely
        satisfy every sell. This may not be the case if a partial
        report was generated (such as from a single year)
        """
        cwd = os.getcwd()
        df = pd.read_csv(self.infile)
        ts = df["Timestamp"]
        df["datetime"] = ts.apply(dateutil.parser.isoparse)
        dt = df["datetime"]
        df["year"] = dt.apply(lambda x: x.year)
        return df

    def readcache(self, df):
        """
        Read a cached version of the transactions report, if one exists.
        The cached version will have a Used column that keeps track of
        how much each transaction has been accounted for.
        """
        if os.path.exists(self.cachefile):
            df_cache = pd.read_csv(self.cachefile)
            df_cache["datetime"] = pd.to_datetime(df_cache["datetime"])
            df_cache = df_cache[["datetime", "Used"]]
            df = df.merge(
                df_cache,
                suffixes=(None, "_y"),
                how="right",
                on="datetime",
                validate="one_to_one",
            )
            df[df["Used"].isnull()] = 0.0
        else:
            df.insert(len(df.columns), "Used", 0)
        return df

    def dispose_all(self):
        """
        Loop through all asset types and dispose each.
        Save the cached version of the transaction report.
        Save the output file, which should be appropriate to use
        in your tax return.
        """
        df = self.readfile()
        df = self.readcache(df)
        df_dispos = pd.DataFrame()
        coins = pd.unique(df["Asset"])
        for coin in coins:
            asset = Asset(df, coin, self.policy)
            df, df_tmp = asset.dispose()
            df_dispos = df_dispos.append(df_tmp)
        df.to_csv(self.cachefile, index=False, float_format=formatstr)
        if len(df_dispos) > 0:
            df_dispos.to_csv(self.outfile, index=False, float_format=formatstr)


class Disposition:
    """
    A class for the cryptocurrency disposition report.
    This file must be written from the Crypto class before
    being read here.
    Call summary to summarize the gains for each year for all assets.
    """

    def __init__(self, file):
        """read disposition file and set summary text file name"""
        self.file = file
        self.summaryfile = os.path.join("../output", Path(file).stem + "_summary.txt")
        if os.path.exists(file):
            df = pd.read_csv(file)
            df["Date Disposed"] = pd.to_datetime(df["Date Disposed"])
            df["Date Acquired"] = pd.to_datetime(df["Date Acquired"])
            dt = df["Date Disposed"]
            df["year"] = dt.apply(lambda x: x.year)
            self.df = df

    def clear_summary(self):
        """remove summary file associated with the provided disposition file"""
        if os.path.exists(self.summaryfile):
            os.remove(self.summaryfile)

    def gains(self, df):
        """compute net gains over all rows of a dataframe"""
        duration = df["Date Disposed"] - df["Date Acquired"]
        islongterm = duration >= pd.Timedelta(365, "D")
        gains_longterm = sum(df[islongterm].Gain)
        gains_shortterm = sum(df[~islongterm].Gain)
        return gains_longterm, gains_shortterm

    def write(self, df):
        """write long term and short term summary spreadsheets"""
        year = df.iloc[1]["year"]
        duration = df["Date Disposed"] - df["Date Acquired"]
        islongterm = duration >= pd.Timedelta(365, "D")
        df_longterm = df[islongterm]
        df_shortterm = df[~islongterm]
        file_longterm = os.path.join("../output", "longterm_" + str(year) + ".csv")
        file_shortterm = os.path.join("../output", "shortterm_" + str(year) + ".csv")
        df_longterm.to_csv(file_longterm, index=False, float_format=formatstr)
        df_shortterm.to_csv(file_shortterm, index=False, float_format=formatstr)

    def print_summary(self, file, coin, gains_longterm, gains_shortterm):
        """print one line of disposition summary"""
        print(
            coin
            + ", long term gains = "
            + str(round(gains_longterm, digits))
            + ", short term gains = "
            + str(round(gains_shortterm, digits)),
            file=file,
        )

    def summary(self):
        """Read the dispos file and summarize all gains and losses"""
        years = pd.unique(self.df["year"])
        with open(self.summaryfile, "w") as f:
            for year in years:
                print("Profit/Loss Summary, " + str(year), file=f)
                df_year = self.df[self.df["year"] == year]
                self.write(df_year)
                coins = pd.unique(df_year["Asset"])
                for coin in coins:
                    dfasset = df_year[df_year["Asset"] == coin]
                    gains_longterm, gains_shortterm = self.gains(dfasset)
                    self.print_summary(f, coin, gains_longterm, gains_shortterm)
                # total gains for year
                gains_longterm, gains_shortterm = self.gains(df_year)
                self.print_summary(f, "Total", gains_longterm, gains_shortterm)


def listfiles():
    files = {}
    datapath = "../data"
    dirs = glob.glob(datapath + "/*.csv")
    for idx, file in enumerate(dirs):
        print(idx, file)
        files[idx] = Path(file).name
    idx = len(files)
    files[idx] = "exit"
    print(idx, files[idx])
    return files


def selection():
    option = pyip.inputNum("Select a file, or exit:  ")
    return option


def main(args):
    parser = argparse.ArgumentParser(
        description="Process crypto taxes from transaction report"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-c", "--clear", action="store_true", help="clear cache and output files"
    )
    group.add_argument(
        "-p",
        "--policy",
        type=str,
        choices=["HIFO", "FIFO", "LIFO"],
        help="disposition policy: HIFO (default), FIFO, LIFO",
    )
    args = parser.parse_args()

    if args.policy is not None:
        policy = args.policy
    else:
        policy = "HIFO"

    if args.clear:
        print("Clear cache")
        files = listfiles()
        option = selection()

        if files[option] != "exit":
            file = files[option]
            crypto = Crypto(file, policy)
            crypto.clear_cache()
            crypto.clear_output()
    else:
        print("Dispose transactions")
        files = listfiles()
        option = selection()

        if files[option] != "exit":
            file = files[option]
            crypto = Crypto(file, policy)
            crypto.dispose_all()
            dispos = Disposition(crypto.outfile)
            dispos.clear_summary()
            dispos.summary()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
