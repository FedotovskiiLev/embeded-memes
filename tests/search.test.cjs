const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const ROOT=path.join(__dirname,'..');global.window=global;
for(const f of ['data/catalog.js','data/lsa.js','src/search.js'])vm.runInThisContext(fs.readFileSync(path.join(ROOT,f),'utf8'),{filename:f});
const e=new MemeSearch(EM_DATA,EM_LSA),query=(q)=>e.search(q).map(x=>x.record.id);
for(const [q,id] of [['пишет в блокноте','HAMPTER_0127'],['записываю замечания','HAMPTER_0127'],['notebook','HAMPTER_0127'],['блакнот','HAMPTER_0127'],['лупа ищу подвох','HAMPTER_0406'],['нужен воздух кислород','HAMPTER_0332'],['слёзы радости','HAMPTER_0146'],['сдерживает слёзы','HAMPTER_0016'],['палец вверх','HAMPTER_0093'],['сердце руками','HAMPTER_0187'],['сижу с попкорном','HAMPTER_0427'],['моется в душе','HAMPTER_0430']])test('rank-1: '+q,()=>assert.equal(query(q)[0],id));
test('aliases and common missing initial letter',()=>{assert.equal(query('HAMPTER_0447')[0],'HAMPTER_0127');assert.equal(query('AMPTER_0127')[0],'HAMPTER_0127');});
test('notebook never retrieved for old eating/fork description',()=>{assert(!query('еда вилка').includes('HAMPTER_0127'));assert(!e.byId.get('HAMPTER_0127').tags.includes('fork'));});
test('near-blank source is deleted from collection (including quarantine)',()=>{assert(!e.byId.has('HAMPTER_0223'));assert(!query('HAMPTER_0223').length);assert(!e.search('HAMPTER_0223',{quarantine:true}).length);});
test('safe filter uses explicit flags, not substring deadpan',()=>{assert(!e.byId.get('HAMPTER_0001').content_warnings.includes('death'));assert(!e.search('рвота',{safe:true}).some(x=>x.record.id==='HAMPTER_0062'));});
test('variant filter and favorite subset',()=>{assert(!e.search('',{originals:true}).some(x=>x.record.related_to));assert.deepEqual(e.search('',{onlyIds:new Set(['HAMPTER_0127'])}).map(x=>x.record.id),['HAMPTER_0127']);});
test('LSA geometry and matching revision',()=>{assert.equal(e.dim,96);assert.equal(EM_LSA.ids.length,EM_DATA.records.filter(r=>r.status==='reviewed').length);const v=e.project('пишет в блокноте');assert(Math.abs(Math.hypot(...v)-1)<1e-5);assert.equal(new MemeSearch(EM_DATA,{...EM_LSA,catalog_hash:'wrong'}).lsa,null);});
test('unknown nonsense has no random fallback',()=>assert.equal(e.search('qqqzxvplm987').length,0));
test('similar excludes self and blank',()=>{const r=e.similar('HAMPTER_0127');assert(r.length);assert(r.every(x=>x.id!=='HAMPTER_0127'&&x.status==='reviewed'));});

test('generic magnifier query contains both true magnifier scenes',()=>assert.deepEqual(new Set(query('лупа').slice(0,2)),new Set(['HAMPTER_0083','HAMPTER_0406'])));
test('Russian judging inflection returns actual skeptical expressions',()=>assert(query('осуждает').some(id=>['HAMPTER_0007','HAMPTER_0011','HAMPTER_0041','HAMPTER_0098','HAMPTER_0210','HAMPTER_0339'].includes(id))));

test('curated angry-crying duplicate resolves to canonical original',()=>{assert.equal(e.resolve('HAMPTER_0213')?.id,'HAMPTER_0035');assert(query('плачет от злости').includes('HAMPTER_0035'));});

test('374 individual v3 readings with distinct emotional, comic and cultural layers',()=>{
 assert.equal(EM_DATA.records.length,374);
 assert.equal(EM_DATA.records.filter(r=>r.analysis?.version==='3.0.0').length,374);
 for(const r of EM_DATA.records){
  assert(r.analysis.nuanced_emotion.length>=40,`Missing nuance: ${r.id}`);
  assert(r.analysis.humor_mechanism.length>=30,`Missing humor: ${r.id}`);
  assert(r.analysis.cultural_context.length>=20,`Missing context: ${r.id}`);
  assert(r.analysis.not_to_confuse_with.length>=25,`Missing contrasts: ${r.id}`);
  assert(Array.isArray(r.analysis.subtext)&&r.analysis.subtext.length>0,r.id);
  assert(Array.isArray(r.analysis.search_phrases)&&r.analysis.search_phrases.length>0,r.id);
 }
});
test('search follows new subtle emotional and character interpretations',()=>{
 for(const [q,id] of [['записываю вашу очередную глупость','HAMPTER_0127'],['герой выбран уверенность не выдали','HAMPTER_0089'],['суровый вид минимум открытой реакции','HAMPTER_0347'],['смеюсь сквозь слёзы','HAMPTER_0146'],['Deltarune Ральзей','HAMPTER_0346'],['Gorillaz Murdoc','HAMPTER_0100']])
   assert.equal(query(q)[0],id,`Subtle/emotional query failed: ${q}`);
});
test('references carry explicit scope and are only on their cited cards',()=>{
 const r=e.byId.get('HAMPTER_0346');
 assert.equal(r.character_reference.character,'Ralsei / Ральзей');
 assert(r.analysis.sources.some(s=>s.id==='deltarune'&&s.url.startsWith('https://')));
 assert.equal(e.byId.get('HAMPTER_0127').analysis.sources.length,0);
 assert(e.byId.get('HAMPTER_0127').analysis.humor_mechanism.includes('протокол')||e.byId.get('HAMPTER_0127').analysis.humor_mechanism.length>40);
});
test('negative visual contrasts are not indexed as positive evidence',()=>{
 const r=e.byId.get('HAMPTER_0127');
 assert(!r.tags.includes('fork'));
 assert(!query('еда вилка').includes(r.id));
});
