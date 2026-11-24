# Synthetic Data Dictionary

- `instruments.csv`: 164 instruments (`PERP`, `CALL`, `PUT`), strike in USD, contract multiplier, and synthetic expiry day.
- `marks.csv`: 29,520 instrument-day observations containing `mid`, `bid`, `ask` in USD, annualized implied volatility (`iv`), `stale` flag, and `source`. Marks represent synthetic market snapshots rather than live exchange feeds.
- `index.csv`: 720 synthetic index price values indexed by `day` and `underlying`.
- `events.csv`: 4,763 chronological account events (`deposit`, `fill`, `funding`). Note that raw fills represent unilateral synthetic events rather than matched two-sided counterparty trades.
- `manifest.json`: dataset seed, coverage metrics, and chronological partition windows (`train`: days 0–89; `validation`: days 90–134; `test`: days 135–179).

Note: Options with `expiry_day <= current_day` require explicit settlement and closure prior to accepting subsequent trade requests.
