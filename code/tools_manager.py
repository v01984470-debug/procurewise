import pandas as pd
from typing import Optional, List, Union
from datetime import datetime

global_import_duties_df = None

def _parse_percent(s: str) -> float:
    try:
        return float(s.strip().rstrip("%"))
    except:
        return 0.0

import pandas as pd
from datetime import datetime, date, timedelta

def analyze_po_requirements(po_number: str) -> str:
    output = ""
    print("po_number", po_number)
    # 1. Load CSVs
    po_df   = pd.read_csv('./updated_docs/Open_PO_data.csv', dayfirst=True)
    prod_df = pd.read_csv('./updated_docs/Production_data.csv', dayfirst=True)
    inv_df  = pd.read_csv('./updated_docs/Inventory_data.csv', dayfirst=True)

    # 2. Coerce numeric columns
    prod_df['Qnty planned'] = pd.to_numeric(prod_df['Qnty planned'], errors='coerce')
    inv_df['Qty']            = pd.to_numeric(inv_df['Qty'], errors='coerce')

    # 3. Select target PO
    target_po = po_df[po_df['PO number'] == po_number]
    if target_po.empty:
        return f"No PO found with number {po_number}\n"

    # 4. Region‑prefix helper
    def region_prefix(loc: str):
        return loc.split('/')[0].strip().lower()

    ship_pref = region_prefix(target_po.iloc[0]['Shipping location'])
    to_pref   = region_prefix(target_po.iloc[0]['Ship to Location'])

    print("ship_pref", ship_pref)
    print("to_pref", to_pref)

    # 5. Filter POs by region
    region_po = po_df[
        po_df['Shipping location'].str.lower().str.startswith(ship_pref)
        & po_df['Ship to Location'].str.lower().str.startswith(to_pref)
    ]

    # 6. Parse production dates
    for col in ['Production start date', 'Production end date']:
        prod_df[col] = pd.to_datetime(prod_df[col], dayfirst=True, errors='coerce')
        prod_df[col] = prod_df[col].dt.strftime('%d-%m-%Y')

    print("prod_df", prod_df)

    # 7. Identify POs with June production requirements
    prod_matches = []  # list of PO numbers with June production
    first_rate = None
    first_qty  = None

    for _, po_row in region_po.iterrows():
        desc = po_row['Item Description'].strip().lower()
        m = prod_df[prod_df['SKU desc'].str.strip().str.lower() == desc].copy()
        print("m SKU desc", m)
        m['__start_dt'] = pd.to_datetime(m['Production start date'], dayfirst=True, errors='coerce')
        m['__end_dt']   = pd.to_datetime(m['Production end date'], dayfirst=True, errors='coerce')
        m = m[(m['__start_dt'].dt.month == 6) | (m['__end_dt'].dt.month == 6)]
        if not m.empty:
            prod_matches.append(po_row['PO number'])

    # 8. List non-immediate POs by number
    non_immediate = [po for po in region_po['PO number'] if po not in prod_matches and po != po_number]
    if non_immediate:
        output += "PO(s) without immediate June production requirement: " + ", ".join(non_immediate) + "\n\n"

    # 9. Filter to only immediate POs
    immediate_po = region_po[region_po['PO number'].isin(prod_matches)]
    if immediate_po.empty:
        return output + "No POs with immediate production requirements in June."

    output += "**PO(s) with immediate June production requirement (filtered by region):**\n"
    output += immediate_po.to_markdown(index=False) + "\n\n"

    # 10. Detail production requirements and calculate rates
    for _, po_row in immediate_po.iterrows():
        desc = po_row['Item Description'].strip().lower()
        m = prod_df[prod_df['SKU desc'].str.strip().str.lower() == desc].copy()
        print("m SKU desc", m)
        m['__start_dt'] = pd.to_datetime(m['Production start date'], dayfirst=True, errors='coerce')
        m['__end_dt']   = pd.to_datetime(m['Production end date'], dayfirst=True, errors='coerce')
        m = m[(m['__start_dt'].dt.month == 6) | (m['__end_dt'].dt.month == 6)]
        output += f"**Production for {po_row['Item Number']} – {po_row['Item Description']}:**\n"
        output += m.drop(columns=['__start_dt','__end_dt']).to_markdown(index=False) + "\n\n"
        for _, r in m.iterrows():
            qty_req = r['Qnty planned']
            start   = pd.to_datetime(r['Production start date'], dayfirst=True)
            end     = pd.to_datetime(r['Production end date'], dayfirst=True)
            total_days = (end - start).days + 1 if pd.notna(start) and pd.notna(end) else None
            rate = qty_req / total_days if total_days and total_days > 0 else float('nan')
            output += f"- Quantity required: **{qty_req}**\n"
            output += f"- Start date: **{start.strftime('%d-%m-%Y')}**\n"
            output += f"- End date: **{end.strftime('%d-%m-%Y')}**\n"
            output += f"- Total days: **{total_days}**\n"
            output += f"- Requirement per day: **{rate:.2f}**\n\n"
            if first_rate is None and pd.notna(rate):
                first_rate = rate
                first_qty  = qty_req

    # 11. Inventory check for first immediate PO
    first_po = prod_matches[0]
    item_num = immediate_po[immediate_po['PO number'] == first_po].iloc[0]['Item Number']
    inv_filt = inv_df[
        (inv_df['Item Number'] == item_num) &
        (inv_df['Stock Ownership Basis (SOB)'] == 'Own Stock') &
        (inv_df['Country'] == 'US')
    ]
    if inv_filt.empty:
        return output + "No matching 'Own Stock' US inventory found."

    output += "**Inventory for item:**\n"
    output += inv_filt.to_markdown(index=False) + "\n\n"

    qty_on_hand = inv_filt.iloc[0]['Qty']
    if first_rate is None or first_rate <= 0 or pd.isna(first_rate):
        return output + "Undefined daily requirement rate; cannot compute sufficiency."

    reference_date = date(2025, 6, 12)
    days_covered   = (qty_on_hand / first_rate) - 1
    suffice_until  = reference_date + timedelta(days=days_covered)

    output += f"- On-hand quantity: **{qty_on_hand:.0f}**\n"
    output += f"- Covers **{days_covered:.1f}** days (until {suffice_until.strftime('%d-%m-%Y')})\n"
    output += f"- Additional quantity required: **{max(first_qty - qty_on_hand, 0):.0f}** of ITM-002\n\n"
    output += f"Final Suggestion: Place an order for **{max(first_qty - qty_on_hand, 0):.0f}** units needed by {suffice_until.strftime('%d-%m-%Y')}"

    return output

def get_top_alternative_suppliers(
    item_number: str,
    location: Optional[str] = None,
    metric: str = "capacity_allocation",
    ascending: bool = True,
    top_n: int = 3,
    capacity_csv: str = "./updated_docs/Supplier_capacity_data.csv",
    supplier_csv: str = "./updated_docs/Supplier_data.csv"
) -> str:
    """
    Returns the top N alternative suppliers for a given item, filtered by location
    and ranked by the specified metric.

    Parameters:
    - item_number: Item code, e.g. "ITM-001".
    - location: Supplier Location filter (country or region substring).
    - metric: One of ["capacity_allocation", "unit_price", "lead_time", "moq"].
    - ascending: Sort order (True = lowest first).
    - top_n: Number of suppliers to return.
    - capacity_csv: Path to ./updated_docs/Supplier_capacity_data.csv.
    - supplier_csv: Path to ./updated_docs/Supplier_data.csv.

    Returns:
    - Markdown table of top suppliers with key columns and chosen metric.
    """
    
    cap = pd.read_csv(capacity_csv)
    sup = pd.read_csv(supplier_csv)

    
    cap['capacity_allocation'] = cap['Percentage allocation to company'].apply(_parse_percent)

    
    df = cap.merge(
        sup[['Item Number','Supplier Name','Supplier Code','Supplier Location',
             'Unit Price (USD)','MOQ','Lead time (Weeks)']],
        left_on=['Item number','Supplier Code'],
        right_on=['Item Number','Supplier Code'],
        how='left'
    )
    df['lead_time'] = df['Lead time (Weeks)'] * 7 



    
    df = df[df['Item number'] == item_number]
    
    print(df.to_csv("suppl_loc.csv"))

    if location:
        df = df[df['Supplier Location_x'].str.contains(location, case=False, na=False)]

    
    if metric not in ['capacity_allocation','unit_price','lead_time','moq']:
        raise ValueError("Metric must be one of capacity_allocation, unit_price, lead_time, moq")
    key = {
        'capacity_allocation':'capacity_allocation',
        'unit_price':'Unit Price (USD)',
        'lead_time':'lead_time',
        'moq':'MOQ'
    }[metric]

    df_sorted = df.sort_values(by=key, ascending=False).head(top_n)
    
    out = df_sorted[[
        'Supplier Name','Supplier Code','Supplier Location_x', 'Manufacturing location/plant name','Item Number', "Item Desc", "Total monthly capacity (units)", "MOQ_x", "Current committed capacity (units)",
        key
    ]]
    return out.to_markdown(index=False)

import pandas as pd

def get_avg_lead_time(
    mode_of_transport: str,
    supplier_code: str,
    item_number: str,
    delivery_location: str,
    csv_path: str = "./updated_docs/Shipment_tracker_data.csv"
) -> Union[float, None]:
    """
    (UNCHANGED from original)
    Reads the CSV at `csv_path` and returns the average 'Lead time (days)'
    for rows matching all four criteria:
      - Mode of Transport   == mode_of_transport
      - Supplier Code       == supplier_code
      - Item Number         == item_number
      - Delivery Location   == delivery_location

    If no matching rows are found, returns None.
    """
    # 1. Read the CSV into a DataFrame, forcing 'Lead time (days)' to float
    df = pd.read_csv(
        csv_path,
        dtype={
            "PO number": str,
            "Item Number": str,
            "Supplier Code": str,
            "Mode of Transport": str,
            "Delivery Location": str,
        },
        converters={"Lead time (days)": lambda x: float(x) if x not in ["", None] else None},
    )

    # 2. Drop any rows where 'Lead time (days)' is missing
    df = df[df["Lead time (days)"].notna()].copy()
    df["Lead time (days)"] = df["Lead time (days)"].astype(float)

    # 3. Filter by the four criteria
    mask = (
        (df["Mode of Transport"] == mode_of_transport) &
        (df["Supplier Code"]    == supplier_code) &
        (df["Item Number"]      == item_number) &
        (df["Delivery Location"]== delivery_location.split('/')[0])
    )
    subset = df.loc[mask]

    # 4. If no matches, return None
    if subset.empty:
        return None

    # 5. Compute and return the mean lead time
    return subset["Lead time (days)"].mean()


def get_open_po_data(
    po_number: str,
    csv_path: str = "./updated_docs/Open_PO_data.csv"
) -> str:
    """
    Reads the CSV at `csv_path` and returns a Markdown-formatted table
    containing all rows where "PO number" == po_number.
    If no matches are found, returns an empty string.
    """
    # 1. Read the CSV, ensuring "PO number" is string
    df = pd.read_csv(
        csv_path,
        dtype={"PO number": str}
    )

    # 2. Filter rows by PO number
    result = df.loc[df["PO number"] == po_number].copy()

    # 3. If no matches, return empty string
    if result.empty:
        return ""

    # 4. Otherwise return the Markdown table string
    return result.to_markdown(index=False)



def expedite_po_by_cost(
    open_po_number: str,
    capacity_csv: str = "./updated_docs/Supplier_capacity_data.csv",
    supplier_csv: str = "./updated_docs/Supplier_data.csv",
    open_po_csv: str = "./updated_docs/Open_PO_data.csv"
) -> str:
    """
    Splits out *only* the Sea-expedite (partial) logic from the original tool.
    Keeps ALL calculations and column names exactly as before.

    Returns a single markdown string containing:
      1. The "Sea Expediting Logic (Partial Expedite)" table (df_sea).
      2. Its original Explanation (verbatim except adjusted for context).
      3. A Final Comparison table with *only* "Baseline Sea" vs. "Partial Expedite"
         (using the exact same columns: ["Scenario","Details","Total Cost (USD)","Lead Time"]).
      4. Its original Explanation (verbatim except trimmed to these two rows).
    """
    # --- Read all required CSVs into DataFrames ---
    df_capacity = pd.read_csv(capacity_csv)    # has columns "Supplier Code", "Item number", "Expedite Qnty possible", "Expedite Lead time", "Premium to expedite", ...
    df_supplier = pd.read_csv(supplier_csv)    # has columns "Supplier Code", "Item Number", "Total Unit Cost with Sea shipping", "Total Unit Cost with Air shipping", "Lead time (Weeks)", ...
    df_openpo   = pd.read_csv(open_po_csv)     # has columns "PO number", "Supplier Code", "Item Number", "Qnty Ordered", "Requested Mode of Transport", "Ship to Location", ...

    # 1. Find the PO row
    df_po = df_openpo[df_openpo["PO number"] == open_po_number]
    if df_po.empty:
        return f"No purchase order found with PO number '{open_po_number}'."
    po = df_po.iloc[0]

    # 2. Extract key fields from the PO
    supplier_code     = po["Supplier Code"]
    item_number       = po["Item Number"]
    qty_ordered       = float(po["Qnty Ordered"])
    # current_mode not used here, but we keep it for parity
    current_mode      = po["Requested Mode of Transport"]
    delivery_location = po.get("Ship to Location", "").strip().split("/")[0]

    # 3. Filter supplier data (to get cost info & lead time in weeks)
    df_sup = df_supplier[
        (df_supplier["Supplier Code"] == supplier_code) &
        (df_supplier["Item Number"]   == item_number)
    ]
    if df_sup.empty:
        return (
            f"No supplier data found for Supplier Code '{supplier_code}', "
            f"Item Number '{item_number}'."
        )
    sup = df_sup.iloc[0]

    # 4. Filter capacity data (to get expedite info)
    df_cap = df_capacity[
        (df_capacity["Supplier Code"] == supplier_code) &
        (df_capacity["Item number"]   == item_number)
    ]
    if df_cap.empty:
        return (
            f"No capacity data found for Supplier Code '{supplier_code}', "
            f"Item Number '{item_number}'."
        )
    cap = df_cap.iloc[0]

    # --- Parse numeric fields from supplier & capacity tables ---
    sea_cost_per_unit = float(sup["Total Unit Cost with Sea shipping"])
    # We do *not* need air costs here—this is purely by-cost/sea logic.

    sea_total_cost = qty_ordered * sea_cost_per_unit

    expedite_max_qty    = float(cap["Expedite Qnty possible"])
    expedite_lead_time  = str(cap["Expedite Lead time"])  # e.g., "2 days"

    # Parse premium per unit from a string like "$1.2/pc"
    prem_str = str(cap["Premium to expedite"])
    premium_per_unit = float(prem_str.replace("$", "").replace("/pc", "").strip())
    premium_per_unit +=50
    # Sea lead time (in weeks) -> represent as string
    lead_time_weeks = sup["Lead time (Weeks)"]
    baseline_lead_time_str = f"{lead_time_weeks} weeks"
    baseline_lead_time_days = float(lead_time_weeks) * 7

    # Calculate non-expedited quantity
    non_expedited_qty = max(qty_ordered - expedite_max_qty, 0)

    # --- Build Sea Expedite Scenario Table (df_sea) exactly as before ---
    expedited_unit_cost = sea_cost_per_unit + premium_per_unit
    total_expedited_cost = expedite_max_qty * expedited_unit_cost
    total_non_expedited_cost = non_expedited_qty * sea_cost_per_unit
    combined_total_cost = total_expedited_cost + total_non_expedited_cost

    df_sea = pd.DataFrame([{
        "Item Number": item_number,
        "Quantity Ordered": int(qty_ordered),
        "Expedite Max Qty": int(expedite_max_qty),
        "Expedite Lead Time": expedite_lead_time,
        "Expedite Premium Per Unit (USD)": premium_per_unit,
        "Expedited Unit Cost (USD)": expedited_unit_cost,
        "Non-Expedited Qty": int(non_expedited_qty),
        "Sea Cost Per Unit (USD)": sea_cost_per_unit,
        "Total Expedited Cost (USD)": total_expedited_cost,
        "Total Non-Expedited Cost (USD)": total_non_expedited_cost,
        "Combined Total Cost (USD)": combined_total_cost
    }])

    # --- Build the Final Comparison Table (df_final_cost) with exactly two rows ---
    df_final_cost = pd.DataFrame([
        {
            "Scenario": "Baseline Sea",
            "Details": f"All {int(qty_ordered)} units via Sea",
            "Total Cost (USD)": sea_total_cost,
            "Lead Time": baseline_lead_time_str
        },
        {
            "Scenario": "Partial Expedite",
            "Details": (
                f"{int(expedite_max_qty)} units expedited "
                f"(premium $ {premium_per_unit:.2f}/unit) @ {expedite_lead_time}; "
                f"{int(non_expedited_qty)} units via Sea @ {baseline_lead_time_str}"
            ),
            "Total Cost (USD)": combined_total_cost,
            "Lead Time": (
                f"{expedite_lead_time} (expedited), "
                f"{baseline_lead_time_str} (remainder)"
            )
        }
    ])

    # --- Build the response string with tables and explanations ---
    response = []

    # 1. Sea Expediting Logic Table (identical to original)
    response.append("**Sea Expediting Logic (Partial Expedite)**")
    response.append(df_sea.to_markdown(index=False))
    response.append("\n**Explanation:**\n")
    response.append(
        "This table illustrates the scenario of expediting a portion of the order via the supplier’s premium expedite process. "
        f"You can expedite up to {int(expedite_max_qty)} units at a premium of $ {premium_per_unit:.2f} per unit, "
        f"bringing the Expedited Unit Cost to $ {expedited_unit_cost:.2f}. The remaining {int(non_expedited_qty)} units ship normally by sea at $ {sea_cost_per_unit:.2f} per unit. "
        f"Total Expedited Cost = $ {total_expedited_cost:.2f}, Total Non-Expedited Cost = $ {total_non_expedited_cost:.2f}, "
        f"Combined Total Cost = $ {combined_total_cost:.2f}. The expedited {int(expedite_max_qty)} units arrive in {expedite_lead_time}, "
        f"while the remaining {int(non_expedited_qty)} units follow the standard sea lead time of {baseline_lead_time_str}."
    )

    # 2. Final Comparison Table (only baseline vs. partial)
    response.append("\n**Final Comparison of Scenarios (Sea-Cost Focus)**")
    response.append(df_final_cost.to_markdown(index=False))
    response.append("\n**Explanation:**\n")
    response.append(
        "This final table compares the two scenarios side by side:\n"
        "1. **Baseline Sea:** No changes— all units ship via sea at the standard sea lead time.\n"
        "2. **Partial Expedite:** Expedite up to the maximum quantity ("
        f"{int(expedite_max_qty)} units) at a premium, reducing lead time for that subset, "
        "while the remainder ships via sea. Combined cost and split lead times are shown."
    )

    return "\n\n".join(response)


def expedite_po_by_lead(
    open_po_number: str,
    capacity_csv: str = "./updated_docs/Supplier_capacity_data.csv",
    supplier_csv: str = "./updated_docs/Supplier_data.csv",
    open_po_csv: str = "./updated_docs/Open_PO_data.csv",
    shipment_tracker_csv: str = "./updated_docs/Shipment_tracker_data.csv"
) -> str:
    """
    Splits out *only* the Air-freight logic from the original tool.
    Keeps ALL calculations and column names exactly as before.

    Returns a single markdown string containing:
      1. The "Air Expediting Logic" table (df_air).
      2. Its original Explanation (verbatim except adjusted for context).
      3. A Final Comparison table with *only* "Baseline Sea" vs. "Air Freight (Full Quantity)"
         (using the exact same columns: ["Scenario","Details","Total Cost (USD)","Lead Time"]).
      4. Its original Explanation (verbatim except trimmed to these two rows).
    """
    # --- Read all required CSVs into DataFrames ---
    df_supplier = pd.read_csv(supplier_csv)
    df_openpo   = pd.read_csv(open_po_csv)

    # 1. Find the PO row
    df_po = df_openpo[df_openpo["PO number"] == open_po_number]
    if df_po.empty:
        return f"No purchase order found with PO number '{open_po_number}'."
    po = df_po.iloc[0]

    # 2. Extract key fields from the PO
    supplier_code     = po["Supplier Code"]
    item_number       = po["Item Number"]
    qty_ordered       = float(po["Qnty Ordered"])
    delivery_location = po.get("Ship to Location", "").strip().split("/")[0]

    # 3. Filter supplier data (to get cost info & lead time in weeks)
    df_sup = df_supplier[
        (df_supplier["Supplier Code"] == supplier_code) &
        (df_supplier["Item Number"]   == item_number)
    ]
    if df_sup.empty:
        return (
            f"No supplier data found for Supplier Code '{supplier_code}', "
            f"Item Number '{item_number}'."
        )
    sup = df_sup.iloc[0]

    # 4. Parse numeric fields from supplier table
    sea_cost_per_unit = float(sup["Total Unit Cost with Sea shipping"])
    air_cost_per_unit = float(sup["Total Unit Cost with Air shipping"])
    incremental_cost_per_unit_air = air_cost_per_unit - sea_cost_per_unit

    sea_total_cost = qty_ordered * sea_cost_per_unit
    air_total_cost = qty_ordered * air_cost_per_unit

    # 5. Build Air Expediting Logic Table (df_air) exactly as before
    df_air = pd.DataFrame([{
        "Item Number": item_number,
        "Quantity Ordered": int(qty_ordered),
        "Sea Cost Per Unit (USD)": sea_cost_per_unit,
        "Air Cost Per Unit (USD)": air_cost_per_unit,
        "Incremental Cost Per Unit Air (USD)": incremental_cost_per_unit_air,
        "Sea Total Cost (USD)": sea_total_cost,
        "Air Total Cost (USD)": air_total_cost
    }])

    # 6. Determine actual Air lead time using Shipment Tracker data
    if delivery_location:
        avg_lead_time_air = get_avg_lead_time(
            mode_of_transport="Air",
            supplier_code=supplier_code,
            item_number=item_number,
            delivery_location=delivery_location
        )
        avg_lead_time_sea = get_avg_lead_time(
            mode_of_transport="Sea",
            supplier_code=supplier_code,
            item_number=item_number,
            delivery_location=delivery_location
        )
        if avg_lead_time_air is None:
            air_lead_time_str = "Not found in data"
        else:
            air_lead_time_str = f"{round(avg_lead_time_air,0)} days"
            sea_lead_time_str = f"{round(avg_lead_time_sea,0)} days"
    else:
        air_lead_time_str = "Delivery location not provided"

    # 7. Sea lead time (in weeks) -> represent as string (for final comparison)
    lead_time_weeks = sup["Lead time (Weeks)"]
    baseline_lead_time_str = f"{lead_time_weeks} weeks"

    # 8. Build the Final Comparison Table (df_final_lead) with exactly two rows
    df_final_lead = pd.DataFrame([
        {
            "Scenario": "Baseline Sea",
            "Details": f"All {int(qty_ordered)} units via Sea",
            "Total Cost (USD)": sea_total_cost,
            "Lead Time": baseline_lead_time_str,
            "Transit Time": sea_lead_time_str
        },
        {
            "Scenario": "Air Freight (Full Quantity)",
            "Details": f"All {int(qty_ordered)} units via Air to {delivery_location}",
            "Total Cost (USD)": air_total_cost,
            "Lead Time": baseline_lead_time_str,
            "Transit Time": air_lead_time_str

        }
    ])

    # --- Build the response string with tables and explanations ---
    response = []

    # 1. Air Expediting Logic Table (identical to original)
    response.append("**Air Expediting Logic**")
    response.append(df_air.to_markdown(index=False))
    response.append("\n**Explanation:**\n")
    response.append(
        "This table shows the cost comparison if the entire quantity is switched to air freight. "
        f"Sea Cost Per Unit is $ {sea_cost_per_unit:.2f}, Air Cost Per Unit is $ {air_cost_per_unit:.2f}, "
        f"so an extra $ {incremental_cost_per_unit_air:.2f} per unit. For {int(qty_ordered)} units, "
        f"Sea Total Cost = $ {sea_total_cost:.2f} vs. Air Total Cost = $ {air_total_cost:.2f}."
    )

    # 2. Final Comparison Table (only baseline vs. full-air)
    response.append("\n**Final Comparison of Scenarios (Air-Lead Focus)**")
    response.append(df_final_lead.to_markdown(index=False))
    response.append("\n**Explanation:**\n")
    response.append(
        "This final table compares the two scenarios side by side:\n"
        "1. **Baseline Sea:** No changes— all units ship via sea at the standard sea lead time.\n"
        "2. **Air Freight (Full Quantity):** Switch all units to air. "
        f"The actual average lead time for Air has been looked up from shipment data and is '{air_lead_time_str}'. This presents a reduction of '{int(round(avg_lead_time_sea - avg_lead_time_air, 0))}' days from {sea_lead_time_str} in case of Sea Shipping to {air_lead_time_str} when switching to Air."
    )

    return "\n\n".join(response)



def find_alternate_suppliers_by_cost(
    item_number: str,
    region: Optional[str] = None,
    moq_max: Optional[int] = None,
    currency: str = "USD",
    top_n: int = 5,
    capacity_csv: str = "./updated_docs/Supplier_capacity_data.csv",
    supplier_csv: str = "./updated_docs/Supplier_data.csv"
) -> str:
    """
    Lists top N cheapest suppliers for an item, optionally filtered by region & MOQ.
    Joins capacity → master to ensure every vendor is considered.

    Output columns: Supplier Name, Supplier Code, Supplier Location,
                    Unit Price (USD), MOQ, lead_time_days
    """
    cap = pd.read_csv(capacity_csv)
    sup = pd.read_csv(supplier_csv)

    base = cap[cap['Item number'] == item_number].copy()
    if base.empty:
        return f"No capacity data for item {item_number}."

    df = base.merge(
        sup[['Item Number','Supplier Code','Supplier Name','Supplier Location',
             'Unit Price (USD)','MOQ','Lead time (Weeks)']],
        left_on=['Item number','Supplier Code'],
        right_on=['Item Number','Supplier Code'],
        how='left'
    )


    if region:
        df = df[df['Supplier Location_x']
                .str.contains(region, case=False, na=False)]


    if moq_max is not None:
        df = df[df['MOQ'].fillna(moq_max+1) <= moq_max]


    df = df[df['Unit Price (USD)'].notna()]

    try:
        df_sorted = df.sort_values(by='Unit Price (USD)', ascending=True).head(top_n)
    except:
        df_sorted = df.sort_values(by='Unit Price (USD)', ascending=True)
    df_sorted['lead_time_days'] = df_sorted['Lead time (Weeks)'] * 7

    out = df_sorted[[
        'Supplier Name','Supplier Code','Supplier Location_x',
        'Unit Price (USD)','lead_time_days'
    ]]
    if out.empty:
        return f"No suppliers match filters for {item_number}."
    return out.to_markdown(index=False)


# TODO: Need to fix this function for sorting :(
def rank_suppliers_by_leadtime_and_moq(
    item_number: str,
    # max_moq: int,
    location: Optional[str] = None,
    top_n: int = 4,
    supplier_csv: str = "./updated_docs/Supplier_data.csv"
) -> str:
    """
    For an item, return the top N suppliers with the shortest lead times
    and MOQ <= max_moq, optionally filtered by location.

    Returns markdown table.
    """
    df = pd.read_csv(supplier_csv)
    df = df[df['Item Number'] == item_number]

    if location:
        df = df[df['Supplier Location'].str.contains(location, case=False, na=False)]
    df['lead_time_days'] = df['Lead time (Weeks)'] * 7
    df.to_csv('s1.csv')
    df_sorted = df.sort_values(by=['lead_time_days','MOQ'])
    
    out = df_sorted[[
        'Supplier Name','Supplier Code','Supplier Location',
        'MOQ','lead_time_days'
    ]]
    return out.to_markdown(index=False)

def get_best_suppliers(
    item_numbers: list,
    delivery_location: str,
    shipping_mode: str = 'sea',
    supplier_csv_path: str= './updated_docs/Supplier_data.csv'
) -> str:
    """
    Reads supplier data from a CSV, then for each item number finds the top supplier
    in each supplier country based on lowest Total Cost.

    Total Cost is calculated as:
        Unit Price + Shipping Cost

    Parameters:
    - supplier_csv_path (str): Path to the CSV file containing supplier data.
    - item_numbers (list): List of ITM codes (e.g., ['ITM-001', 'ITM-002']).
    - delivery_location (str): Delivery location string to filter supplier rows.
      Example: 'US/New York' or 'Philippines/Manila'.
    - shipping_mode (str): Either 'sea' or 'air'. Defaults to 'sea'.

    Returns:
    - str: A concatenated markdown string with a separate table for each item.
    """
    # 1) Load supplier data from CSV
    items_data = pd.read_csv(supplier_csv_path)

    # 2) Determine which shipping‐cost column to use
    mode = shipping_mode.strip().lower()
    if mode == 'air':
        shipping_column = 'Air shipping cost/pc'
    else:
        shipping_column = 'Sea shipping cost/pc'

    output_strings = []

    # 3) Iterate over each requested item number
    for itm in item_numbers:
        # Filter rows by Item Number and Delivery location
        filtered = items_data[
            (items_data['Item Number'] == itm) &
            (items_data['Delivery location'] == delivery_location)
        ].copy()

        if filtered.empty:
            output_strings.append(
                f"{itm}: No matching entries found for delivery location '{delivery_location}'."
            )
            continue

        # 4) Compute Total Cost = Unit Price + Shipping Cost (no import duty)
        def compute_total_cost(row):
            unit_price = float(row['Unit Price (USD)'])
            shipping_cost = float(row[shipping_column])
            return pd.Series({'Total Cost': unit_price + shipping_cost})

        computed = filtered.apply(compute_total_cost, axis=1)
        filtered = pd.concat([filtered, computed], axis=1)

        # 5) Sort by Supplier Location + Total Cost, then pick cheapest per country
        filtered.sort_values(by=['Supplier Location', 'Total Cost'], inplace=True)
        best_per_country = filtered.groupby('Supplier Location', as_index=False).first()

        # 6) Keep only the columns you need (omit import-duty columns)
        cols = [
            'Item Number',
            'Item Description',
            'Supplier Name',
            'Supplier Code',
            'Supplier Location',
            'Delivery location',
            'Lead time (Weeks)',
            'MOQ',
            'Unit Price (USD)',
            shipping_column,
            'Total Cost'
        ]
        result_df = best_per_country[cols].copy()

        # 7) Rename the shipping column to 'Shipping Cost/pc'
        result_df.rename(columns={shipping_column: 'Shipping Cost/pc'}, inplace=True)
        result_df['Total Cost'] = result_df['Total Cost'].round(2)

        # 8) Convert to markdown, save CSV if desired, and append to output
        md_table = result_df.to_markdown(index=False)
        result_df.to_csv(f"itm_{itm}.csv", index=False)
        output_strings.append(f"{itm}:\n\n{md_table}\n")

    return "\n".join(output_strings)

def get_best_suppliers_by_lead_cost(
    item_numbers: list,
    delivery_location: str,
    shipping_mode: str = 'sea',
    supplier_csv_path: str = './updated_docs/Supplier_data.csv'
) -> str:
    """
    For each requested item, finds the best supplier _from each country_ by:
      1) Lowest Lead time (Weeks)
      2) Tiebreaker: Lowest Total Cost (Unit Price + Shipping Cost)

    Excludes suppliers located in China.

    Returns a concatenated markdown with a table per item.
    """
    # 1) Load supplier data
    df = pd.read_csv(supplier_csv_path)

    # 2) Pick shipping‑cost column
    mode = shipping_mode.strip().lower()
    ship_col = 'Air shipping cost/pc' if mode == 'air' else 'Sea shipping cost/pc'

    output_strings = []

    for itm in item_numbers:
        # 3) Filter to this item, delivery location, and exclude China
        sub = df[
            (df['Item Number'] == itm) &
            (df['Delivery location'] == delivery_location) &
            (df['Supplier Location'].str.strip().str.lower() != 'china')
        ].copy()

        if sub.empty:
            output_strings.append(
                f"**{itm}**: No entries for delivery location '{delivery_location}' (excluding China)."
            )
            continue

        # 4) Ensure numeric
        sub['Lead time (Weeks)'] = pd.to_numeric(sub['Lead time (Weeks)'], errors='coerce')
        sub['Unit Price (USD)']  = pd.to_numeric(sub['Unit Price (USD)'],  errors='coerce')
        sub[ship_col]            = pd.to_numeric(sub[ship_col],            errors='coerce')

        # 5) Compute Total Cost
        sub['Total Cost'] = sub['Unit Price (USD)'] + sub[ship_col]

        # 6) Sort by country, then Lead time, then Total Cost
        sub.sort_values(
            by=['Supplier Location', 'Lead time (Weeks)', 'Total Cost'],
            inplace=True
        )

        # 7) Pick the best per country
        best = sub.groupby('Supplier Location', as_index=False).first()

        # 8) Select & rename columns
        cols = [
            'Item Number', 'Item Description',
            'Supplier Name','Supplier Code','Supplier Location',
            'Delivery location','Lead time (Weeks)','MOQ',
            'Unit Price (USD)', ship_col, 'Total Cost'
        ]
        result = best[cols].copy()
        result.rename(columns={ship_col: 'Shipping Cost/pc'}, inplace=True)
        result['Total Cost'] = result['Total Cost'].round(2)

        # 9) Render & save
        md = result.to_markdown(index=False)
        result.to_csv(f"best_suppliers_{itm}.csv", index=False)
        output_strings.append(f"**{itm}**\n\n{md}\n")

    return "\n".join(output_strings)

def update_import_duties( updates: dict = {}, use_global: bool = False, csv_path: str='./updated_docs/Import Duty.csv') -> str:
    global global_import_duties_df

    # Determine initial DataFrame source
    if use_global and global_import_duties_df is not None:
        df = global_import_duties_df.copy()
    else:
        # Load fresh from CSV if no global exists or use_global is False
        df = pd.read_csv(csv_path)
        df['Import Duty'] = df['Import Duty'].astype(str)

    # Apply each update: overwrite existing or append new row
    for (supplier, delivery), new_duty in updates.items():
        mask = (df['Supplier Location'] == supplier) & (df['Delivery Location'] == delivery)
        if mask.any():
            df.loc[mask, 'Import Duty'] = new_duty
        else:
            new_row = {
                'Supplier Location': supplier,
                'Delivery Location': delivery,
                'Import Duty': new_duty
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # Sort for readability
    df = df.sort_values(by=['Supplier Location', 'Delivery Location']).reset_index(drop=True)

    # Update the global variable so future calls can use this DataFrame
    global_import_duties_df = df.copy()

    # Return markdown representation
    return df.to_markdown(index=False)





def find_suppliers_for_due_date(
    Supplier_Name: Optional[str] = None,
    Supplier_Code: Optional[str] = None,
    Supplier_Location: Optional[str] = None,
    Item_Number: Optional[str] = None,
    due_in_days: Optional[int] = None,
    destinations: Optional[List[str]] = None,
    top_n_carriers: int = 4,
    supplier_csv: str = "./updated_docs/Supplier_data.csv",
    capacity_csv: str = "./updated_docs/Supplier_capacity_data.csv",
    shipment_csv: str = "./updated_docs/Shipment_tracker_data.csv"
) -> str:
    """
    1) Suggest suppliers who meet the `due_in_days` window from origin region.
    2) For those suppliers, analyze historic carriers to given destinations.
       Returns two markdown tables:
         • suppliers: Supplier name, code, location, and total lead days.
         • carriers: Carrier name with min, avg, and max transit times (days).

    Parameters:
    - Supplier_Name (str, optional): substring match on supplier name
    - Supplier_Code (str, optional): exact match on supplier code
    - Supplier_Location (str, optional): substring match on supplier location
    - Item_Number (str, optional): exact match on item number
    - due_in_days (int, optional): include suppliers whose total lead time ≤ this
    - destinations (List[str], optional): list of delivery-location substrings to filter shipments
    - top_n_carriers (int): how many top carriers by avg transit time to return
    - *\*_csv (str): filepaths to your CSVs

    Returns:
    - str: two markdown tables concatenated—first suppliers, then carriers with
           min/avg/max transit times.
    """

    # --- Load data ---
    sup  = pd.read_csv(supplier_csv)
    cap  = pd.read_csv(capacity_csv)
    ship = pd.read_csv(shipment_csv, dtype=str)

    # --- Parse dates into datetime ---
    for col in ['Ship Date', 'Receipt Date', 'Delivery Date']:
        ship[col] = pd.to_datetime(
            ship[col].str.strip() + '-2025',
            format='%d-%b-%Y',
            errors='coerce'
        )

    # --- Merge capacity with supplier lead time & price ---
    merged = cap.merge(
        sup[['Supplier Code', 'Lead time (Weeks)', 'Unit Price (USD)']],
        on='Supplier Code',
        how='left'
    )
    merged['total_lead_days'] = merged['Lead time (Weeks)'] * 7

    # --- Apply filters for suppliers ---
    df = merged
    if Supplier_Name:
        df = df[df['Supplier name'].str.contains(Supplier_Name, case=False, na=False)]
    if Supplier_Code:
        df = df[df['Supplier Code'] == Supplier_Code]
    if Supplier_Location:
        df = df[df['Supplier Location'].str.contains(Supplier_Location, case=False, na=False)]
    if Item_Number:
        df = df[df['Item number'] == Item_Number]
    if due_in_days is not None:
        df = df[df['total_lead_days'] <= due_in_days]

    # --- Build supplier output table ---
    df_sup = df.sort_values('Unit Price (USD)')
    suppliers_out = df_sup[[
        'Supplier name', 'Supplier Code', 'Supplier Location', 'total_lead_days'
    ]]

    # --- Filter shipment history to matching suppliers & destinations ---
    carr = ship[ ship['Supplier Code'].isin(df_sup['Supplier Code']) ]
    if destinations:
        pattern = '|'.join(destinations)
        carr = carr[carr['Delivery Location'].str.contains(pattern, case=False, na=False)]

    # --- Compute transit days ---
    carr['transit_days'] = (carr['Delivery Date'] - carr['Ship Date']).dt.days


    # --- Aggregate by carrier: min, avg, max ---
    carriers = (
        carr.groupby('Carrier name')['transit_days']
            .agg(
                min_transit_days='min',
                avg_transit_days='mean',
                max_transit_days='max'
            )
            .reset_index()
            # Round the average to one decimal, if you like:
            .assign(avg_transit_days=lambda d: d['avg_transit_days'])
            .sort_values('avg_transit_days')
            .head(top_n_carriers)
    )

    # --- Return Markdown tables ---
    return (
        suppliers_out.to_markdown(index=False) +
        "\n\n" +
        carriers.to_markdown(index=False)
    )



def list_expired_inventory(
    as_of_date: str,
    sloc: Optional[str]    = None,
    category: Optional[str] = None,
    inventory_csv: str      = "./updated_docs/Inventory_data.csv"
) -> str:
    """
    List all items whose expiry (day+month) falls ON OR BEFORE as_of_date,
    optionally filtered by sloc (storage location) or category.
    Returns a markdown table.
    """

    df = pd.read_csv(inventory_csv, dtype=str)

    df['Expiry Date'] = pd.to_datetime(
        df['Expiry Date'].str.strip() + '-2025',
        format='%d-%b-%Y',
        errors='coerce'
    )

    print(df)
    cutoff = pd.to_datetime(as_of_date, dayfirst=True, errors='coerce')
    print(cutoff)

    expired = df[df['Expiry Date'] <= cutoff]


    if sloc:
        expired = expired[expired['Sloc']
                          .str.contains(sloc, case=False, na=False)]
    if category:
        expired = expired[expired['Category']
                          .str.contains(category, case=False, na=False)]


    out = expired[['Item Number','Item Description','Qty','Expiry Date','Sloc']]

    return out.to_markdown(index=False)



def summarize_inventory_vs_po(
    item_number: Optional[str] = None,
    sloc: Optional[str] = None,
    po_date_from: Optional[str] = None,
    po_date_to: Optional[str] = None,
    inventory_csv: str = "./updated_docs/Inventory_data.csv",
    po_csv: str = "./updated_docs/PO_data.csv"
) -> str:
    """
    Cross-compare on-hand inventory vs pending PO quantities.

    Returns markdown table: Item, On-Hand Qty, Pending Qty, Net Position.
    """
    inv = pd.read_csv(inventory_csv)
    po = pd.read_csv(po_csv, parse_dates=['PO date'], dayfirst=True)
    
    inv['Qty_n'] = inv['Qty'].str.replace(',','').astype(float)
    po['Qnty pending'] = po['Qnty pending'].astype(float)

    if item_number:
        inv = inv[inv['Item Number']==item_number]
        po = po[po['Item number']==item_number]
    if sloc:
        inv = inv[inv['Sloc'].str.contains(sloc, case=False, na=False)]
    if po_date_from:
        df_from = pd.to_datetime(po_date_from, dayfirst=True)
        po = po[po['PO date']>=df_from]
    if po_date_to:
        df_to = pd.to_datetime(po_date_to, dayfirst=True)
        po = po[po['PO date']<=df_to]

    inv_sum = inv.groupby('Item Number')['Qty_n'].sum().reset_index()
    po_sum = po.groupby('Item number')['Qnty pending'].sum().reset_index()
    merged = inv_sum.merge(po_sum, left_on='Item Number', right_on='Item number', how='outer').fillna(0)
    merged['Net Position'] = merged['Qty_n'] - merged['Qnty pending']
    out = merged[['Item Number','Qty_n','Qnty pending','Net Position']]
    out.columns = ['Item Number','On-Hand Qty','Pending Qty','Net Position']
    return out.to_markdown(index=False)


def get_supplier_load(
    supplier_code: str,
    item_number: Optional[str] = None,
    capacity_csv: str = "./updated_docs/Supplier_capacity_data.csv"
) -> str:
    """
    Show current committed vs available capacity for a supplier, optionally per item.

    Returns markdown table: Item, Total Cap, Committed, Available, MOQ, Lead Time.
    """
    df = pd.read_csv(capacity_csv)
    df = df[df['Supplier Code']==supplier_code]
    if item_number:
        df = df[df['Item number']==item_number]
    df['Available'] = df['Total monthly capacity (units)'] - df['Current committed capacity (units)']
    df['Lead days'] = df['Lead time'].str.extract(r"(\d+)").astype(int)
    out = df[[
        'Item number','Total monthly capacity (units)','Current committed capacity (units)',
        'Available','MOQ','Lead days'
    ]]
    out.columns = ['Item','Total Cap','Committed','Available','MOQ','Lead Time (days)']
    return out.to_markdown(index=False)


def calculate_transit_time(supplier_location: str = None, delivery_location: str = None, mode_of_transport: str = None) -> str:
    """
    Calculates the average transit time (in days) for shipments from a supplier location to a delivery location,
    optionally filtered by mode of transport (Air or Sea).

    Parameters:
    - supplier_location (str): Supplier's origin location (e.g., 'Japan')
    - delivery_location (str): Delivery destination (e.g., 'Philippines/Manila')
    - mode_of_transport (str, optional): Mode of transport ('Air', 'Sea'); if None, considers all modes

    Returns:
    - str: A markdown table showing average transit time for the filtered routes
    """

    df = pd.read_csv("./updated_docs/Shipment_tracker_data.csv")


    # Filter based on inputs
    if supplier_location in df['Supplier Code'].to_list():
        df = df[df["Supplier Code"].str.lower() == supplier_location.lower()]
    if delivery_location:
        df = df[df["Delivery Location"].str.lower().str.contains(delivery_location.lower(), na=False)]
    if mode_of_transport:
        df = df[df["Mode of Transport"].str.lower() == mode_of_transport.lower()]

    if df.empty:
        return "No shipment data available for the given filters."



    result = df.groupby(["Supplier Code","Supplier Location","Delivery Location","Mode of Transport"])["Lead time (days)"].mean().reset_index()
    result.rename(columns={"Lead time (days)": "Avg Transit Time (days)"}, inplace=True)
    return_result = result.sort_values(by=['Avg Transit Time (days)'])
    return result.to_markdown(index=False)


# ===== PANAMA CANAL DELAY ANALYSIS FUNCTIONS =====

def get_delayed_shipments_to_east_coast(affected_dc: str = None, delay_days: int = 15) -> dict:
    """
    Identify high-risk shipments to East Coast ports affected by Panama Canal delays.
    Filters by east coast ports, affected DC, and prioritizes high-risk items by DOS and classification.
    
    Args:
        affected_dc: Specific DC to analyze (e.g., 'DC3'). If None, analyzes all East Coast DCs
        delay_days: Number of days of delay (default 15)
    
    Returns:
        Dict containing:
        - markdown_output: Formatted markdown table string
        - delayed_items: List of dicts with item details
        - total_value_at_risk: Total financial impact
        - affected_dc: DC being analyzed
        - summary_stats: Additional metrics
    """
    try:
        # Load relevant data
        po_df = pd.read_csv('./updated_docs/Open_PO_data.csv')
        inv_df = pd.read_csv('./updated_docs/Inventory_data.csv')
        
        # East Coast ports affected by Panama Canal delays
        east_coast_ports = ['Port Georgia', 'Port New York', 'Port Boston']
        
        # Filter POs going to East Coast ports
        east_coast_pos = po_df[po_df['Arrival Port'].isin(east_coast_ports)].copy()
        
        if east_coast_pos.empty:
            return "No purchase orders found heading to East Coast ports."
        
        # If specific DC is requested, filter further
        if affected_dc:
            east_coast_pos = east_coast_pos[east_coast_pos['Destination DC'] == affected_dc].copy()
            if east_coast_pos.empty:
                return f"No East Coast shipments found for {affected_dc}."
        
        # Get current inventory to calculate Days of Supply for risk assessment
        if affected_dc:
            dc_filter = [affected_dc]
        else:
            dc_filter = east_coast_pos['Destination DC'].unique()
        
        # Calculate DOS for items in affected shipments
        high_risk_items = []
        
        for dc in dc_filter:
            dc_inventory = inv_df[inv_df['destination_dc'] == dc].copy()
            if dc_inventory.empty:
                continue
                
            # Convert to numeric and calculate DOS
            dc_inventory['Qty'] = pd.to_numeric(dc_inventory['Qty'].astype(str).str.replace(',', ''), errors='coerce')
            dc_inventory['daily_sales_forecast_quantity'] = pd.to_numeric(dc_inventory['daily_sales_forecast_quantity'], errors='coerce')
            dc_inventory['Days_of_Supply'] = dc_inventory['Qty'] / dc_inventory['daily_sales_forecast_quantity'].replace(0, 1)
            
            # Identify high-risk items: Classification A items with DOS < delay_days
            dc_high_risk = dc_inventory[
                (dc_inventory['Days_of_Supply'] < delay_days) & 
                (dc_inventory['Classification'] == 'A')
            ]['Item Number'].tolist()
            
            high_risk_items.extend(dc_high_risk)
        
        # Filter shipments to only include high-risk items
        if high_risk_items:
            filtered_shipments = east_coast_pos[east_coast_pos['Item Number'].isin(high_risk_items)].copy()
        else:
            # If no high-risk items identified, show all Class A items from East Coast shipments
            filtered_shipments = east_coast_pos.copy()
        
        if filtered_shipments.empty:
            return f"No high-risk shipments identified for {'East Coast DCs' if not affected_dc else affected_dc}."
        
        # Add delay information and risk scoring
        filtered_shipments['Original Due Date'] = pd.to_datetime(filtered_shipments['PO Due Date'], dayfirst=True)
        filtered_shipments['Delayed Due Date'] = filtered_shipments['Original Due Date'] + pd.Timedelta(days=delay_days)
        filtered_shipments['Delay Days'] = delay_days
        
        # Add financial impact calculation
        filtered_shipments['Qnty Ordered'] = pd.to_numeric(filtered_shipments['Qnty Ordered'], errors='coerce')
        filtered_shipments['Item value/pc with shipping'] = pd.to_numeric(filtered_shipments['Item value/pc with shipping'], errors='coerce')
        filtered_shipments['Total Value'] = filtered_shipments['Qnty Ordered'] * filtered_shipments['Item value/pc with shipping']
        
        # Sort by total value (highest impact first)
        filtered_shipments = filtered_shipments.sort_values('Total Value', ascending=False)
        
        # Select relevant columns for output
        output_cols = ['PO number', 'Item Number', 'Item Description', 'Destination DC', 
                      'Arrival Port', 'Container no', 'Qnty Ordered', 'Total Value',
                      'PO Due Date', 'Delayed Due Date', 'Delay Days']
        
        result = filtered_shipments[output_cols].copy()
        result['PO Due Date'] = result['PO Due Date'].astype(str)
        result['Delayed Due Date'] = result['Delayed Due Date'].dt.strftime('%d/%m/%Y')
        result['Total Value'] = result['Total Value'].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "$0.00")
        
        total_shipments = len(result)
        total_value = filtered_shipments['Total Value'].sum()
        
        # Create markdown output
        markdown_output = f"**PANAMA CANAL DELAY IMPACT - HIGH-RISK EAST COAST SHIPMENTS**\n"
        markdown_output += f"{'Analysis for ' + affected_dc if affected_dc else 'East Coast DCs'}: {total_shipments} high-risk shipments delayed {delay_days} days\n"
        markdown_output += f"Total Value at Risk: ${total_value:,.2f}\n\n"
        markdown_output += result.to_markdown(index=False)
        
        # Create structured data for delayed items
        delayed_items = []
        for _, row in filtered_shipments.iterrows():
            delayed_items.append({
                'po_number': row['PO number'],
                'item_number': row['Item Number'],
                'item_description': row['Item Description'],
                'destination_dc': row['Destination DC'],
                'arrival_port': row['Arrival Port'],
                'container_no': row['Container no'],
                'quantity_ordered': int(row['Qnty Ordered']) if pd.notnull(row['Qnty Ordered']) else 0,
                'total_value': float(row['Total Value']) if pd.notnull(row['Total Value']) else 0.0,
                'po_due_date': str(row['PO Due Date']),
                'delayed_due_date': row['Delayed Due Date'].strftime('%d/%m/%Y'),
                'delay_days': delay_days
            })
        
        # Return structured data
        return {
            'markdown_output': markdown_output,
            'delayed_items': delayed_items,
            'total_value_at_risk': float(total_value),
            'affected_dc': affected_dc if affected_dc else 'All East Coast DCs',
            'summary_stats': {
                'total_shipments': total_shipments,
                'delay_days': delay_days,
                'high_risk_items': filtered_shipments['Item Number'].unique().tolist(),
                'affected_ports': filtered_shipments['Arrival Port'].unique().tolist()
            }
        }
        
    except Exception as e:
        error_msg = f"Error analyzing delayed shipments: {str(e)}"
        return {
            'markdown_output': error_msg,
            'delayed_items': [],
            'total_value_at_risk': 0.0,
            'affected_dc': affected_dc or 'Unknown',
            'summary_stats': {'error': str(e)}
        }


def get_delayed_shipments_to_east_coast_markdown(affected_dc: str = None, delay_days: int = 15) -> str:
    """
    Backward compatibility function that returns only the markdown output.
    For new code, use get_delayed_shipments_to_east_coast() which returns structured data.
    """
    result = get_delayed_shipments_to_east_coast(affected_dc, delay_days)
    return result['markdown_output']


def analyze_stockout_risk_by_dc(dc_name: str, delay_days: int = 15) -> str:
    """
    Analyze stockout risk for a specific DC based on inventory levels and sales forecast.
    
    Args:
        dc_name: Name of the distribution center (e.g., 'DC1')
        delay_days: Number of days of delay
    
    Returns:
        Markdown table showing stockout risk analysis
    """
    try:
        # Load inventory data
        inv_df = pd.read_csv('./updated_docs/Inventory_data.csv')
        
        # Filter by DC
        dc_inventory = inv_df[inv_df['destination_dc'] == dc_name].copy()
        
        if dc_inventory.empty:
            return f"No inventory data found for {dc_name}."
        
        # Calculate Days of Supply (DOS)
        # Convert to numeric and handle any formatting issues
        dc_inventory['Qty'] = pd.to_numeric(dc_inventory['Qty'].astype(str).str.replace(',', ''), errors='coerce')
        dc_inventory['daily_sales_forecast_quantity'] = pd.to_numeric(dc_inventory['daily_sales_forecast_quantity'], errors='coerce')
        
        # Calculate DOS, avoiding division by zero
        dc_inventory['Days_of_Supply'] = dc_inventory['Qty'] / dc_inventory['daily_sales_forecast_quantity'].replace(0, 1)
        
        # Identify high-risk items (DOS < delay_days)
        high_risk = dc_inventory[dc_inventory['Days_of_Supply'] < delay_days].copy()
        
        # Focus on Classification A items (high-selling)
        high_risk_class_a = high_risk[high_risk['Classification'] == 'A'].copy()
        
        if high_risk_class_a.empty:
            return f"No high-risk Class A items found for {dc_name} with current delay of {delay_days} days."
        
        # Calculate potential lost sales
        high_risk_class_a['Potential_Lost_Sales_USD'] = (
            (delay_days - high_risk_class_a['Days_of_Supply']) * 
            high_risk_class_a['daily_sales_forecast_quantity'] * 
            high_risk_class_a['selling_price_usd']
        )
        
        # Select relevant columns
        output_cols = ['Item Number', 'Item Description', 'Classification', 'Qty', 
                      'daily_sales_forecast_quantity', 'Days_of_Supply', 'selling_price_usd',
                      'Potential_Lost_Sales_USD']
        
        result = high_risk_class_a[output_cols].copy()
        result['Days_of_Supply'] = result['Days_of_Supply'].round(1)
        result['Potential_Lost_Sales_USD'] = result['Potential_Lost_Sales_USD'].round(2)
        
        # Rename columns for better readability to match agent expectations
        result = result.rename(columns={
            'Qty': 'Current Inventory',
            'Potential_Lost_Sales_USD': 'Potential Lost Sales'
        })
        
        total_lost_sales = result['Potential Lost Sales'].sum()
        
        output = f"**STOCKOUT RISK ANALYSIS - {dc_name}**\n"
        output += f"High-selling products (Classification A) at risk due to {delay_days}-day delay:\n\n"
        output += result.to_markdown(index=False)
        output += f"\n\n**Total Potential Lost Sales: ${total_lost_sales:,.2f}**"
        
        return output
        
    except Exception as e:
        return f"Error analyzing stockout risk for {dc_name}: {str(e)}"


def recommend_container_rerouting(delayed_shipments_data: dict, min_dos_threshold: int = 15) -> str:
    """
    Recommend container rerouting based on delayed shipments analysis.
    Takes structured output from get_delayed_shipments_to_east_coast and finds rerouting options.
    
    Args:
        delayed_shipments_data: Dict output from get_delayed_shipments_to_east_coast function containing:
            - delayed_items: List of delayed shipment details
            - affected_dc: DC being analyzed
            - summary_stats: Additional metrics
        min_dos_threshold: Minimum days of supply required for donor DCs (default 15)
    
    Returns:
        Recommendations for container rerouting with cost-benefit analysis
    """
    try:
        # Load data
        po_df = pd.read_csv('./updated_docs/Open_PO_data.csv')
        inv_df = pd.read_csv('./updated_docs/Inventory_data.csv')
        port_cost_df = pd.read_csv('./updated_docs/Port_transfer_cost.csv')
        
        # Extract data from structured input
        affected_dc = delayed_shipments_data.get('affected_dc')
        delayed_items = delayed_shipments_data.get('delayed_items', [])
        
        if not affected_dc or affected_dc == 'All East Coast DCs':
            return "Rerouting function requires a specific affected DC, not all East Coast DCs."
        
        if not delayed_items:
            return "No delayed items found in the input data."
        
        # Extract high-risk item numbers from delayed items
        high_risk_items = list(set([item['item_number'] for item in delayed_items]))
        
        if not high_risk_items:
            return "No high-risk items found in delayed shipments data."
        
        # East Coast ports (where delays are occurring)
        east_coast_ports = ['Port Georgia', 'Port New York', 'Port Boston']
        
        # Non-East Coast DCs that could be potential donors
        all_dcs = ['DC1', 'DC2', 'DC3', 'DC4', 'DC5']
        potential_donor_dcs = [dc for dc in all_dcs if dc != affected_dc]
        
        rerouting_recommendations = []
        
        # For each high-risk item, find potential donor DCs
        for item_number in high_risk_items:
            
            # Check each potential donor DC
            for donor_dc in potential_donor_dcs:
                
                # Check if donor DC has sufficient DOS (15+ days) for this item
                donor_inv = inv_df[
                    (inv_df['destination_dc'] == donor_dc) & 
                    (inv_df['Item Number'] == item_number)
                ].copy()
                
                if donor_inv.empty:
                    continue
                
                # Calculate DOS for donor DC
                donor_inv['Qty'] = pd.to_numeric(donor_inv['Qty'].astype(str).str.replace(',', ''), errors='coerce')
                donor_inv['daily_sales_forecast_quantity'] = pd.to_numeric(donor_inv['daily_sales_forecast_quantity'], errors='coerce')
                donor_inv['DOS'] = donor_inv['Qty'] / donor_inv['daily_sales_forecast_quantity'].replace(0, 1)
                
                # Check if donor has sufficient inventory (15+ days supply)
                max_donor_dos = donor_inv['DOS'].max()
                if max_donor_dos < min_dos_threshold:
                    continue  # Donor DC doesn't have enough supply
                
                # Look for available PO shipments from donor DC for this item
                donor_shipments = po_df[
                    (po_df['Destination DC'] == donor_dc) &
                    (po_df['Item Number'] == item_number) &
                    (~po_df['Arrival Port'].isin(east_coast_ports))  # Non-East Coast shipments that can be rerouted
                ].copy()
                
                if donor_shipments.empty:
                    continue
                
                # Calculate rerouting costs for each available shipment
                for _, shipment in donor_shipments.iterrows():
                    
                    # Find the destination port for affected DC (where shipment should be rerouted)
                    affected_dc_shipments = po_df[po_df['Destination DC'] == affected_dc]
                    if not affected_dc_shipments.empty:
                        target_port = affected_dc_shipments['Arrival Port'].iloc[0]
                    else:
                        target_port = 'Port Georgia'  # Default East Coast port
                    
                    # Look up rerouting cost
                    cost_lookup = port_cost_df[
                        (port_cost_df['from_port'] == shipment['Arrival Port']) &
                        (port_cost_df['to_port'] == target_port)
                    ]
                    
                    if not cost_lookup.empty:
                        rerouting_cost = cost_lookup['transfer_cost_usd'].iloc[0]
                    else:
                        rerouting_cost = 1500  # Default cost if not found
                    
                    # Calculate financial metrics
                    shipment_value = pd.to_numeric(shipment['Total PO value'], errors='coerce')
                    quantity = pd.to_numeric(shipment['Qnty Ordered'], errors='coerce')
                    
                    rerouting_recommendations.append({
                        'Item_Number': item_number,
                        'Item_Description': shipment['Item Description'],
                        'PO_Number': shipment['PO number'],
                        'Container_No': shipment['Container no'],
                        'Donor_DC': donor_dc,
                        'Donor_DOS': f"{max_donor_dos:.1f}",
                        'From_Port': shipment['Arrival Port'],
                        'To_DC': affected_dc,
                        'Quantity': quantity,
                        'Shipment_Value': shipment_value,
                        'Rerouting_Cost': rerouting_cost,
                        #'Cost_Benefit_Ratio': (shipment_value / rerouting_cost) if rerouting_cost > 0 else 0
                    })
        
        if not rerouting_recommendations:
            return f"No viable rerouting options found. Non-East Coast DCs do not have sufficient inventory (15+ days supply) for high-risk items."
        
        # Sort by Rerouting Cost (lowest value per rerouting cost)
        rerouting_recommendations.sort(key=lambda x: x['Rerouting_Cost'], reverse=False)
        
        # Create output table
        output = f"**CONTAINER REROUTING RECOMMENDATIONS FOR {affected_dc}**\n"
        output += f"Found {len(rerouting_recommendations)} viable rerouting options from DCs with 15+ days supply:\n\n"
        
        # Take top 5 recommendations
        top_recommendations = rerouting_recommendations[:5]
        
        # Format as markdown table
        headers = ['PO Number', 'Item', 'Donor DC', 'From Port', 'To DC', 
                  'Qty', 'Value', 'Reroute Cost']
        
        table_data = []
        total_rerouting_cost = 0
        total_shipment_value = 0
        
        for rec in top_recommendations:
            total_rerouting_cost += rec['Rerouting_Cost']
            total_shipment_value += rec['Shipment_Value']
            print("**********--", rec['To_DC'])
            
            table_data.append([
                rec['PO_Number'],
                f"{rec['Item_Number']} - {rec['Item_Description'][:20]}...",
                f"{rec['Donor_DC']} ({rec['Donor_DOS']}d)",
                rec['From_Port'],
                rec['To_DC'],
                f"{rec['Quantity']:,.0f}",
                f"${rec['Shipment_Value']:,.0f}",
                f"${rec['Rerouting_Cost']:,.0f}",
                #f"{rec['Cost_Benefit_Ratio']:.1f}x"
            ])
        
        # Create markdown table
        table_rows = []
        table_rows.append('| ' + ' | '.join(headers) + ' |')
        table_rows.append('|' + '|'.join([':' + '-'*(len(h)-1) for h in headers]) + '|')
        
        for row in table_data:
            table_rows.append('| ' + ' | '.join([str(cell) for cell in row]) + ' |')
        
        output += '\n'.join(table_rows)
        
        # Summary
        roi_percentage = ((total_shipment_value - total_rerouting_cost) / total_rerouting_cost * 100) if total_rerouting_cost > 0 else 0
        
        output += f"\n\n**REROUTING SUMMARY:**\n"
        output += f"- Total Shipment Value: ${total_shipment_value:,.2f}\n"
        output += f"- Total Rerouting Cost: ${total_rerouting_cost:,.2f}\n"
        #output += f"- Net Value (shipment value - rerouting cost): ${total_shipment_value - total_rerouting_cost:,.2f}\n"
        #output += f"- ROI: {roi_percentage:,.0f}%\n"
        output += f"- Recommendation: {'PROCEED with rerouting' if roi_percentage > 100 else 'EVALUATE ALTERNATIVES'}"
        
        # Create structured output for other functions to use
        structured_output = {
            'markdown_output': output,
            'total_rerouting_cost': total_rerouting_cost,
            'container_information': top_recommendations if 'top_recommendations' in locals() else []
        }

        return structured_output
        
    except Exception as e:
        return f"Error generating rerouting recommendations: {str(e)}"


def calculate_cost_benefit_analysis(affected_dc: str, delay_days: int = 15) -> str:
    """
    Calculate comprehensive cost-benefit analysis for container rerouting vs. accepting stockouts.
    
    Args:
        affected_dc: DC that needs inventory
        delay_days: Number of days of delay
    
    Returns:
        Cost-benefit analysis with recommendations
    """
    try:
        # Load data
        inv_df = pd.read_csv('./updated_docs/Inventory_data.csv')
        port_cost_df = pd.read_csv('./updated_docs/Port_transfer_cost.csv')
        
        # Calculate potential lost sales (cost of doing nothing)
        affected_inv = inv_df[inv_df['destination_dc'] == affected_dc].copy()
        affected_inv['Qty'] = pd.to_numeric(affected_inv['Qty'].astype(str).str.replace(',', ''), errors='coerce')
        affected_inv['daily_sales_forecast_quantity'] = pd.to_numeric(affected_inv['daily_sales_forecast_quantity'], errors='coerce')
        affected_inv['Days_of_Supply'] = affected_inv['Qty'] / affected_inv['daily_sales_forecast_quantity'].replace(0, 1)
        
        high_risk_items = affected_inv[
            (affected_inv['Days_of_Supply'] < delay_days) & 
            (affected_inv['Classification'] == 'A')
        ].copy()
        
        if high_risk_items.empty:
            return f"No high-risk items found for {affected_dc}."
        
        # Calculate total potential lost sales
        high_risk_items['Lost_Sales'] = (
            (delay_days - high_risk_items['Days_of_Supply']) * 
            high_risk_items['daily_sales_forecast_quantity'] * 
            high_risk_items['selling_price_usd']
        )
        
        total_lost_sales = high_risk_items['Lost_Sales'].sum()
        
        # Get ACTUAL rerouting costs from the same logic used by panama_analysis_agent
        rerouting_result = recommend_container_rerouting(affected_dc, delay_days)
        
        # Extract total rerouting cost from the rerouting recommendation
        if "Total Rerouting Cost: $" in rerouting_result:
            cost_line = [line for line in rerouting_result.split('\n') if 'Total Rerouting Cost: $' in line][0]
            cost_str = cost_line.split('Total Rerouting Cost: $')[1].replace(',', '').replace('**', '')
            try:
                total_rerouting_cost = float(cost_str)
            except:
                # Fallback to estimation if parsing fails
                avg_rerouting_cost = port_cost_df['transfer_cost_usd'].mean()
                estimated_containers_needed = max(1, len(high_risk_items) // 3)
                total_rerouting_cost = avg_rerouting_cost * estimated_containers_needed
        else:
            # No rerouting options available, set cost to 0
            total_rerouting_cost = 0
        
        # Calculate ROI
        net_benefit = total_lost_sales - total_rerouting_cost
        roi = (net_benefit / total_rerouting_cost) * 100 if total_rerouting_cost > 0 else 0
        
        # Create summary table
        analysis_data = {
            'Cost Category': [
                'Potential Lost Sales (Do Nothing)',
                'Container Rerouting Cost',
                'Net Value (total lost sales value - rerouting cost)',
                'ROI of Rerouting (%)'
            ],
            'Amount (USD)': [
                f"${total_lost_sales:,.2f}",
                f"${total_rerouting_cost:,.2f}",
                f"${net_benefit:,.2f}",
                f"{roi:.1f}%"
            ],
            'Impact': [
                'Revenue Loss',
                'One-time Cost',
                'Savings/Loss',
                'Return on Investment'
            ]
        }
        
        analysis_df = pd.DataFrame(analysis_data)
        
        # Generate recommendation
        if net_benefit > 0:
            recommendation = "✅ **RECOMMEND REROUTING**: Rerouting containers will save money and prevent stockouts."
        else:
            recommendation = "❌ **DO NOT REROUTE**: Rerouting costs exceed potential lost sales."
        
        output = f"**COST-BENEFIT ANALYSIS - PANAMA CANAL DELAY**\n"
        output += f"Analysis for {affected_dc} with {delay_days}-day delay:\n\n"
        output += analysis_df.to_markdown(index=False)
        output += f"\n\n{recommendation}"
        # Extract number of containers from rerouting result
        container_count = 0
        if "Total Rerouting Cost: $" in rerouting_result:
            # Count containers by counting table rows (excluding header)
            table_lines = [line for line in rerouting_result.split('\n') if '|' in line and 'PO number' not in line and ':-' not in line]
            container_count = len([line for line in table_lines if line.strip() and not line.startswith('**')])
        
        output += f"\n\n**Key Insights:**"
        output += f"\n• {len(high_risk_items)} high-selling items at risk of stockout"
        if container_count > 0:
            output += f"\n• {container_count} containers identified for rerouting"
        else:
            output += f"\n• No suitable containers available for rerouting"
        output += f"\n• Break-even rerouting cost: ${total_lost_sales:,.2f}"
        
        return output
        
    except Exception as e:
        return f"Error calculating cost-benefit analysis: {str(e)}"


def calculate_financial_impact_and_recommendation(
    delayed_shipments_data: dict,
    rerouting_data: dict = None
) -> str:
    """
    Calculate financial impact and recommendation using structured data from panama analysis.
    Focuses on potential lost sales calculation with optional rerouting cost-benefit analysis.
    
    Args:
        delayed_shipments_data: Dict output from get_delayed_shipments_to_east_coast containing:
            - delayed_items: List of delayed shipment details
            - total_value_at_risk: Total shipment value delayed
            - affected_dc: DC being analyzed
            - summary_stats: Additional metrics
        rerouting_data: Optional dict from recommend_container_rerouting with cost analysis
    
    Returns:
        Financial analysis with potential lost sales and recommendation
    """
    try:
        # Extract data from structured input
        affected_dc = delayed_shipments_data.get('affected_dc')
        delayed_items = delayed_shipments_data.get('delayed_items', [])
        total_shipment_value = delayed_shipments_data.get('total_value_at_risk', 0)
        delay_days = delayed_shipments_data.get('summary_stats', {}).get('delay_days', 15)
        
        if not affected_dc or affected_dc == 'All East Coast DCs':
            return "Financial impact calculation requires a specific affected DC."
        
        if not delayed_items:
            return f"No delayed shipments found for {affected_dc}."
        
        # Load inventory data to calculate potential lost sales
        inv_df = pd.read_csv('./updated_docs/Inventory_data.csv')
        
        # Get high-risk item numbers from delayed shipments
        high_risk_item_numbers = list(set([item['item_number'] for item in delayed_items]))
        
        # Filter inventory for affected DC and high-risk items
        affected_inv = inv_df[
            (inv_df['destination_dc'] == affected_dc) & 
            (inv_df['Item Number'].isin(high_risk_item_numbers))
        ].copy()
        
        if affected_inv.empty:
            return f"No inventory data found for {affected_dc} high-risk items."
        
        # Calculate Days of Supply and potential lost sales
        affected_inv['Qty'] = pd.to_numeric(affected_inv['Qty'].astype(str).str.replace(',', ''), errors='coerce')
        affected_inv['daily_sales_forecast_quantity'] = pd.to_numeric(affected_inv['daily_sales_forecast_quantity'], errors='coerce')
        affected_inv['selling_price_usd'] = pd.to_numeric(affected_inv['selling_price_usd'], errors='coerce')
        affected_inv['Days_of_Supply'] = affected_inv['Qty'] / affected_inv['daily_sales_forecast_quantity'].replace(0, 1)
        
        # Calculate potential lost sales for items with insufficient inventory
        affected_inv['Stockout_Days'] = (delay_days - affected_inv['Days_of_Supply']).clip(lower=0)
        affected_inv['Lost_Sales'] = (
            affected_inv['Stockout_Days'] * 
            affected_inv['daily_sales_forecast_quantity'] * 
            affected_inv['selling_price_usd']
        )
        
        # Filter to only items that will actually have lost sales
        items_with_losses = affected_inv[affected_inv['Lost_Sales'] > 0].copy()
        total_lost_sales = items_with_losses['Lost_Sales'].sum()
        
        # Parse rerouting data if provided
        total_rerouting_cost = 0
        container_count = 0
        rerouting_available = False

        if rerouting_data:
            # Handle both string and dict formats
            if isinstance(rerouting_data, dict):
                total_rerouting_cost = rerouting_data.get('total_rerouting_cost', 0)
                container_info = rerouting_data.get('container_information', [])
                container_count = len(container_info) if container_info else 0
            elif isinstance(rerouting_data, str) and "Total Rerouting Cost: $" in rerouting_data:
                # Parse from markdown string if needed
                import re
                cost_match = re.search(r'Total Rerouting Cost: \$([0-9,]+\.?\d*)', rerouting_data)
                if cost_match:
                    total_rerouting_cost = float(cost_match.group(1).replace(',', ''))
                # Count containers from table rows
                container_count = len(re.findall(r'PO-\d+', rerouting_data))
            
            rerouting_available = total_rerouting_cost > 0 and container_count > 0

        # Calculate cost-benefit analysis
        if rerouting_available and total_rerouting_cost > 0:
            net_benefit = total_lost_sales - total_rerouting_cost
            roi = (net_benefit / total_rerouting_cost) * 100
            if roi > 100:
                recommendation = "✅ **RECOMMEND REROUTING**: Rerouting will prevent significant lost sales."
            elif roi > 0:
                recommendation = "⚠️ **EVALUATE REROUTING**: Consider alternatives."
            else:
                recommendation = "❌ **DO NOT REROUTE**: Rerouting costs exceed potential lost sales."
        else:
            net_benefit = -total_lost_sales  # All losses since no rerouting
            roi = 0
            recommendation = "❌ **NO REROUTING OPTIONS**: Accept lost sales or find alternative solutions."
        
        # Generate output with focus on potential lost sales
        output = f"**FINANCIAL IMPACT ANALYSIS - PANAMA CANAL DELAY**\n"
        output += f"Analysis for {affected_dc} with {delay_days}-day delay:\n\n"
        
        # Delayed shipments summary
        output += f"**DELAYED SHIPMENTS SUMMARY**\n"
        output += f"• Total shipments delayed: {len(delayed_items)}\n"
        output += f"• Total shipment value: ${total_shipment_value:,.2f}\n"
        output += f"• Delay period: {delay_days} days\n\n"
        
        # Potential lost sales analysis
        if items_with_losses.empty:
            output += f"**GOOD NEWS: No Lost Sales Expected**\n"
            output += f"{affected_dc} has sufficient inventory to cover the {delay_days}-day delay.\n"
            output += f"All delayed items have adequate Days of Supply.\n\n"
            output += "✅ **RECOMMENDATION**: No immediate action required. Monitor situation."
        else:
            output += f"**POTENTIAL LOST SALES ANALYSIS**\n"
            output += f"Items at risk of stockout during {delay_days}-day delay:\n\n"
            
            # Show detailed lost sales breakdown with proper column naming
            loss_cols = ['Item Number', 'Item Description', 'Qty', 'Days_of_Supply', 'Lost_Sales']
            
            loss_summary = items_with_losses[loss_cols].copy()
            loss_summary['Days_of_Supply'] = loss_summary['Days_of_Supply'].round(1)
            loss_summary['Lost_Sales'] = loss_summary['Lost_Sales'].round(2)
            
            # Rename columns to match agent expectations
            loss_summary = loss_summary.rename(columns={
                'Qty': 'Current Inventory',
                'Lost_Sales': 'Potential Lost Sales'
            })
            
            # Format currency column
            loss_summary['Potential Lost Sales'] = loss_summary['Potential Lost Sales'].apply(lambda x: f"${x:,.2f}")
            
            output += loss_summary.to_markdown(index=False)
            output += f"\n\n**TOTAL POTENTIAL LOST SALES: ${total_lost_sales:,.2f}**\n\n"
            
            # Cost-benefit analysis if rerouting data provided
            if rerouting_available:
                output += f"**COST-BENEFIT ANALYSIS**\n"
                output += f"• Potential Lost Sales: ${total_lost_sales:,.2f}\n"
                output += f"• Rerouting Cost: ${total_rerouting_cost:,.2f}\n"
                #output += f"• Net Benefit: ${net_benefit:,.2f}\n"
                #output += f"• ROI: {roi:.1f}%\n\n"
            
            output += f"{recommendation}\n\n"
            
            # Key insights
            output += f"**KEY INSIGHTS:**\n"
            output += f"• {len(items_with_losses)} items will experience stockouts\n"
            output += f"• Average stockout period: {items_with_losses['Stockout_Days'].mean():.1f} days\n"
            output += f"• Highest-impact item: {items_with_losses.loc[items_with_losses['Lost_Sales'].idxmax(), 'Item Description']}\n"
            
            if rerouting_available and container_count > 0:
                output += f"• {container_count} containers available for rerouting\n"
            
            output += f"• Break-even rerouting cost: ${total_lost_sales:,.2f}"
        
        return output
        
    except Exception as e:
        return f"Error calculating financial impact: {str(e)}"


