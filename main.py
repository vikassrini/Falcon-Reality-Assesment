from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import pandas as pd
from io import StringIO

# Import your functions
from strategy_module import detect_and_extend_ranges, detect_in_price_entries

app = FastAPI(title="BTC Strategy Detector", version="1.0")


@app.post("/analyze")
async def analyze_dataset(file: UploadFile = File(...)):
    try:
        # Read uploaded CSV file
        content = await file.read()
        df = pd.read_csv(StringIO(content.decode("utf-8")))

        # Ensure required columns are present
        required_cols = {'timestamp', 'open', 'high', 'low', 'close'}
        if not required_cols.issubset(df.columns):
            return JSONResponse(
                content={"error": f"Missing required columns: {required_cols - set(df.columns)}"},
                status_code=400
            )

        # Apply strategy detectors
        ranges_df, limit_entries = detect_and_extend_ranges(df)
        in_price_entries = detect_in_price_entries(df)

        results = []

        if not limit_entries.empty:
            results.append({
                "strategy": "Limit Catch Entry",
                "entries": limit_entries.to_dict(orient="records")
            })

        if not in_price_entries.empty:
            results.append({
                "strategy": "In-Price Entry",
                "entries": in_price_entries.to_dict(orient="records")
            })

        if not results:
            return {"result": "No strategy applicable"}

        return {"result": results}

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
