import os
from dotenv import load_dotenv
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from google import genai
import database

app = FastAPI()
database.tablolari_olustur()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

GEMINI_API_KEY = "BURAYA_GEMINI_API_ANAHTARINI_YAZ"

@app.get("/", response_class=HTMLResponse)
async def ana_sayfa(request: Request):
    musteriler, finanslar = database.verileri_getir()
    gelir = sum(f["tutar"] for f in finanslar if f["tur"] == "Gelir")
    gider = sum(f["tutar"] for f in finanslar if f["tur"] == "Gider")
    return templates.TemplateResponse(request=request, name="index.html", context={
        "musteriler": musteriler, "finanslar": finanslar,
        "toplam_gelir": gelir, "toplam_gider": gider,
        "net_bakiye": gelir - gider, "ai_analiz": None
    })

@app.post("/ai-analiz", response_class=HTMLResponse)
async def yapay_zeka_analiz(request: Request):
    musteriler, finanslar = database.verileri_getir()
    gelir = sum(f["tutar"] for f in finanslar if f["tur"] == "Gelir")
    gider = sum(f["tutar"] for f in finanslar if f["tur"] == "Gider")
    net = gelir - gider
    isler = "\n".join([f"- {m['ad_soyad']}: {m['proje_adi']} ({m['ucret']} TL) - {m['durum']}" for m in musteriler])
    hareketler = "\n".join([f"- {f['tur']}: {f['aciklama']} ({f['tutar']} TL)" for f in finanslar])
    prompt = f"Profesyonel finans danışmanı olarak en fazla 4 maddelik kısa Türkçe özet ve tavsiye ver:\nGelir: {gelir} TL, Gider: {gider} TL, Net: {net} TL\nİşler:\n{isler}\nHareketler:\n{hareketler}"
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        res = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        analiz = res.text
    except Exception as e:
        analiz = f"API Hatası (API anahtarını kontrol et): {str(e)}"
    return templates.TemplateResponse(request=request, name="index.html", context={
        "musteriler": musteriler, "finanslar": finanslar,
        "toplam_gelir": gelir, "toplam_gider": gider,
        "net_bakiye": net, "ai_analiz": analiz
    })

@app.post("/musteri-ekle")
async def yeni_musteri(ad_soyad: str = Form(...), proje_adi: str = Form(...), ucret: float = Form(...), durum: str = Form(...)):
    database.musteri_ekle(ad_soyad, proje_adi, ucret, durum)
    return RedirectResponse(url="/", status_code=303)

@app.post("/musteri-durum/{musteri_id}")
async def guncelle_musteri(musteri_id: int, durum: str = Form(...)):
    database.musteri_durum_guncelle(musteri_id, durum)
    return RedirectResponse(url="/", status_code=303)

@app.post("/musteri-sil/{musteri_id}")
async def sil_musteri(musteri_id: int):
    database.musteri_sil(musteri_id)
    return RedirectResponse(url="/", status_code=303)

@app.post("/finans-ekle")
async def yeni_finans(tur: str = Form(...), aciklama: str = Form(...), tutar: float = Form(...)):
    database.finans_ekle(tur, aciklama, tutar)
    return RedirectResponse(url="/", status_code=303)

@app.post("/finans-sil/{finans_id}")
async def sil_finans(finans_id: int):
    database.finans_sil(finans_id)
    return RedirectResponse(url="/", status_code=303)
