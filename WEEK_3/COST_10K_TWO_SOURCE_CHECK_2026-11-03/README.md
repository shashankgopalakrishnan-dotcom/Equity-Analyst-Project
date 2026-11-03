# Costco latest 10-K: two-source check

**Financial Datasets key:** Valid. The filings endpoint returned HTTP 200 with the professor key in the `X-API-KEY` header. The key is not saved in this folder. Two authenticated filings requests were made during validation and output capture; current plan usage was not checked.

**Financial Datasets record:** Form 10-K; filing date 2026-10-07; report date 2026-08-30; accession `0000909832-26-000093`; URL: https://www.sec.gov/Archives/edgar/data/909832/000090983226000093/cost-20260830.htm.

**SEC EDGAR record:** Form 10-K; filing date 2026-10-07; report date 2026-08-30; accession `0000909832-26-000093`; document download HTTP 200.

**Comparison:** Accession number and filing date match.

**Source limitation:** Financial Datasets returned filing metadata and a URL on sec.gov. It did not return a separate copy of the 10-K body in this endpoint. The saved HTML and text were downloaded from SEC EDGAR. The test confirms that the vendor key can access its filings endpoint and that both sources identify the same latest 10-K.

**Downloaded SEC document:** 1456596 bytes; SHA-256 `79bd633964563c7c5826db591a370d0ff5236340e31ed3649cce020543c975ed`.
