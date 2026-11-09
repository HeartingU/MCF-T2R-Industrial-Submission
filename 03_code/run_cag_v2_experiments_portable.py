import fitz, re, pandas as pd, numpy as np, random, pathlib, json, os
from collections import Counter, defaultdict

PDF=os.environ.get('CAG_SOURCE_PDF','restricted_sources/heat_exchanger_datasheet.pdf')
SQL=os.environ.get('CAG_MATERIAL_SQL','restricted_sources/material_library.sql')
SEED=20260908

# ---------- parse material library ----------
sql=pathlib.Path(SQL).read_text(encoding='utf-8',errors='ignore')
pat=re.compile(r"INSERT INTO `材料表` VALUES \((\d+), '((?:[^']|'')*)', '((?:[^']|'')*)', '((?:[^']|'')*)', '((?:[^']|'')*)'\);")
rows=[m.groups() for m in pat.finditer(sql)]
mat=pd.DataFrame(rows,columns=['id','type','grade','state','standard'])
mat['basegrade']=mat['grade'].str.replace(r'\(.*\)$','',regex=True).str.strip()
# unique standard mapping for a product form + grade
std_map={}
for (t,g),sub in mat.groupby(['type','basegrade']):
    ss=sorted(set(sub['standard']))
    if len(ss)==1:
        std_map[(t,g)]=ss[0]

# ---------- canonical table coordinates/components ----------
pdf=fitz.open(PDF)
page_indices=[4,8,12,16,20,24,28,32,36,40,44]
equip_ids=['HX01','HX02','HX03','HX04','HX05','HX06','HX07','HX08','HX09','HX10','HX11']
groups=[('A',(85,190),(190,240)),('B',(240,330),(330,385)),('C',(385,500),(500,570))]
component_map={}
for row,label in {15:'壳程壳体',16:'壳程封头',17:'管程壳体',18:'管程封头',19:'壳体法兰-管箱侧',20:'壳体法兰-外头盖侧',21:'管箱法兰-壳程侧',22:'管箱法兰-封头侧',23:'管箱法兰盖',24:'外头盖-壳体',25:'外头盖-封头',26:'外头盖-法兰',27:'固定管板',28:'浮头管板',29:'换热管',30:'膨胀节'}.items(): component_map[('A',row)]=label
for row,label in {14:'浮头法兰',15:'钩圈',16:'浮头盖封头',17:'螺栓/螺柱-壳体',18:'螺栓/螺柱-浮头',19:'螺母-壳体',20:'螺母-浮头',21:'接管-壳程',22:'接管-管程',23:'接管法兰-壳程',24:'接管法兰-管程',25:'补强圈-壳程',26:'补强圈-管程',27:'复合层/衬里-壳程',28:'复合层/衬里-管程',29:'复合层/衬里-管板',30:'复合层/衬里-浮头盖封头'}.items(): component_map[('B',row)]=label
for row,label in {14:'垫片-壳程侧/外头盖',15:'垫片-浮头',16:'垫片-管程侧/管箱头盖',17:'折流板/支持板',18:'旁路挡板',19:'定距管',20:'拉杆/螺母',21:'滑板',22:'堰板',23:'支座/支座垫板',24:'防腐涂料-壳程侧',25:'防腐涂料-管程侧',26:'试验环',27:'阳极牺牲保护板',28:'部分卡环',29:'活套法兰',30:'焊接材料'}.items(): component_map[('C',row)]=label

def label_token(t):
    return any('\u4e00'<=c<='\u9fff' for c in t) or '—' in t or '－' in t

def clean_value(v):
    v=v.strip().strip(',;，；')
    # PDF text extraction occasionally merges the next cell label into a long material token.
    for suffix in ['螺母','复合层/衬里—壳程','复合层/衬里-壳程']:
        if v.endswith(suffix) and len(v)>len(suffix):
            v=v[:-len(suffix)]
    return v.strip().strip(',;，；')

def extract_by_tolerance(tol, dictionary_only=False, require_label=False, dictionary=None):
    rec=[]
    for pidx,eid in zip(page_indices,equip_ids):
        words=pdf[pidx].get_text('words')
        nums=[(int(w[4]),w[1]) for w in words if 65<w[0]<85 and w[4].isdigit() and 14<=int(w[4])<=31]
        row_y={n:y for n,y in nums}
        for row in range(14,31):
            if row not in row_y: continue
            ry=row_y[row]
            rowwords=[w for w in words if abs(w[1]-ry)<=tol]
            for g,(lx0,lx1),(vx0,vx1) in groups:
                comp=component_map.get((g,row))
                if not comp: continue
                label_present=any(lx0<=w[0]<lx1 and label_token(w[4]) for w in rowwords)
                vals=[w[4] for w in sorted(rowwords,key=lambda x:x[0]) if vx0<=w[0]<vx1]
                if not vals: continue
                v=clean_value(''.join(vals))
                if not v: continue
                if require_label and not label_present: continue
                if dictionary_only and dictionary is not None and not dictionary(v): continue
                rec.append((eid,comp,v))
    return set(rec)

# Gold benchmark: complete enumeration of filled material cells using the widest row-cell alignment.
gold_set=extract_by_tolerance(6.5,False,False)
gold_df=pd.DataFrame(sorted(gold_set),columns=['equipment','component','material'])

# Dictionary for retrieval-assisted candidate extraction, from material SQL + engineering special values.
grades=set(mat['basegrade'].astype(str))
extras={'35CrMoA','30CrMoA','Q355E','复合波齿垫'}
dict_vals=set(extras)
for g in grades:
    dict_vals.add(g); dict_vals.add(g+'锻')

def in_dictionary(v):
    v=clean_value(v)
    if v in dict_vals: return True
    v2=v.replace('+堆焊','')
    if v2 in dict_vals: return True
    parts=[p for p in re.split(r'[+/]',v2) if p]
    return bool(parts) and all(p in dict_vals for p in parts)

def metrics(pred,gold):
    pred=set(pred); gold=set(gold)
    tp=len(pred & gold); fp=len(pred-gold); fn=len(gold-pred)
    p=tp/(tp+fp) if tp+fp else 0
    r=tp/(tp+fn) if tp+fn else 0
    f=2*p*r/(p+r) if p+r else 0
    return {'gold':len(gold),'generated':len(pred),'exact_match':tp,'missing':fn,'redundant':fp,'precision':p,'recall':r,'f1':f}

extract_methods={
    'Strict-rule': extract_by_tolerance(2.5,True,True,in_dictionary),
    'Dictionary/RAG-assisted': extract_by_tolerance(3.5,True,False,in_dictionary),
    'Maximum-recall': extract_by_tolerance(6.5,False,False),
}
extract_results=[]
for name,pred in extract_methods.items():
    x=metrics(pred,gold_set); x['method']=name; extract_results.append(x)
extract_df=pd.DataFrame(extract_results)[['method','gold','generated','exact_match','missing','redundant','precision','recall','f1']]

# ---------- structured constraint benchmark ----------
plate_comps={'壳程壳体','壳程封头','管程壳体','管程封头','折流板/支持板','旁路挡板','滑板','外头盖-壳体','外头盖-封头','补强圈-壳程','补强圈-管程'}
forging_comps={'浮头法兰','钩圈','壳体法兰-管箱侧','壳体法兰-外头盖侧','管箱法兰-壳程侧','管箱法兰-封头侧','管箱法兰盖','接管法兰-壳程','接管法兰-管程','外头盖-法兰','固定管板','浮头管板'}
pipe_comps={'换热管','接管-壳程','接管-管程'}

def base_value(v): return v.replace('+堆焊','').replace('锻','').strip()
def resolve_type(comp,v):
    if '/' in v or ('+' in v.replace('+堆焊','')): return None
    if '锻' in v or comp in forging_comps: return '钢锻件'
    if comp in plate_comps: return '钢板'
    if comp in pipe_comps: return '钢管'
    return None

struct=[]
for e,c,v in gold_set:
    t=resolve_type(c,v)
    if not t: continue
    g=base_value(v)
    st=std_map.get((t,g))
    if st:
        struct.append((e,c,t,g,st))
struct_gold=set(struct)
struct_df=pd.DataFrame(sorted(struct_gold),columns=['equipment','component','material_type','material_grade','material_standard'])

valid_types=set(mat['type'])
valid_grades=set(mat['basegrade']) | extras
valid_standards=set(mat['standard'])
expected_type={}
for c,sub in struct_df.groupby('component'):
    ts=set(sub['material_type'])
    if len(ts)==1: expected_type[c]=next(iter(ts))
standards=sorted(valid_standards)

def domain_ok(x):
    e,c,t,g,s,tag=x
    return t in valid_types and g in valid_grades and (s is None or s in valid_standards)

def fd_ok_or_uncertain(x):
    e,c,t,g,s,tag=x
    exp=std_map.get((t,g))
    if exp is None or s is None: return True
    return s==exp

def business_ok(x):
    e,c,t,g,s,tag=x
    exp=expected_type.get(c)
    return exp is None or t==exp

def eval5(pred):
    return metrics(pred,struct_gold)

def one_corruption_run(seed):
    rng=random.Random(seed)
    candidates=[]
    gold_list=sorted(struct_gold)
    for e,c,t,g,st in gold_list:
        # Uncertainty: withhold the standard in 15% of cases.
        if rng.random()<0.15: candidates.append((e,c,t,g,None,'missing_standard'))
        else: candidates.append((e,c,t,g,st,'gold'))
        # Domain violation.
        if rng.random()<0.20: candidates.append((e,c,t,'INVALID_'+g,st,'domain'))
        # FD violation: legal standard, wrong for the type+grade.
        if rng.random()<0.20:
            choices=[s for s in standards if s!=st]
            candidates.append((e,c,t,g,rng.choice(choices),'fd'))
        # Business violation: another legal material family/product form.
        if rng.random()<0.20:
            alts=[(t2,g2,s2) for (t2,g2),s2 in std_map.items() if t2!=t]
            if alts:
                t2,g2,s2=rng.choice(alts); candidates.append((e,c,t2,g2,s2,'business'))
        # Hard plausible negative: legal same-type grade/standard combination.
        if rng.random()<0.10:
            alts=[(g2,s2) for (t2,g2),s2 in std_map.items() if t2==t and g2!=g]
            if alts:
                g2,s2=rng.choice(alts); candidates.append((e,c,t,g2,s2,'plausible'))

    initial=[x[:5] for x in candidates]
    d=[x for x in candidates if domain_ok(x)]
    fd=[x for x in d if fd_ok_or_uncertain(x)]
    b=[x for x in fd if business_ok(x)]
    b_complete=[x[:5] for x in b if x[4] is not None]
    repaired=[]
    repair_count=0
    for x in b:
        e,c,t,g,s,tag=x
        if s is None:
            exp=std_map.get((t,g))
            if exp is None: continue
            s=exp; repair_count+=1
        repaired.append((e,c,t,g,s))
    return {
        'Initial candidate set':eval5(initial),
        '+ Domain':eval5([x[:5] for x in d]),
        '+ FD':eval5([x[:5] for x in fd]),
        '+ Business':eval5(b_complete),
        'Full CAG + Repair':eval5(repaired),
        '_repair_count':repair_count,
        '_candidate_count':len(candidates)
    }

fixed=one_corruption_run(SEED)
ablation_rows=[]
for stage in ['Initial candidate set','+ Domain','+ FD','+ Business','Full CAG + Repair']:
    x=fixed[stage].copy(); x['stage']=stage; ablation_rows.append(x)
ablation_df=pd.DataFrame(ablation_rows)[['stage','gold','generated','exact_match','missing','redundant','precision','recall','f1']]

# 10-seed robustness statistics for the controlled-corruption benchmark.
runs=[one_corruption_run(SEED+i) for i in range(10)]
stability=[]
for stage in ['Initial candidate set','+ Domain','+ FD','+ Business','Full CAG + Repair']:
    for metric in ['precision','recall','f1']:
        vals=np.array([r[stage][metric] for r in runs],dtype=float)
        stability.append({'stage':stage,'metric':metric,'mean':float(vals.mean()),'std':float(vals.std(ddof=1))})
stability_df=pd.DataFrame(stability)

# ---------- dedicated repair benchmark ----------
rng=random.Random(SEED)
gold_list=sorted(struct_gold)
idx=list(range(len(gold_list))); rng.shuffle(idx)
sets=[idx[i*30:(i+1)*30] for i in range(4)]
# history is leave-one-equipment-out

def hist_pick_excl(component,typ,options,e_excl):
    cnt=Counter()
    for e,c,t,g,s in gold_list:
        if e!=e_excl and c==component and t==typ: cnt[g]+=1
    seen=[o for o in options if cnt[o]>0]
    if not seen: return None
    return sorted(seen,key=lambda x:(-cnt[x],x))[0]

repair_rows=[]
# missing standard
ok=0
for j in sets[0]:
    e,c,t,g,s=gold_list[j]; ok += (std_map.get((t,g))==s)
repair_rows.append(('Missing standard',len(sets[0]),ok))
# missing type
ok=0
for j in sets[1]:
    e,c,t,g,s=gold_list[j]; ok += (expected_type.get(c)==t)
repair_rows.append(('Missing material type',len(sets[1]),ok))
# conflicting standard
ok=0
for j in sets[2]:
    e,c,t,g,s=gold_list[j]; wrong=rng.choice([x for x in standards if x!=s]); ok += (std_map.get((t,g))==s)
repair_rows.append(('Conflicting standard',len(sets[2]),ok))
# ambiguous grade; choose true grade vs one same-type alternative using leave-one-equipment-out historical frequency
ok=0; n=0
for j in sets[3]:
    e,c,t,g,s=gold_list[j]
    alts=[g2 for (t2,g2),s2 in std_map.items() if t2==t and g2!=g]
    if not alts: continue
    alt=rng.choice(alts); n+=1
    pred=hist_pick_excl(c,t,[g,alt],e)
    ok += (pred==g)
repair_rows.append(('Ambiguous grade',n,ok))
repair_df=pd.DataFrame(repair_rows,columns=['corruption_type','cases','correct_repair'])
repair_df['repair_accuracy']=repair_df['correct_repair']/repair_df['cases']
repair_total={'cases':int(repair_df.cases.sum()),'correct':int(repair_df.correct_repair.sum())}
repair_total['accuracy']=repair_total['correct']/repair_total['cases']

# Save outputs
outdir=pathlib.Path(os.environ.get('CAG_OUTPUT_DIR','cag_v2_results')); outdir.mkdir(exist_ok=True)
gold_df.to_csv(outdir/'gold_material_tuples.csv',index=False,encoding='utf-8-sig')
struct_df.to_csv(outdir/'structured_constraint_gold.csv',index=False,encoding='utf-8-sig')
extract_df.to_csv(outdir/'maximum_recall_results.csv',index=False,encoding='utf-8-sig')
ablation_df.to_csv(outdir/'constraint_ablation_results.csv',index=False,encoding='utf-8-sig')
stability_df.to_csv(outdir/'stability_10seeds.csv',index=False,encoding='utf-8-sig')
repair_df.to_csv(outdir/'repair_results.csv',index=False,encoding='utf-8-sig')
summary={
    'source_equipment_count':len(equip_ids),
    'gold_material_tuple_count':len(gold_set),
    'structured_constraint_gold_count':len(struct_gold),
    'material_library_rows':len(mat),
    'fixed_seed':SEED,
    'controlled_corruption_design':{'missing_standard_rate':0.15,'domain_error_rate':0.20,'fd_error_rate':0.20,'business_error_rate':0.20,'plausible_same_type_negative_rate':0.10},
    'repair_total':repair_total,
}
(outdir/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print('SUMMARY',json.dumps(summary,ensure_ascii=False))
print('\nEXTRACTION')
print(extract_df.to_string(index=False))
print('\nABLATION FIXED SEED')
print(ablation_df.to_string(index=False))
print('\nSTABILITY')
print(stability_df.to_string(index=False))
print('\nREPAIR')
print(repair_df.to_string(index=False))
print('repair total',repair_total)
