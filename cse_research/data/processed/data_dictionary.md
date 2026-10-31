# CSE Cleaned Dataset Data Dictionary (`cse_clean`)

| Column Name | Data Type | Units / Format | Description | Modelling Status |
|---|---|---|---|---|
| `date` | String | `YYYY-MM-DD` | CSE official trading date. Verified unique and strictly monotonic. | Index / Feature |
| `aspi` | Float | Index Points | All Share Price Index closing level. Base year 1985 = 100. | Reconstructed Level (Rule R4) |
| `sp20` | Float | Index Points | S&P Sri Lanka 20 Index closing level. Inception date 2012-06-27. NaN prior to inception. | Feature (Post-2012) |
| `has_sp20` | Boolean | `True` / `False` | Indicator whether S&P SL 20 is active and populated on date $t$. | Feature / Filter |
| `turnover_equity_mn` | Float | Millions LKR | Daily equity market turnover (excludes debt and mutual funds). | Feature |
| `shares_traded_equity_k` | Float | Thousands Shares | Number of equity shares traded during the trading session (in thousands). | Feature |
| `aspi_log_return` | Float | Log Return | One-day ASPI log return: $r_t = \ln(	ext{ASPI}_t / 	ext{ASPI}_{t-1})$. $r_0 = 	ext{NaN}$. | Primary Modelling Target |
