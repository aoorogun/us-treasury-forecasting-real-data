# Data sources and provenance

The project downloads public observations using FRED's graph CSV endpoint and stores each series separately with its exact URL, row count and SHA-256 checksum in `data/raw/source_manifest.json`.

| ID | Description | Original source | Units |
|---|---|---|---|
| DGS3MO | 3-month Treasury constant maturity rate | Federal Reserve Board, H.15 | Percent, daily |
| DGS2 | 2-year Treasury constant maturity rate | Federal Reserve Board, H.15 | Percent, daily |
| DGS10 | 10-year Treasury constant maturity rate | Federal Reserve Board, H.15 | Percent, daily |
| DGS30 | 30-year Treasury constant maturity rate | Federal Reserve Board, H.15 | Percent, daily |
| DFF | Effective federal funds rate | Federal Reserve Bank of New York | Percent, daily |
| DFII10 | 10-year inflation-indexed Treasury yield | Federal Reserve Board, H.15 | Percent, daily |
| T10YIE | 10-year breakeven inflation rate | Federal Reserve Bank of St. Louis | Percent, daily |
| VIXCLS | CBOE Volatility Index | CBOE | Index, daily close |

Series pages and suggested citations:

- https://fred.stlouisfed.org/series/DGS3MO
- https://fred.stlouisfed.org/series/DGS2
- https://fred.stlouisfed.org/series/DGS10
- https://fred.stlouisfed.org/series/DGS30
- https://fred.stlouisfed.org/series/DFF
- https://fred.stlouisfed.org/series/DFII10
- https://fred.stlouisfed.org/series/T10YIE
- https://fred.stlouisfed.org/series/VIXCLS

## Reproducibility and revision caveat

The committed snapshot is bounded to 1 January 2004–31 December 2024. FRED series can be corrected or revised, so downloading the same date range later may not reproduce every byte. The manifest identifies the exact bundled files used by the model. This is not a true vintage/ALFRED dataset and should not be described as one.

The Treasury rates are public-domain data for which citation is requested. Some downstream series, notably VIX, carry source-specific copyright/citation terms. This educational repository preserves attribution and does not claim ownership.

