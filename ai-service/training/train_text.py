"""Train a small reproducible baseline from a CSV with `text,label` columns.
Labels must be `legitimate` or `scam`. Synthetic demo data is not included as
performance evidence. Supply a lawful dataset explicitly via --data.
"""
import argparse, json
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_recall_fscore_support
import joblib

def main():
 p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--out',default='artifacts');a=p.parse_args()
 df=pd.read_csv(a.data)
 if not {'text','label'}.issubset(df.columns):raise SystemExit('CSV must contain text,label columns')
 df=df[['text','label']].dropna().drop_duplicates()
 if not set(df.label).issubset({'legitimate','scam'}):raise SystemExit('Labels must be legitimate or scam')
 if df.label.nunique()!=2 or df.label.value_counts().min()<2:raise SystemExit('Need at least two samples per class')
 xtr,xte,ytr,yte=train_test_split(df.text,df.label,test_size=.25,random_state=42,stratify=df.label)
 model=Pipeline([('tfidf',TfidfVectorizer(ngram_range=(1,2),max_features=30000)),('classifier',LogisticRegression(max_iter=1000,class_weight='balanced'))]);model.fit(xtr,ytr);pred=model.predict(xte)
 prec,rec,f1,_=precision_recall_fscore_support(yte,pred,labels=['scam','legitimate'],average='binary',pos_label='scam',zero_division=0)
 out=Path(a.out);out.mkdir(parents=True,exist_ok=True);joblib.dump(model,out/'text-baseline.joblib')
 metrics={'model_version':'tfidf-logreg-0.1','dataset_rows':len(df),'test_rows':len(yte),'accuracy':accuracy_score(yte,pred),'scam_precision':prec,'scam_recall':rec,'scam_f1':f1,'confusion_matrix_labels':['legitimate','scam'],'confusion_matrix':confusion_matrix(yte,pred,labels=['legitimate','scam']).tolist(),'classification_report':classification_report(yte,pred,zero_division=0),'split_seed':42,'note':'Metrics describe only the supplied dataset split; not validated real-world performance.'}
 (out/'metrics.json').write_text(json.dumps(metrics,indent=2));print(json.dumps(metrics,indent=2))
if __name__=='__main__':main()
