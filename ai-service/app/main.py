from fastapi import FastAPI, HTTPException, UploadFile, File
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
@app.post('/analyze/qr-image')
async def analyze_qr_image(file:UploadFile=File(...)):
 if file.content_type not in ('image/png','image/jpeg','image/webp'):
  raise HTTPException(415,'Upload a PNG, JPEG, or WebP image.')
 content=await file.read(5*1024*1024+1)
 if len(content)>5*1024*1024:raise HTTPException(413,'Image exceeds 5 MB.')
 try:
  import cv2, numpy as np
 except ImportError:
  raise HTTPException(503,'QR decoding is unavailable because the image decoder is not installed.')
 try:
  image=cv2.imdecode(np.frombuffer(content,dtype=np.uint8),cv2.IMREAD_COLOR)
  if image is None:raise ValueError('invalid image bytes')
  height,width=image.shape[:2]
  if max(height,width)>2400:
   scale=2400/max(height,width)
   image=cv2.resize(image,(int(width*scale),int(height*scale)),interpolation=cv2.INTER_AREA)
  detector=cv2.QRCodeDetector()
  decoded=detector.detectAndDecode(image)
  data=decoded[0] if isinstance(decoded,tuple) else decoded
  if not data and hasattr(detector,'detectAndDecodeMulti'):
   multi=detector.detectAndDecodeMulti(image)
   if isinstance(multi,tuple) and len(multi)>1 and multi[0]:
    data='\n'.join(value for value in multi[1] if value)
 except Exception:
  raise HTTPException(400,'Image could not be decoded. Try a clearer, well-lit QR image.')
 if not data:raise HTTPException(422,'No supported QR code was found in this image.')
 try:
  return analyze_qr(data)
 except Exception:
  raise HTTPException(400,'The decoded QR data could not be interpreted safely.')

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