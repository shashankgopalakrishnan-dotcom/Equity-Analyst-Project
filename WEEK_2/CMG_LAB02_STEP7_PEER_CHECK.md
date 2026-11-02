# CMG Lab 02 Step 7 — Peer filing check

**Checked:** 2026-11-02
**Definition:** GAAP operating income (or the issuer's equivalent GAAP operating profit) divided by GAAP total revenue.
**Result:** All three peer figures match their latest 10-K statements. Numerator and denominator use the same fiscal year for each company.

| Ticker | Latest 10-K | Fiscal period | Revenue (statement line) | Operating income (statement line) | Calculation | Result |
|---|---|---|---:|---:|---:|---:|
| MCD | Accession `0000063908-26-000035`, filed 2026-02-24 | Year ended 2025-12-31 | $26,885 million (`10k.txt` line 00808) | $12,393 million (`10k.txt` line 00821) | $12,393m / $26,885m | 46.10% |
| YUM | Accession `0001041061-26-000084`, filed 2026-02-20 | Year ended 2025-12-31 | $8,214 million (`10k.txt` line 01083) | $2,574 million (`10k.txt` line 01092) | $2,574m / $8,214m | 31.34% |
| CAVA | Accession `0001628280-26-011296`, filed 2026-02-25 | Fiscal year ended 2025-12-28 | $1,179,664 thousand (`10k.txt` line 01156) | $55,285 thousand (`10k.txt` line 01170) | $55,285k / $1,179,664k | 4.69% |

The 10-K text files are saved under `WEEK_2/runs/CHIPOTLE_MEXICAN_GRILL_INC_20261101_101158_EST/peers/`:

- `MCDONALDS_CORP/10k.txt`
- `YUM_BRANDS_INC/10k.txt`
- `CAVA_GROUP_INC./10k.txt`

The revenue and operating income values also match the peer facts saved in the corresponding `*_companyfacts.json` files. MCD and YUM use the `Revenues` and `OperatingIncomeLoss` tags. CAVA uses `RevenueFromContractWithCustomerExcludingAssessedTax` and `OperatingIncomeLoss`. The statement values are in millions for MCD and YUM and thousands for CAVA; each calculation uses a consistent unit within that company's numerator and denominator.

Operating margins are now calculated with one definition. The business models differ: MCD and YUM have substantial franchised operations, while CAVA operates company restaurants. The same formula satisfies the Lab 02 comparison check, but the margins do not represent identical economics.

## SEC filing sources

- [MCD 2025 10-K filing index](https://www.sec.gov/Archives/edgar/data/63908/000006390826000035/0000063908-26-000035-index.html) · [10-K](https://www.sec.gov/Archives/edgar/data/63908/000006390826000035/mcd-20251231.htm)
- [YUM 2025 10-K filing index](https://www.sec.gov/Archives/edgar/data/1041061/000104106126000084/0001041061-26-000084-index.html) · [10-K](https://www.sec.gov/Archives/edgar/data/1041061/000104106126000084/yum-20251231.htm)
- [CAVA 2025 10-K filing index](https://www.sec.gov/Archives/edgar/data/1639438/000162828026011296/0001628280-26-011296-index.html) · [10-K](https://www.sec.gov/Archives/edgar/data/1639438/000162828026011296/cava-20251228.htm)
