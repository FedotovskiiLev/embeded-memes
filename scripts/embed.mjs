#!/usr/bin/env node
/** Optional REAL E5 build. Needs internet on the first run; no API key. */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const MODEL='Xenova/multilingual-e5-small',REVISION='761b726dd34fb83930e26aab4e9ac3899aa1fa78';
async function main(){
 const {pipeline,env}=await import('@huggingface/transformers');env.cacheDir=path.join(root,'.cache','transformers');env.allowLocalModels=false;
 const data=JSON.parse(await fs.readFile(path.join(root,'catalog/catalog.json'),'utf8'));const docs=data.records.filter(r=>r.status==='reviewed');
 console.log('Loading',MODEL,REVISION,'q8');
 const extractor=await pipeline('feature-extraction',MODEL,{revision:REVISION,dtype:'q8'});
 const bundle={model:MODEL,revision:REVISION,runtime:'transformers.js 3.7.6',dtype:'q8',pooling:'mean',normalize:true,dimensions:384,catalog_hash:data.catalog_hash,ids:docs.map(r=>r.id),vectors:[]};
 for(let i=0;i<docs.length;i+=4){const texts=docs.slice(i,i+4).map(r=>'passage: '+[r.title,r.visual_description,r.reaction,...r.use_cases,...r.tags].join('. '));const out=await extractor(texts,{pooling:'mean',normalize:true});bundle.vectors.push(...out.tolist());console.log(`${Math.min(i+4,docs.length)}/${docs.length}`);}
 for(const v of bundle.vectors){if(v.length!==384||!v.every(Number.isFinite)||Math.abs(Math.hypot(...v)-1)>.02)throw new Error('Invalid E5 vector');}
 const json=JSON.stringify(bundle);await fs.writeFile(path.join(root,'data/embeddings/e5.json'),json+'\n');await fs.writeFile(path.join(root,'data/e5.js'),'window.EM_E5='+json.replaceAll('</','<\\/')+';\n');
 const {vectors,...manifest}=bundle;await fs.writeFile(path.join(root,'data/embeddings/e5-manifest.json'),JSON.stringify(manifest,null,2)+'\n');console.log('Saved E5 index. Commit data/e5.js and data/embeddings/e5*.json to share it.');
}
main().catch(e=>{console.error('E5 build failed; existing LSA search remains usable.\n'+e.stack);process.exitCode=1;});
