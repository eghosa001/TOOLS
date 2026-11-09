from huggingface_hub import hf_hub_download,HfApi
import pyarrow.parquet as pq
from collections import defaultdict
REPO="kaupane/chinese-painting-collection"
f=hf_hub_download(REPO,filename="metadata/metadata.parquet",repo_type="dataset")
print("METADATA_FILE",f,flush=True)
p=pq.ParquetFile(f)
print("METADATA_SCHEMA",p.schema.names,flush=True)
cols=[c for c in ["image_id","source","shard","object_no","local_path","__url__","view_type","title"] if c in p.schema.names]
print("SAMPLE_COLS",cols,flush=True)
tab=p.read(columns=cols).to_pydict()
print("TOTAL",len(next(iter(tab.values()))),flush=True)
for i in [0,1,50,100,150,171,172,173,174,500,1000,1400,3000,4000,6000,9000,20000,80000]:
 if i<len(next(iter(tab.values()))):print("INDEX",i,{k:str(v[i])[:110] for k,v in tab.items()},flush=True)
for key in ["source","shard"]:
 if key in tab:
  o=defaultdict(lambda:[0,None,None])
  for i,v in enumerate(tab[key]):
   x=o[str(v)]
   x[0]+=1
   if x[1] is None:x[1]=i
   x[2]=i
  print("RANGE",key, sorted(o.items(), key=lambda x:x[1][1])[:25],flush=True)
