from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from modules import dc_report
from database import get_connection

app = FastAPI()

# =========================
# MODEL
# =========================
class DCEntry(BaseModel):
    dc_date: str
    distributor: str
    amount: float

# =========================
# HOME
# =========================
@app.get("/")
def home():
    return {"status": "API running"}

# =========================
# GET DATA
# =========================
@app.get("/dc/data")
def get_data():
    df = dc_report.get_all_data()
    return df.to_dict(orient="records")

# =========================
# ADD ENTRY
# =========================
@app.post("/dc/add")
def add_entry(entry: DCEntry):
    return dc_report.run(entry.dc_date, entry.distributor, entry.amount)

# =========================
# ✏️ EDIT ENTRY
# =========================
@app.put("/dc/edit/{entry_id}")
def edit_entry(entry_id: int, entry: DCEntry):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE dc_entries
        SET dc_date=?, distributor=?, amount=?
        WHERE id=?
    """, (entry.dc_date, entry.distributor, entry.amount, entry_id))

    conn.commit()
    conn.close()

    return {"status": "success"}

# =========================
# DELETE
# =========================
@app.delete("/dc/delete/{entry_id}")
def delete_entry(entry_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM dc_entries WHERE id=?", (entry_id,))
    conn.commit()
    conn.close()

    return {"status": "success"}

# =========================
# DOWNLOAD
# =========================
@app.get("/dc/download")
def download():
    result = dc_report.run()

    if result["status"] != "success":
        return result

    return FileResponse(
        result["output"],
        filename=os.path.basename(result["output"]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
