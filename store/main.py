"""Standalone working practice store. No payment, accounts, or external data."""
import json, os, time, uuid, threading
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse,JSONResponse
from pydantic import BaseModel,Field
from prometheus_client import Counter,Histogram,CONTENT_TYPE_LATEST,generate_latest
from starlette.responses import Response

APP=FastAPI(title='CloudShield Target Demo Store 2',version='3.0.0')
HERE=Path(__file__).resolve().parent
requests=Counter('ecs2_store_http_requests_total','Actual ECS2 HTTP requests',['route','status'])
latency=Histogram('ecs2_store_http_seconds','ECS2 HTTP duration')
orders=Counter('ecs2_store_orders_total','Synthetic orders')
PRODUCTS=[{'id':201,'name':'VPC Network Backpack','emoji':'🎒','category':'Accessories','price_cents':4800}, {'id':202,'name':'Cloud Security Hoodie','emoji':'🧥','category':'Apparel','price_cents':3600}, {'id':203,'name':'Performance Testing Mug','emoji':'☕','category':'Accessories','price_cents':1100}, {'id':204,'name':'Routing Notebook','emoji':'📘','category':'Stationery','price_cents':900}, {'id':205,'name':'DevOps Water Bottle','emoji':'🧴','category':'Accessories','price_cents':2200}, {'id':206,'name':'KooLab T-Shirt','emoji':'👕','category':'Apparel','price_cents':2900}]
BY_ID={p['id']:p for p in PRODUCTS};history={};lock=threading.Lock()
@APP.middleware('http')
async def meter(request:Request,call_next):
    t=time.monotonic();resp=await call_next(request);latency.observe(time.monotonic()-t);requests.labels(route=request.url.path,status=str(resp.status_code)).inc();return resp
@APP.get('/')
def index():return FileResponse(HERE/'store.html')
@APP.get('/assets/{name}')
def asset(name:str):
    if name not in ('store.js','store.css'):raise HTTPException(404)
    return FileResponse(HERE/name)
@APP.get('/health')
def health():return {'ok':True,'store':'Demo Store 2','ecs':'ECS2','version':'3.0.0'}
@APP.get('/api/products')
def products():return {'items':PRODUCTS,'total':len(PRODUCTS)}
@APP.get('/api/search')
def search(q:str=''):
    q=q.lower()[:80];data=[x for x in PRODUCTS if q in x['name'].lower()];return {'items':data,'total':len(data)}
@APP.get('/api/products/{product_id}')
def product(product_id:int):
    if product_id not in BY_ID:raise HTTPException(404)
    return BY_ID[product_id]
class Item(BaseModel):
    product_id:int
    quantity:int=Field(ge=1,le=10)
class Checkout(BaseModel):
    items:list[Item]=Field(min_length=1,max_length=8)
@APP.post('/api/checkout')
def checkout(body:Checkout):
    if any(x.product_id not in BY_ID for x in body.items):raise HTTPException(422,'Unknown product')
    total=sum(BY_ID[x.product_id]['price_cents']*x.quantity for x in body.items)
    record={'ok':True,'order_id':'ECS2-'+uuid.uuid4().hex[:10].upper(),'total_cents':total,'items':[x.model_dump() for x in body.items],'message':'Dummy order completed; no payment'}
    with lock: history[record['order_id']]=record
    orders.inc();return record
@APP.get('/api/slow')
def slow(ms:int=100):
    if not 1<=ms<=300:raise HTTPException(422)
    time.sleep(ms/1000);return {'ok':True,'simulated_database_ms':ms}
@APP.post('/api/login')
async def login(request:Request):
    body=await request.json();allowed=body.get('username')=='student' and body.get('password')=='classroom-demo'
    return {'ok':True,'message':'Demo credentials accepted'} if allowed else JSONResponse({'ok':False,'message':'Incorrect demo login'},status_code=401)
@APP.get('/api/download')
def download(mb:int=1):
    if not 1<=mb<=8:raise HTTPException(422)
    def gen():
        chunk=b'CloudShield-ECS2-performance-data\n'*2048
        remaining=mb*1048576
        while remaining:
            content=chunk[:min(remaining,len(chunk))];remaining-=len(content);yield content
    return StreamingResponse(gen(),media_type='application/octet-stream')
@APP.get('/metrics')
def metrics():return Response(generate_latest(),media_type=CONTENT_TYPE_LATEST)
