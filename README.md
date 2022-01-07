# Introduction
Two things are certain, death and taxes. And that crypto goes up. And that crypto goes down. C'est la vie I suppose. If you're like me, you reviewed the last year of crypto trades and saw a lot more than you remembered. While there are fine online tools for calculating gains and taxes on your crypto holding, their free tier usually only include 100, maybe 200 trades. That's why I wrote this little program to compute the necessary data to fill out IRS orm 8949.

It should be said up front that I am neither a tax professional nor a cryptocurrency professional nor a professional programmer. I am an engineer with lots of years of software under my belt - enough to have fun on projects like this. Use at your own risk. Better yet, contribute to the repository and help make it better.
# Usage
I use Coinbase and this was developed using a Coinbase transaction report. See the todo section below for possible limitations and caveats.
Drop your transaction report, a csv file, into the data folder. From the src folder type
```python
python crypto.py
```
Options include `-c` or `--clear` to clear the cache and `-p` or `--policy` to set the calculation method. For help type
```python
python crypto.py -h
```
The program will show a selection of all csv files in the data folder and prompt you to select one. Select your by typing in the item number. The file will be processed and two files will be generated in the output folder. One is a disposition csv file - this is where you will pull data for your IRS form 8949. The second is a summary text file that shows gains/losses, long term and short term, in a brief format.
## Policies
The basic approach is always the same. For every sale of an asset, select a prior buy of that asset and match it against the sale, coin for coin. There are different methods for doing this that have ramifications on the resulting long term and short term gains. 
* LIFO. Last In First Out. Match coins starting with the last purchase, going back in time as needed.
* FIFO. First In First Out. Match coins starting with the first purchase, moving forward in time as needed.
* HIFO. Highest In First Out. Match coins starting with the largest purches, moving to next-largest, and so on, as needed.
The purchase price is called the basis. The gain (or loss) for each pair of transactions is the sale price minus the basis. Rarely will a buy transaction match the number of coins in a sale exactly. Therefore, it's necessary to match a portion of a purchase with a sale, or vice-versa. Each transaction matched pair will have a buy date and a sell date. It qualifies as a long term gain (or loss) if the difference is at least one year.

see [this article](https://cryptotrader.tax/blog/cryptocurrency-tax-calculations-fifo-and-lifo-costing-methods-explained) for a discussion on which is the best policy to use. 
## Cached Data
The program creates a cached version of the transaction report with a Used column. The purpose of this column is to keep track of which transactions have been used in the tax calculations and whether the used portion represents the complete transaction or some part. The idea is that this cached file can hang around until next year, and that calculation can build upon the cached data.

Keeping this cached version around is really only important if you want to change your policy (LIFO, FIFO, HIFO) from one year to the next. If you don't want to change from year to year, you can just process a multi-year transaction report, essentially re-doing previous years' calculations.
# Tests
There is a test data file in the data folder and a set of tests in the tests folder. Run tests from the src folder with the command
```python
pytest
```
# Todo
Some folks have much more complicated cryto histories than me. I've not accounted for all the possibilities in my program. Some of the limitations and desired features are listed here.
* If crypto was send from one account to another the basis will not be computed correctly because the transaction report will not have the original purchase. The current workaround is to manually edit the report, or manually merge transaction reports from multiple accounts or exchanges.
* This program was designed around a Coinbase transaction report. I have no idea what such reports look like from other exchanges and sites.
* I considered one transaction type as a sell: Sell
* I considered four transaction types as buys: Buy, Rewards Income, Coinbase Earn, Receive.
* There may be other transaction types I've not seen
