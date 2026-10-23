from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from app.detectors.risk import analyze_text, analyze_url, analyze_qr

app=FastAPI(title='DSPS Analysis Service',version='0.1.0')
class AnalysisInput(BaseModel):
 text:str|None=Field(default=None,max_length=10000)
 url:str|None=Field(default=None,max_length=2048)
 sender:str|None=Field(default=None,max_length=300)
 context:str|None=Field(default=None,max_length=5000)
@app.get('/health')
def health():return {'status':'ok','service':'dsps-ai','model':'heuristic-rules-0.1'}
@app.post('/analyze/{scan_type}')
def analyze(scan_type:str,payload:AnalysisInput):
 if scan_type=='url':
  if not payload.url and not payload.text:raise HTTPException(400,'Provide a URL to review.')
  return analyze_url(payload.url or payload.text)
 text=payload.text or payload.url or ''
 if not text.strip():raise HTTPException(400,'Provide text to review.')
 if scan_type=='qr':return analyze_qr(text)
 if scan_type not in ('sms','whatsapp','impersonation'):raise HTTPException(404,'Unknown scan type.')
 r=analyze_text(text,scan_type,payload.context or '')
 if scan_type=='impersonation' and payload.sender:r['explanation']+=f' Supplied sender details were considered as context: {payload.sender[:100]}.'
 return r
