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
