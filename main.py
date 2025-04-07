from config import NOTIF_API_KEY, NOTIF_BASE_URL
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import httpx
import asyncio
import os
import json
from datetime import datetime, timedelta
import random
import pandas as pd
import os.path

app = FastAPI()

# CORS middleware with specific origin for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

class SparePart(BaseModel):
    name: str
    price: int
    reason: str

class Customer(BaseModel):
    phone_number: str
    date: str
    spare_parts: List[SparePart]
    avg_km_per_month: float = 0.0

# Load data from dataset.csv
def load_prediction_data():
    dataset_path = os.path.join('model', 'dataset.csv')
    
    if not os.path.exists(dataset_path):
        print(f"Warning: {dataset_path} not found. Using sample data instead.")
        return generate_sample_predictions()
    
    try:
        # Read the CSV file
        df = pd.read_csv(dataset_path)
        
        # Check if required columns exist
        required_columns = ['tanggal_next_reminder', 'no_telp', 'rata_km_bln']
        for col in required_columns:
            if col not in df.columns:
                print(f"Warning: Column '{col}' not found in dataset. Using sample data instead.")
                return generate_sample_predictions()
        
        # Convert to list of dictionaries
        predictions = []
        spare_parts_options = [
            {"name": "Oil Filter", "price": 50000, "reason": "Dirty and clogged"},
            {"name": "Air Filter", "price": 75000, "reason": "Reduced performance"},
            {"name": "Spark Plug", "price": 25000, "reason": "Worn out"},
            {"name": "Chain", "price": 150000, "reason": "Stretched and worn"},
            {"name": "Brake Pads", "price": 100000, "reason": "Thin and worn"},
            {"name": "Coolant", "price": 45000, "reason": "Low level"},
            {"name": "Transmission Oil", "price": 80000, "reason": "Due for replacement"},
            {"name": "Battery", "price": 350000, "reason": "Low voltage"}
        ]
        
        # Get current date
        today = datetime.now().date()
        
        for _, row in df.iterrows():
            # Parse date from tanggal_next_reminder
            try:
                # Handle different date formats
                if isinstance(row['tanggal_next_reminder'], str):
                    # Try to parse the date string
                    date_str = row['tanggal_next_reminder'].split(' ')[0]  # Get only the date part
                else:
                    # If it's already a timestamp or other format
                    date_str = str(row['tanggal_next_reminder']).split(' ')[0]
                
                # Format the date as YYYY-MM-DD
                date_obj = pd.to_datetime(date_str).date()
                
                # Skip dates that are in the past
                if date_obj < today:
                    continue
                    
                formatted_date = date_obj.strftime('%Y-%m-%d')
                
                # Get phone number
                phone_number = str(row['no_telp'])
                if not phone_number.startswith('+'):
                    phone_number = '+' + phone_number
                
                # Get average km per month
                avg_km = float(row['rata_km_bln']) if not pd.isna(row['rata_km_bln']) else 0.0
                
                # Select 1-3 random spare parts
                num_parts = random.randint(1, 3)
                selected_parts = random.sample(spare_parts_options, num_parts)
                
                # Create customer prediction
                customer = {
                    "phone_number": phone_number,
                    "date": formatted_date,
                    "spare_parts": selected_parts,
                    "avg_km_per_month": round(avg_km, 2)
                }
                
                predictions.append(customer)
            except Exception as e:
                print(f"Error processing row: {e}")
                continue
        
        if not predictions:
            print("Warning: No valid predictions could be extracted from dataset. Using sample data instead.")
            return generate_sample_predictions()
        
        return predictions
    
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return generate_sample_predictions()

# Sample prediction data - used as fallback if dataset.csv is not available
def generate_sample_predictions(days=30):
    predictions = []
    spare_parts_options = [
        {"name": "Oil Filter", "price": 50000, "reason": "Dirty and clogged"},
        {"name": "Air Filter", "price": 75000, "reason": "Reduced performance"},
        {"name": "Spark Plug", "price": 25000, "reason": "Worn out"},
        {"name": "Chain", "price": 150000, "reason": "Stretched and worn"},
        {"name": "Brake Pads", "price": 100000, "reason": "Thin and worn"},
        {"name": "Coolant", "price": 45000, "reason": "Low level"},
        {"name": "Transmission Oil", "price": 80000, "reason": "Due for replacement"},
        {"name": "Battery", "price": 350000, "reason": "Low voltage"}
    ]
    
    phone_numbers = [
        "+62812345678", "+62823456789", "+62834567890", 
        "+62845678901", "+62856789012", "+62867890123"
    ]
    
    today = datetime.now().date()
    
    for i in range(days):
        current_date = today + timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Random number of customers for this day (0-5)
        num_customers = random.randint(0, 5)
        
        for j in range(num_customers):
            # Select random phone number
            phone = random.choice(phone_numbers)
            
            # Select 1-3 random spare parts
            num_parts = random.randint(1, 3)
            selected_parts = random.sample(spare_parts_options, num_parts)
            
            # Random average km per month between 500 and 2000
            avg_km = round(random.uniform(500, 2000), 2)
            
            # Create customer prediction
            customer = {
                "phone_number": phone,
                "date": date_str,
                "spare_parts": selected_parts,
                "avg_km_per_month": avg_km
            }
            
            predictions.append(customer)
    
    return predictions

# Load predictions from dataset
PREDICTIONS = load_prediction_data()

@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse("static/index.html")

@app.get("/api/predictions")
async def get_predictions():
    return {"predictions": PREDICTIONS}

@app.get("/api/predictions/{date}")
async def get_predictions_by_date(date: str):
    date_predictions = [p for p in PREDICTIONS if p["date"] == date]
    return {"predictions": date_predictions}

@app.post("/api/send-notification", tags=["Notifications"])
async def send_notification(customers: List[Customer]):
    
    # Check if notification API keys are available
    if not NOTIF_API_KEY or not NOTIF_BASE_URL:
        return JSONResponse(
            status_code=503,
            content={"message": "Notification service not configured"})
    
    for customer in customers:
        
        phone_number = customer.phone_number
        date = customer.date
        spare_parts = customer.spare_parts
        
        message = f"Halo {phone_number},\n\nJangan lupa service motor kalian pada tanggal {customer.date}.\n\nBerikut adalah prediksi spare part yang harus diganti:\n"
        
        for i, spare_part in enumerate(spare_parts):
            message += f"{i+1}. {spare_part.name} - {spare_part.reason}\n"
        
        # print(message)
        
        data = {
            "apikey": NOTIF_API_KEY,
            "receiver": phone_number,
            "mtype": "image",
            "text": message,
            "url": "https://www.suarapemredkalbar.com/public/media/post/2021/01/12/728x528/1610461202_ayo_ke_ahass_konsumen_terbaik_astra_motor_bisa_menikmati_layanan_terbaik_servis_kendaraan.jpeg"
        }
        
        # print(data)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(NOTIF_BASE_URL + "api/send-message", json=data)
                
                # print(f"Response status: {response.status_code}")
                # print(f"Response content: {response.text}")
            
            if response.status_code != 200:
                return JSONResponse(
                    status_code=500,
                    content={"message": f"Failed to send notification: {response.text}"})
        except Exception as e:
            print(f"Error sending notification: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"message": f"Error sending notification: {str(e)}"})
    
    
    return {"message": "Notification sent successfully"}

# Health check endpoint for Cloud Run
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable or default to 8080
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(app, host="0.0.0.0", port=port)
