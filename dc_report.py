import os
import pandas as pd
import xlsxwriter
from datetime import datetime
from utils.logger import get_logger
from database import get_connection

logger = get_logger()


# =========================
# ✅ SAVE DATA TO DB
# =========================
def save_input_data(dc_date, distributor, amount):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO dc_entries (dc_date, distributor, amount)
        VALUES (?, ?, ?)
    """, (dc_date, distributor, amount))

    conn.commit()
    conn.close()


# =========================
# ✅ FETCH ALL DATA FROM DB
# =========================
def get_all_data():
    conn = get_connection()

    #df = pd.read_sql_query("SELECT dc_date, distributor, amount FROM dc_entries", conn)
    df = pd.read_sql_query(
    "SELECT id, dc_date, distributor, amount FROM dc_entries",
    conn
)

    conn.close()

    return df


# =========================
# ✅ MAIN RUN FUNCTION
# =========================
def run(dc_date=None, distributor=None, amount=None):
    try:
        logger.info("DC process started")

        # 📁 Output folder
        OUTPUT_DIR = os.path.join(os.getcwd(), "dc_output")
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # 📄 Excel file path
        output_file = os.path.join(
            OUTPUT_DIR,
            f"Daily_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

        # =========================
        # 👉 SAVE INPUT (IF GIVEN)
        # =========================
        if dc_date and distributor and amount is not None:
            save_input_data(dc_date, distributor, amount)

        # =========================
        # 👉 FETCH FULL DATA
        # =========================
        df = get_all_data()

        logger.info(f"Records fetched from DB: {len(df)}")

        # =========================
        # 👉 HANDLE EMPTY DB
        # =========================
        if df.empty:
            logger.warning("No data found in database")

        # =========================
        # 👉 CREATE EXCEL
        # =========================
        workbook = xlsxwriter.Workbook(output_file)
        ws = workbook.add_worksheet("New_DC_Report")

        # Write header
        headers = ["DC_Date", "Distributor", "Amount"]
        for col_num, col_name in enumerate(headers):
            ws.write(0, col_num, col_name)

        # Write data
        for row_idx in range(len(df)):
            ws.write(row_idx + 1, 0, str(df.iloc[row_idx]["dc_date"]))
            ws.write(row_idx + 1, 1, str(df.iloc[row_idx]["distributor"]))
            ws.write(row_idx + 1, 2, str(df.iloc[row_idx]["amount"]))

        workbook.close()

        logger.info(f"DC FILE CREATED: {output_file}")
        logger.info("DC process completed successfully")

        return {
            "status": "success",
            "output": output_file
        }

    except Exception as e:
        logger.error(f"DC process error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }    
