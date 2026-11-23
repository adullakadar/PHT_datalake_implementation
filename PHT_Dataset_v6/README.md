# Piplodwala Hardware Trading LLC (PHT) – Simulated Dataset v6 (TallyPrime export formats)

All records are **synthetic**, for an academic case study. The **file formats follow PHT's real TallyPrime vouchers** (sales invoice, quotation, purchase invoice, stock journal transfer, list of stock items). The values are invented, and customer and supplier names are fictional.

Regenerate (≈45 s, Python 3.4+ standard library): `python3 generate_data.py` → `./data/`

## Scenario
| Location | Opened | Tally setup |
|---|---|---|
| SHJ1 – Sharjah 1 (main) | Jul 2019 | TallyPrime server + clients. Also books the **Main Warehouse** godown |
| WH1 – Main Warehouse | Jul 2019 | Godown inside SHJ1's Tally only |
| DB1 – Dubai 1 | Apr 2021 | TallyPrime on a single PC |
| SHJ2 – Sharjah 2 | Feb 2023 | TallyPrime server + clients |
| AJM1 – Ajman | provisional | joins the data lake (streaming scenario) |

Each branch runs its **own** Tally. Masters (items, ledgers) are **unified** (same names everywhere), but transactions live in separate systems that aren't connected. Shops are open Mon–Sat, 8–1 and 3–7, with a COVID dip in 2020.

## Headline figures (`data/summary.json`)
| | |
|---|---|
| Items in master | ~42,200, including ~4,600 **one-off "SPECIAL" items** created for customer special requests (repeat requests reuse the same item) |
| Sales invoices / lines | ~197,000 / ~400,000 |
| Customers per day | 28 (2019) → 57 (2021) → 96 (2023) → 132 (2025) → **~149 (Aug–Oct 2026)** |
| Quotations / lines | ~108,000 / ~284,000. About 42,000 (~39%) converted (invoice `Other References` = quote no.) |
| Stock transfer lines / pink slips | ~212,500 / ~10,400 |
| Transfer receipts never entered / qty mismatch | ~3,000 / ~1,900 |
| Purchase invoice lines | ~164,000 |
| Revenue 2025 | ~AED 13.1M (Ajman-based customers ≈ 12%) |
| Size | ~445 MB |

## Folder layout
```
data/
  locations.csv
  tally_exports/<SHJ1|DB1|SHJ2>/
      ListOfStockItems_<BR>.csv          Sl. No., Name of Item, Under, Units, Opening Qty, Rate, per, Opening Balance
      ListOfLedgers_<BR>.csv             customers (Sundry Debtors) + suppliers in SHJ1 (Sundry Creditors), with TRN
      sales/SalesInvoices_<BR>_YYYY_MM.csv
      quotations/Quotations_<BR>_YYYY_MM.csv
      stock_journal/StockJournal_<BR>_YYYY_MM.csv
      stock_summary/GodownSummary_<BR>_<date>.csv     year-ends + Aug/Sep/Oct 2026 month-ends
  tally_exports/SHJ1/purchases/PurchaseInvoices_SHJ1_YYYY_MM.csv
  stream/events_2027-02-01/events_HHMM.csv + opening_stock_2027-02-01.csv    (Ajman opening-day live feed)
  reference/   answer keys (NOT lake input): products, customers, suppliers, transfers_truth, stream_expected_alerts
```

## Formats (one CSV row per item line; voucher header repeated on every line)
**Sales invoice / Quotation (43 columns):** Voucher Type, Voucher Mode, Voucher No, Date, Effective Date, Reference No/Date (customer LPO), Party Ledger, Buyer Name/Address/Emirate/Country/TRN, Consignee Name/Address, Delivery Note No/Date, Dispatch Doc No, Dispatched Through, Destination, Carrier, Bill of Lading, Motor Vehicle No, Sales Order No/Date, Mode/Terms of Payment, Other References, Terms of Delivery, Port of Loading/Discharge, Shipping Bill No, **Name of Item, Item Description, Godown, Actual Qty, Billed Qty, Rate, per, Disc %, Amount, VAT %, VAT Amount**, Narration.
Quotations use Voucher Type `Quotation`.

**Purchase invoice (27 columns):** Voucher No, Date (entered 0–5 days after the goods arrive), Supplier Invoice No/Date, Party Ledger (supplier), Supplier Address/Country/TRN, Receipt Note No/Date, Order No/Date (PO), Terms, item columns as above, Godown = `Main Warehouse`.

**Stock journal (transfer):** Voucher Type `Stock Journal`, Voucher Class `Transfer of Materials - Inter Godown`, Voucher No, Date, Day, Destination Godown, Name of Item, Source Godown, Quantity, Rate, per, Amount, Narration.

## Data-management challenges built in (what the lake has to handle)
- **Tally conventions:** dates like `5-Mar-25`, quantities with units (`20 Nos`, `5 Box`, `25 Mtr`), header repeated on every line, many mostly-empty columns (dispatch, export, sales order).
- **Every transfer is recorded twice, in two separate Tallys.** The sender books `own showroom → "<Dest> Branch"` and the receiver books `"<Sender> Branch" → own showroom`, 0–3 days after arrival. About 3% of receipts are missing and about 2% have the wrong quantity. Narrations quote the pink slip (`PS#003772`) about 70% of the time.
- **Warehouse booked through SHJ1:** warehouse → DB1/SHJ2 appears in SHJ1's Tally as `Main Warehouse → Sharjah 1 Showroom` **and** `Sharjah 1 Showroom → "<Dest> Branch"`. The receiver says it came from `Sharjah 1 Branch`.
- **One-off items:** about 11% of the item master are `SPECIAL …` items under `Special Orders`, bought in for a customer request. Some recur, which makes them candidates for the regular catalogue.
- **Lake item IDs:** Tally has no item codes. The lake numbers items `PHT-00001…` in alphabetical order of item name, and the stream and reference files use the same IDs.
- **Actual vs Billed Qty:** occasionally differ (free extra units). Purchases are occasionally short-delivered.
- **Quote → invoice link** only exists through `Other References` on the invoice.
