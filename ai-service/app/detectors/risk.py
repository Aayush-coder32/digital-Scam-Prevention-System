import re, uuid
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs, unquote
from ipaddress import ip_address

SCAM_TERMS={
 'urgency':(r'\b(immediately|urgent|within\s+\d+\s*(?:hours?|mins?)|act now|आज ही|तुरंत|अभी|जल्दी)\b','Urgency or time pressure',15),
 'credential':(r'\b(otp|one.time.password|pin|password|cvv|share.*(?:code|otp)|verify.*account|kyc)\b','Requests sensitive credentials or account verification',25),
 'payment':(r'\b(pay|payment|transfer|upi|send money|fee|deposit|processing charge|भेजें|जमा|पेमेंट)\b','Unexpected payment or transfer request',18),
 'threat':(r'\b(blocked|suspend|arrest|police|fine|penalty|legal action|account.*close|बंद|गिरफ्तार)\b','Threat or account suspension pressure',20),
 'prize':(r'\b(lottery|winner|prize|won|reward|claim.*cash|इनाम|लॉटरी)\b','Unexpected prize or reward claim',18),
 'job':(r'\b(work from home|daily income|easy money|job offer|registration fee|घर बैठे|नौकरी)\b','Job offer or easy-income language',12),
 'remote':(r'\b(anydesk|teamviewer|remote access|screen share)\b','Request for remote access or screen sharing',25),
 'shortlink':(r'https?://(?:bit\.ly|tinyurl\.com|t\.co|rb\.gy|cutt\.ly|is\.gd)/\S+','Shortened URL hides its destination',15),
}
DEMO_HIGH_RISK_HOSTS={
 'bank-verify-example.test',
 'upi-refund-example.test',
 'free-cashback-example.test',
 'fake-kyc-example.invalid',
 'account-security-example.test',
}
def level(score): return 'Low' if score<25 else 'Medium' if score<50 else 'High' if score<75 else 'Critical'
def result(scan_type,score,signals,explanation,actions,method='heuristic_rules'):
 score=max(0,min(100,int(score)));return {'scan_id':str(uuid.uuid4()),'scan_type':scan_type,'risk_score':score,'risk_level':level(score),'detection_method':method,'suspicious_indicators':signals,'explanation':explanation,'recommended_actions':actions,'confidence':0.55 if signals else 0.3,'model_version':'rules-baseline-0.1','provider_status':{'threat_intelligence':'not_configured','ml_model':'not_configured'},'created_at':datetime.now(timezone.utc).isoformat()}
def analyze_text(text,scan_type='sms',context=''):
 text=(text or '').strip(); lower=text.lower(); signals=[]; score=0
 for key,(pattern,description,weight) in SCAM_TERMS.items():
  if re.search(pattern,lower,re.I): signals.append({'code':key,'description':description,'method':'heuristic'}); score+=weight
 urls=re.findall(r'https?://[^\s<>"\']+',text,re.I)
 for url in urls:
  host=urlparse(url).hostname or ''
  if host and (host.count('.')>=3 or re.search(r'\d{4,}',host)): signals.append({'code':'url_structure','description':f'Link hostname may be deceptive: {host}','method':'heuristic'}); score+=12
 if len(signals)>4: score-=min(18,(len(signals)-4)*4)
 expl='Signals were found that can be associated with scam tactics. This is a heuristic review and context can change the assessment.' if signals else 'No strong warning patterns were detected by the baseline rules. This does not establish that the message is safe.'
 return result(scan_type,score,signals,expl,['Do not share passwords, PINs, or OTPs.','Verify requests by contacting the organization using independently obtained details.','Avoid sending money under pressure.'], 'heuristic_rules')
def analyze_url(url):
 raw=(url or '').strip(); candidate=raw if '://' in raw else 'https://'+raw
 try: p=urlparse(candidate); host=p.hostname or ''; port=p.port
 except Exception: return result('url',60,[{'code':'malformed','description':'The URL could not be parsed safely.','method':'heuristic'}],'The URL format is malformed or ambiguous.',['Do not open the link. Verify the sender independently.'])
 signals=[];score=0
 if host.lower().rstrip('.') in DEMO_HIGH_RISK_HOSTS:
  return result('url',90,[{'code':'known_demo_scam_domain','description':'This demo domain is configured as a high-risk scam training example.','method':'heuristic'}],'This hostname matches a configured scam-training example associated with fake verification, refunds, cashback, KYC, or account-security requests. The link was not opened.',['Do not open the link or enter any information.','Verify the request through the organization’s official app or website.','Never share an OTP, PIN, password, or payment details.'])
 if p.scheme not in ('https','http'): signals.append({'code':'scheme','description':'Unexpected URL scheme.','method':'heuristic'});score+=25
 if not host or '.' not in host: signals.append({'code':'host','description':'Hostname is missing or unusual.','method':'heuristic'});score+=30
 try:
  ip=ip_address(host)
  if ip: signals.append({'code':'ip_host','description':'The link uses a raw IP address instead of a named domain.','method':'heuristic'});score+=25
 except ValueError: pass
 if host.startswith('xn--') or '.xn--' in host: signals.append({'code':'punycode','description':'Hostname contains internationalized punycode labels.','method':'heuristic'});score+=20
 if host.count('.')>=4: signals.append({'code':'subdomains','description':'Hostname has many subdomain levels.','method':'heuristic'});score+=12
 if port and port not in (80,443): signals.append({'code':'port','description':f'Unusual port number: {port}.','method':'heuristic'});score+=15
 if '@' in p.netloc: signals.append({'code':'at_sign','description':'The URL contains @ in its authority, which can obscure the destination.','method':'heuristic'});score+=20
 if p.scheme=='http': signals.append({'code':'no_https','description':'The link does not use HTTPS. Encryption status alone does not prove legitimacy.','method':'heuristic'});score+=8
 signals.append({'code':'reputation_unavailable','description':'Threat reputation lookup is not configured.','method':'provider_status'})
 return result('url',score,signals,f'Parsed hostname: {host or "unavailable"}. The link was not opened; no reputation provider is configured.', ['Do not open unexpected links.','Confirm the domain with the organization through an official source.','HTTPS does not establish that a site is trustworthy.'])
def analyze_qr(text):
 raw=(text or '').strip()
 if raw.lower().startswith('upi://'):
  p=urlparse(raw);q=parse_qs(p.query);payee=(q.get('pa')or[''])[0];name=(q.get('pn')or[''])[0];amount=(q.get('am')or[''])[0];signals=[];score=5
  if not payee or '@' not in payee:signals.append({'code':'upi_id','description':'UPI payee identifier is missing or malformed.','method':'heuristic'});score+=35
  if amount and not re.fullmatch(r'\d+(\.\d{1,2})?',amount):signals.append({'code':'amount','description':'Payment amount format is malformed.','method':'heuristic'});score+=25
  return result('qr',score,signals,f'Decoded payment request: payee name={name or "not supplied"}; UPI ID={payee or "not supplied"}; amount={amount or "not specified"}. These details are not verified.', ['Compare the UPI ID and amount with the intended recipient before proceeding.','Never share your UPI PIN or OTP.','Decoding did not initiate a payment.'])
 if re.match(r'https?://',raw,re.I): r=analyze_url(raw);r['scan_type']='qr';r['explanation']='The QR content is a URL. '+r['explanation'];return r
 return result('qr',20,[{'code':'qr_content','description':'QR content is not a recognized UPI payment URI or URL.','method':'heuristic'}],'QR content was reviewed as plain data; no payment action was taken.',['Confirm the QR source with the intended recipient.','Do not enter a PIN or OTP after scanning an unexpected code.'])
