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

app = FastAPI()

# CORS middleware with specific origin for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend development server
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

# Sample prediction data - in a real app, this would come from a database or ML model
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
    
    today = datetime.now()
    
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
            
            # Create customer prediction
            customer = {
                "phone_number": phone,
                "date": date_str,
                "spare_parts": selected_parts
            }
            
            predictions.append(customer)
    
    return predictions

# Generate sample predictions
PREDICTIONS = generate_sample_predictions()

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
