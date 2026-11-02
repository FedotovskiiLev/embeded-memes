/* Local, inspectable search. No requests, no third-party runtime. */
(function(root){
'use strict';
class MemeSearch {
 constructor(data, lsa=null){
  this.data=data;this.cfg=data.search_config;this.stop=new Set(this.cfg.stopwords);this.records=data.records;this.byId=new Map(this.records.map(r=>[r.id,r]));this.aliases=data.aliases||{};
  this.cs=this.cfg.concepts.map(c=>({...c,sets:c.synonyms.map(s=>this.tokens(s))}));
  this.active=this.records.filter(r=>r.status==='reviewed');this.N=this.active.length;this.df=new Map();this.docs=new Map();let total=0;
  for(const r of this.active){const terms=r.search_tokens||this.expand(r.search_text);const counts=new Map();for(const t of terms)counts.set(t,(counts.get(t)||0)+1);for(const t of counts.keys())this.df.set(t,(this.df.get(t)||0)+1);total+=terms.length;this.docs.set(r.id,{counts,len:terms.length,title:this.norm(r.title),tags:this.norm(r.tags.join(' ')),uses:this.norm(r.use_cases.join(' '))});}
  this.avg=total/Math.max(1,this.N);this.vocab=[...this.df.keys()].filter(t=>!t.startsWith('concept_'));this.lsa=null;
  if(lsa&&lsa.catalog_hash===data.catalog_hash){this.lsa=lsa;this.dim=lsa.dimensions;this.V=this.decode(lsa.vectors_b64);this.C=this.decode(lsa.projection_b64);this.vi=new Map(lsa.vocabulary.map((t,i)=>[t,i]));this.row=new Map(lsa.ids.map((id,i)=>[id,i]));}
 }
 norm(s){return String(s||'').toLowerCase().replace(/ё/g,'е');}
 stem(t){for(const x of this.cfg.suffixes)if(t.length-x.length>=3&&t.endsWith(x))return t.slice(0,-x.length);return t;}
 tokens(s){return (this.norm(s).match(/[a-zа-я0-9]+/g)||[]).filter(t=>t.length>1&&!this.stop.has(t)).map(t=>this.stem(t));}
 conceptIds(s){const ts=new Set(this.tokens(s));return this.cs.filter(c=>c.sets.some(set=>set.length&&set.every(t=>ts.has(t)))).map(c=>c.id);}
 expand(s){const cs=this.conceptIds(s).map(x=>'concept_'+x);return this.tokens(s).concat(cs,cs);}
 decode(s){const bin=typeof atob==='function'?atob(s):Buffer.from(s,'base64').toString('binary');const arr=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)arr[i]=bin.charCodeAt(i);return new Float32Array(arr.buffer);}
 project(q){if(!this.lsa)return null;const counts=new Map();for(const t of this.expand(q)){const j=this.vi.get(t);if(j!==undefined)counts.set(j,(counts.get(j)||0)+1);}if(!counts.size)return null;const v=new Float32Array(this.dim);for(const [j,c] of counts){const w=(1+Math.log(c))*this.lsa.idf[j];for(let k=0;k<this.dim;k++)v[k]+=w*this.C[j*this.dim+k];}let norm=0;for(const x of v)norm+=x*x;norm=Math.sqrt(norm)||1;for(let k=0;k<v.length;k++)v[k]/=norm;return v;}
 cosine(id,v){const i=this.row?.get(id);if(i===undefined||!v)return 0;let s=0;for(let k=0;k<this.dim;k++)s+=this.V[i*this.dim+k]*v[k];return s;}
 resolve(id){const clean=String(id).toUpperCase().replace(/^AMPTER_/,'HAMPTER_');return this.byId.get(this.aliases[clean]||clean);}
 distance1(a,b){if(Math.abs(a.length-b.length)>1)return false;let i=0,j=0,e=0;while(i<a.length&&j<b.length){if(a[i]===b[j]){i++;j++;continue;}if(++e>1)return false;if(a.length>b.length)i++;else if(b.length>a.length)j++;else{i++;j++;}}return e+(i<a.length||j<b.length?1:0)<=1;}
 fuzzy(t){if(this.df.has(t)||t.length<4)return [t];const out=this.vocab.filter(w=>this.distance1(w,t)).sort((a,b)=>(this.df.get(b)||0)-(this.df.get(a)||0));return out.slice(0,5);}
 search(query='',options={}){
  const q=this.norm(query).trim(),exact=this.resolve(q);if(/^h?ampter_[0-9]{4}$/i.test(q)&&!exact)return [];const terms=this.tokens(q),concepts=this.conceptIds(q).map(c=>'concept_'+c),qv=options.mode==='words'?null:this.project(q);const expanded=terms.map(t=>this.fuzzy(t));
  let result=[];
  for(const r of this.records){
   if(r.status!=='reviewed'&&!options.quarantine)continue;
   if(options.collection&&r.collection_id!==options.collection)continue;
   if(options.mood&&!r.concepts.includes(options.mood))continue;
   if(options.topic&&!r.concepts.includes(options.topic))continue;
   if(options.safe&&r.content_warnings.length)continue;
   if(options.originals&&r.related_to)continue;
   if(options.minResolution&&Math.min(r.width,r.height)<Number(options.minResolution))continue;
   if(options.onlyIds&&!options.onlyIds.has(r.id))continue;
   if(exact){if(r.id===exact.id)result.push({record:r,score:1000,matched:1});continue;}
   let score=0,matched=0;const d=this.docs.get(r.id);
   if(q&&d){
    for(const alternatives of expanded){let best=0;for(const t of alternatives){const tf=d.counts.get(t)||0;if(!tf)continue;const idf=Math.log(1+(this.N-(this.df.get(t)||0)+.5)/((this.df.get(t)||0)+.5));const value=idf*tf*2.2/(tf+1.2*(.25+.75*d.len/this.avg));best=Math.max(best,value);}if(best>0)matched++;score+=best;}
    for(const t of concepts){if(d.counts.has(t))score+=1.25;}
    if(terms.length)score*=.35+.65*matched/terms.length;
    if(d.title.includes(q))score+=12;if(d.tags.includes(q))score+=8;if(d.uses.includes(q))score+=10;
    if(qv)score+=Math.max(0,this.cosine(r.id,qv))*3;
    // Avoid unrelated fall-through: lexical evidence, a shared concept, or a strong vector match.
    if(!matched&&!concepts.some(t=>d.counts.has(t))&&(!qv||this.cosine(r.id,qv)<.42))continue;
    if(concepts.length>1){const covered=concepts.filter(t=>d.counts.has(t)).length;score*=.4+.6*covered/concepts.length;}
    if(r.related_to)score*=.96;
   }else if(q&&!exact)continue;
   if(exact&&r.id===exact.id)score+=1000;
   if(q&&score<=0)continue;
   result.push({record:r,score,matched});
  }
  const featured=['HAMPTER_0127','HAMPTER_0406','HAMPTER_0187','HAMPTER_0332','HAMPTER_0035','HAMPTER_0397','HAMPTER_0093','HAMPTER_0427','HAMPTER_0062','HAMPTER_0079','HAMPTER_0055','HAMPTER_0237'];
  result.sort((a,b)=>{if(options.sort==='id')return a.record.id.localeCompare(b.record.id);if(options.sort==='resolution')return b.record.width*b.record.height-a.record.width*a.record.height;if(q)return b.score-a.score||a.record.id.localeCompare(b.record.id);const ai=featured.indexOf(a.record.id),bi=featured.indexOf(b.record.id);return (ai<0?999:ai)-(bi<0?999:bi)||a.record.id.localeCompare(b.record.id);});
  if(q&&!exact&&result.length){const top=Math.max(...result.map(x=>x.score));result=result.filter(x=>x.score>=Math.max(.8,top*.22));}
  return result;
 }
 similar(id,n=8){const r=this.byId.get(id);if(!r)return[];if(!this.lsa)return (r.similar_ids||[]).slice(0,n).map(id=>this.byId.get(id)).filter(Boolean);const i=this.row.get(id);if(i===undefined)return[];const v=this.V.subarray(i*this.dim,(i+1)*this.dim);return this.active.filter(r=>r.id!==id).map(r=>({r,s:this.cosine(r.id,v)})).sort((a,b)=>b.s-a.s).slice(0,n).map(x=>x.r);}
}
root.MemeSearch=MemeSearch;if(typeof module!=='undefined')module.exports=MemeSearch;
})(typeof window!=='undefined'?window:globalThis);
