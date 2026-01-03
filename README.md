## Kurulum

### 1) Sanal ortam
python -m venv venv
source venv/bin/activate

### 2) Paketler
pip install -r requirements.txt

### 3) Dataset
data/recipes.json dosyasına tarif JSON'unu koy.

### 4) Çalıştır
RECIPES_PATH=data/recipes.json python -m uvicorn app.main:app --reload --port 8001

### Swagger
http://127.0.0.1:8001/docs
