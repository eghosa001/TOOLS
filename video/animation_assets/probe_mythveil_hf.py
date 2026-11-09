from collections import Counter
from huggingface_hub import HfFileSystem
import pyarrow.parquet as pq
fs=HfFileSystem()
r="datasets/kaupane/chinese-painting-collection/default/train/"
for i in [0,1,2,3,4,5,6,8,10,12,15,18,20,22,25,30,35,40,80,150,300,340,350,360,370,372]:
    path=f"{r}part-{i:05d}.parquet"
    try:
        with fs.open(path,"rb") as f:
            pf=pq.ParquetFile(f)
            names=pf.schema_arrow.names
            keys=pf.read(columns=["__key__"]).column(0).to_pylist() if "__key__" in names else []
            cc=Counter(str(k).split("-")[0] for k in keys)
            print("PART",i,"rows",pf.metadata.num_rows,"sources",cc,"first",keys[:2],"last",keys[-2:],"columns",names,flush=True)
    except Exception as e:
        print("FAILED",i,repr(e)[:250],flush=True)
