# BTC Price Action Strategy

This project implements a rule-based BTC Price Action Trading Strategy using FastAPI.

---

## 🚀 Getting Started

### 1. Create a Python Virtual Environment

```bash
python -m venv env
source env/bin/activate  # For Unix or MacOS
.\env\Scripts\activate  # For Windows
```

### 2. Install Dependencies

Make sure you have a `requirements.txt` file. Then run:

```bash
pip install -r requirements.txt
```

### 3. Run the FastAPI Server

Start your FastAPI application:

```bash
uvicorn main:app --reload
```

Your server will start running at: `http://127.0.0.1:8000`

---

## Testing via Postman

### 1. Open Postman

You can either:
- Create a new collection manually, or
- Import the [Postman collection](https://github.com/vikassrini/Falcon-Reality-Assesment/blob/main/Falcon%20Reality.postman_collection.json) to get started quickly.

### 2. Configure a POST Request

- Create a **POST** request with the URL:

```
http://127.0.0.1:8000/analyze
```

### 3. Set up the Request Body

- Click on **Body**.
- Select **form-data**.
- In the **key** column, type `file`, select **File** instead of text from the dropdown.
- In the **value** column, click on **Select Files**, and choose the file from your local machine that you wish to test.

### 4. Send the Request

- Click **Send**.

You will receive the analysis results based on your dataset.

---

## ✅ Response

The response will contain the detected entries according to the implemented BTC price action strategy rules.

---

## 🗃️ Project Structure

- `main.py`: FastAPI entry point.
- `strategy_module.py`: Contains logic for BTC price action analysis.
- `requirements.txt`: Python dependencies.

---

Happy trading! 📈🚀
