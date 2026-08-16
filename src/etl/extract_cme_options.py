"""
Module 1: Extract & Transform (CME .xlsx Sub-Header Parser)
Path: src/etl/extract_cme_options.py

Parses CME .xlsx files dynamically capturing Contract Month, Option Type,
and Tenor (Monthly vs Weekly) from embedded sub-headers.
"""

import pandas as pd
from pathlib import Path
import re
import warnings

# Suppress openpyxl warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data_raw"
STAGING_DIR = PROJECT_ROOT / "data_processed" / "staging"
STAGING_DIR.mkdir(parents=True, exist_ok=True)

def process_cme_directory(raw_folder: Path) -> pd.DataFrame:
    print("  -> Scanning data_raw/ for cme_voi_*.xlsx files...")
    
    valid_files = list(raw_folder.glob("cme_voi_*.xlsx"))
    
    if not valid_files:
        raise FileNotFoundError("[Error] No CME VOI .xlsx files found in data_raw/")
    
    stacked_data = []
    
    for file in valid_files:
        match = re.search(r'(\d{8})', file.name)
        if not match:
            continue
            
        raw_date = match.group(1)
        trade_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
        
        print(f"  -> Processing: {file.name} (Date: {trade_date})")
        
        df_raw = pd.read_excel(file, header=None)
        
        # Initialize our dynamic state trackers
        current_contract_month = None
        current_option_type = None
        current_tenor_type = None
        
        file_records = []
        is_options_section = False
        
        for idx, row in df_raw.iterrows():
            row_vals = [str(x).strip() for x in row.values if pd.notna(x)]
            if not row_vals:
                continue
                
            first_cell = str(row_vals[0]).strip()
            
            # 1. Detect Tenor (Monthly vs Weekly/EOM)
            if first_cell.upper().startswith("OPTION TYPE:"):
                is_options_section = True
                raw_tenor = first_cell.split(":", 1)[1].strip()
                
                # Standardize American Options to "Monthly" for clean analytics
                if "American" in raw_tenor:
                    current_tenor_type = "Monthly"
                else:
                    current_tenor_type = raw_tenor
                continue
                
            if not is_options_section:
                continue
                
            # 2. Detect Sub-Headers (e.g., "SEP 26 Calls")
            if len(row_vals) <= 2 and ('CALL' in first_cell.upper() or 'PUT' in first_cell.upper()):
                parts = first_cell.upper().split()
                if len(parts) >= 3:
                    current_contract_month = f"{parts[0]} {parts[1]}"
                    current_option_type = "CALL" if "CALL" in first_cell.upper() else "PUT"
                continue
                
            # 3. Skip actual table headers
            if first_cell.upper() == "STRIKE" or first_cell.upper() == "TOTALS":
                continue
                
            # 4. Valid Data Row Extraction
            if current_contract_month and current_option_type and current_tenor_type:
                try:
                    strike = float(first_cell.replace(',', ''))
                    if len(row_vals) >= 9:
                        volume = float(str(row_vals[4]).replace(',', '')) if str(row_vals[4]).replace(',', '').replace('.', '').isdigit() else 0.0
                        open_interest = float(str(row_vals[8]).replace(',', '')) if str(row_vals[8]).replace(',', '').replace('.', '').isdigit() else 0.0
                        
                        file_records.append({
                            'trade_date': trade_date,
                            'contract_month': current_contract_month,
                            'option_type': current_option_type,
                            'strike': strike,
                            'volume': volume,
                            'open_interest': open_interest,
                            'tenor': current_tenor_type  # CRITICAL FIX: Dynamic Tenor
                        })
                except ValueError:
                    continue
                    
        if file_records:
            stacked_data.extend(file_records)
            
    if not stacked_data:
        raise ValueError("No valid option data could be parsed from the files.")
        
    final_df = pd.DataFrame(stacked_data)
    final_df['usd_notional'] = final_df['open_interest'] * 100 * final_df['strike']
    
    return final_df

def main():
    print("=== Starting Module 1: Extract & Transform ===")
    df_cme = process_cme_directory(RAW_DIR)
    
    output_path = STAGING_DIR / "cme_voi_latest.csv"
    df_cme.to_csv(output_path, index=False)
    
    print("\n" + "="*65)
    print("      MODULE 1 (ETL) COMPLETE & STAGED")
    print("="*65)
    print(f"  -> Total Processed Records: {len(df_cme):,}")
    print(f"  -> Distinct Trade Dates   : {list(df_cme['trade_date'].unique())}")
    print(f"  -> Target File            : {output_path}")
    print("  -> Next Step              : Run src/etl/run_pipeline.py")
    print("="*65 + "\n")

if __name__ == "__main__":
    main()