/* Optional, user-initiated network loading. Default site does not load this module. */
const MODEL='Xenova/multilingual-e5-small';
const REVISION='761b726dd34fb83930e26aab4e9ac3899aa1fa78';
const LIBRARY='https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.7.6/dist/transformers.min.js';
let extractor,bundle;
const send=(message,percent)=>postMessage({type:'progress',message,percent});
function dbOpen(){return new Promise((resolve,reject)=>{const r=indexedDB.open('embeded-memes-neural-v1',1);r.onupgradeneeded=()=>r.result.createObjectStore('vectors');r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});}
async function cached(key,value){try{const db=await dbOpen();return await new Promise((resolve,reject)=>{const tx=db.transaction('vectors',value?'readwrite':'readonly');const req=value?tx.objectStore('vectors').put(value,key):tx.objectStore('vectors').get(key);req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);tx.oncomplete=()=>db.close();});}catch{return null;}}
function valid(b,hash,docs){return b&&b.model===MODEL&&b.revision===REVISION&&b.catalog_hash===hash&&b.dimensions===384&&b.ids.length===docs.length&&b.ids.every((id,i)=>id===docs[i].id)&&b.vectors.length===docs.length&&b.vectors.every(v=>v.length===384&&v.every(Number.isFinite));}
onmessage=async e=>{try{const m=e.data;if(m.type==='init'){
 const {pipeline,env}=await import(LIBRARY);env.allowLocalModels=false;env.useBrowserCache=true;env.backends.onnx.wasm.numThreads=1;
 extractor=await pipeline('feature-extraction',MODEL,{revision:REVISION,dtype:'q8',device:'wasm',progress_callback:p=>{if(p.status==='progress')send('Загрузка '+(p.file||'модели')+' · '+Math.round(p.progress||0)+'%',Math.min(35,(p.progress||0)*.35));}});
 const key=MODEL+'@'+REVISION+':'+m.hash;const local=m.prebuilt||await cached(key);
 if(valid(local,m.hash,m.docs))bundle=local;else{
  bundle={model:MODEL,revision:REVISION,runtime:'transformers.js 3.7.6',dtype:'q8',pooling:'mean',normalize:true,dimensions:384,catalog_hash:m.hash,ids:m.docs.map(d=>d.id),vectors:[]};
  for(let i=0;i<m.docs.length;i+=4){const batch=m.docs.slice(i,i+4).map(d=>'passage: '+d.text);const out=await extractor(batch,{pooling:'mean',normalize:true});bundle.vectors.push(...out.tolist());send(`Индексирование описаний: ${Math.min(i+4,m.docs.length)} / ${m.docs.length}`,35+65*Math.min(i+4,m.docs.length)/m.docs.length);}
  await cached(key,bundle);
 }
 postMessage({type:'ready',bundle});
 }else if(m.type==='query'){
  if(!extractor||!bundle)throw new Error('Модель не инициализирована');const out=await extractor('query: '+m.query,{pooling:'mean',normalize:true});const q=out.tolist()[0];const results=bundle.ids.map((id,i)=>[id,bundle.vectors[i].reduce((s,x,k)=>s+x*q[k],0)]);postMessage({type:'results',job:m.job,results});
 }}catch(e){postMessage({type:'error',message:String(e.message||e)});}};
