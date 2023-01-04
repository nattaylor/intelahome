# Intelahome

Retrieve Intelahome structured electricity usage and demand data

Run `help(Intelahome)` for help.


## Usage

To get a dictionary of observations keyed by time:

```
>>> %env CREDS=login=user%40domain.com&password=abc123
>>> I = Intelahome()
>>> I.report('UsageReport')
{'2023-01-02T16:00:00': 0.123}
```
