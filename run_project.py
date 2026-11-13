"""Standalone UniTime v2.4 Tabu Search baseline. Python 3.10+, standard library only.
Supports time/room/instructor overlap, room capacity, committed placements, and preferences.
Does not implement every UniTime group/student/room-sharing constraint: see README.
"""
import argparse, csv, json, random, time, xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


def load(path):
    root = ET.parse(path).getroot()
    rooms = {int(r.get('id')): {'capacity': int(r.get('capacity','0')), 'constraint': r.get('constraint','true') == 'true', 'discouraged':r.get('discouraged') == 'true'} for r in root.find('rooms')}
    classes = {}
    for e in root.find('classes'):
        cid = int(e.get('id'))
        times = [{'days':t.get('days','0000000'),'start':int(t.get('start','0')),'length':int(t.get('length','0')),'pref':float(t.get('pref','0')),'solution':t.get('solution')=='true'} for t in e.findall('time')]
        choices = [{'id':int(r.get('id')),'pref':float(r.get('pref','0')),'solution':r.get('solution')=='true'} for r in e.findall('room')]
        classes[cid] = {'times':times,'rooms':choices,'nr':int(e.get('nrRooms','1')),'instructors':set(int(i.get('id')) for i in e.findall('instructor')),'limit':int(e.get('classLimit',e.get('minClassLimit','0'))),'ratio':float(e.get('roomToLimitRatio','1')),'dates':e.get('dates',''),'committed':e.get('committed')=='true'}
    return rooms,classes


def overlap(a,b,da,db):
    if da and db and not any(x=='1' and y=='1' for x,y in zip(da,db)):return False
    return any(x=='1' and y=='1' for x,y in zip(a['days'],b['days'])) and a['start']<b['start']+b['length'] and b['start']<a['start']+a['length']


def valid_room_sets(c,rooms):
    if c['nr']==0:return [()]
    options=[r for r in c['rooms'] if r['id'] in rooms and rooms[r['id']]['capacity']>=c['limit']*c['ratio']]
    options.sort(key=lambda x:x['pref'])
    if c['nr']==1:return [(r['id'],) for r in options]
    # Multi-room classes: choose combinations from available room domain.
    from itertools import combinations
    return [tuple(r['id'] for r in comb) for comb in combinations(options[:16],c['nr'])][:200]


def placement_cost(cid,p,classes,rooms):
    c=classes[cid]
    if p is None:return 0
    t,rr=p
    prefs={r['id']:r['pref'] for r in c['rooms']}
    return t['pref']+sum(prefs.get(r,0)+ (10 if rooms[r]['discouraged'] else 0) for r in rr)


def score(schedule,classes,rooms):
    # Primary: unassigned + hard conflicts; secondary: preferences.
    hard=0; soft=0.0; active=[]
    for cid,p in schedule.items():
        if p is None:
            if not classes[cid]['committed']:hard+=1
            continue
        t,rr=p; c=classes[cid]
        soft+=placement_cost(cid,p,classes,rooms)
        if len(rr)!=c['nr'] or len(set(rr))!=len(rr):hard+=1
        for rid in rr:
            if rid not in rooms or rooms[rid]['capacity']<c['limit']*c['ratio']:hard+=1
        active.append((cid,t,rr))
    # Index possible conflicts by instructor and room to avoid O(n^2) full scan.
    idx=defaultdict(list)
    for cid,t,rr in active:
        for inst in classes[cid]['instructors']:idx[('i',inst)].append((cid,t))
        for rid in rr:
            if rooms.get(rid,{}).get('constraint',True):idx[('r',rid)].append((cid,t))
    for members in idx.values():
        for i in range(len(members)):
            a,ta=members[i]
            for b,tb in members[i+1:]:
                if overlap(ta,tb,classes[a]['dates'],classes[b]['dates']):hard+=1
    return hard,round(soft,4)


def conflict_report(schedule, classes, rooms):
    """List the conflicts counted by score(), with their section IDs."""
    issues = []
    idx = defaultdict(list)
    for cid, p in schedule.items():
        if p is None:
            if not classes[cid]['committed']:
                issues.append(('unassigned', cid, ''))
            continue
        t, rr = p
        c = classes[cid]
        if len(rr) != c['nr'] or len(set(rr)) != len(rr):
            issues.append(('room_count', cid, ''))
        for rid in rr:
            if rid not in rooms or rooms[rid]['capacity'] < c['limit'] * c['ratio']:
                issues.append(('capacity', cid, rid))
        for inst in c['instructors']:
            idx[('instructor', inst)].append((cid, t))
        for rid in rr:
            if rooms.get(rid, {}).get('constraint', True):
                idx[('room', rid)].append((cid, t))
    for (kind, resource), members in idx.items():
        for i, (a, ta) in enumerate(members):
            for b, tb in members[i + 1:]:
                if overlap(ta, tb, classes[a]['dates'], classes[b]['dates']):
                    issues.append((kind + '_overlap', a, b))
    return issues


def local_conflicts(cid,p,schedule,classes,rooms):
    if p is None:return 1
    t,rr=p; c=classes[cid]; n=0
    for other,q in schedule.items():
        if other==cid or q is None:continue
        ot,orr=q
        if not overlap(t,ot,c['dates'],classes[other]['dates']):continue
        n += len(c['instructors'] & classes[other]['instructors'])
        n += sum(1 for r in rr if r in orr and rooms.get(r, {}).get('constraint', True))
    return n


def repair_conflicts(schedule, classes, rooms, domains, rng, max_passes=3):
    """Try domain-valid single-section repairs, accepting only strict hard improvements."""
    moves = 0
    for _ in range(max_passes):
        issues = conflict_report(schedule, classes, rooms)
        focus = sorted({x for _, a, b in issues for x in (a, b)
                        if isinstance(x, int) and x in classes and not classes[x]['committed']})
        if not focus:
            break
        rng.shuffle(focus)
        changed = False
        for cid in focus:
            old = schedule[cid]
            old_hard = local_conflicts(cid, old, schedule, classes, rooms)
            if old is None and not domains[cid]:
                continue
            best_p = old
            best_key = (old_hard, placement_cost(cid, old, classes, rooms))
            # Inspect all times, but bound room combinations for predictable runtime.
            for t in classes[cid]['times']:
                for rr in domains[cid][:60]:
                    p = (t, rr)
                    key = (local_conflicts(cid, p, schedule, classes, rooms),
                           placement_cost(cid, p, classes, rooms))
                    if key < best_key:
                        best_p, best_key = p, key
                        if key[0] == 0:
                            break
                if best_key[0] == 0:
                    break
            if best_key[0] < old_hard:
                schedule[cid] = best_p
                moves += 1
                changed = True
        if not changed:
            break
    return moves


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data',default='data/pu-fal07-llr.xml');ap.add_argument('--iterations',type=int,default=100);ap.add_argument('--candidates',type=int,default=35);ap.add_argument('--tenure',type=int,default=7);ap.add_argument('--seed',type=int,default=42);ap.add_argument('--out',default='out');args=ap.parse_args()
    rng=random.Random(args.seed); started=time.perf_counter()
    rooms,classes=load(args.data); schedule={}; domains={cid:valid_room_sets(c,rooms) for cid,c in classes.items()}
    # Commit known solution placements, if provided. Do not move committed classes.
    for cid,c in classes.items():
        if c['committed']:
            ts=next((t for t in c['times'] if t['solution']),None)
            rr=tuple(r['id'] for r in c['rooms'] if r['solution'])
            schedule[cid]=(ts,rr) if ts and len(rr)==c['nr'] else None
    # Greedy construction: try a sample of placements for each class.
    ids=[cid for cid in classes if not classes[cid]['committed']]
    ids.sort(key=lambda cid:(len(classes[cid]['times'])*max(1,len(domains[cid])),cid))
    for cid in ids:
        c=classes[cid]; options=[]
        for t in c['times']:
            for rr in domains[cid][:25]:options.append((t,rr))
        if len(options)>150:rng.shuffle(options);options=options[:150]
        schedule[cid]=min(options,key=lambda p:(local_conflicts(cid,p,schedule,classes,rooms),placement_cost(cid,p,classes,rooms))) if options else None
    initial=score(schedule,classes,rooms); repairs=repair_conflicts(schedule,classes,rooms,domains,rng); repaired=score(schedule,classes,rooms); best=repaired; best_schedule=dict(schedule); tabu={}; curve=[]
    for it in range(args.iterations):
        selected=None; selected_key=None; selected_obj=None
        issues = conflict_report(schedule, classes, rooms)
        involved = {cid for _, a, b in issues for cid in (a, b) if isinstance(cid, int) and cid in ids}
        focus = sorted(involved)
        for _ in range(args.candidates):
            cid = rng.choice(focus if focus and rng.random() < 0.85 else ids)
            c=classes[cid]
            if not c['times'] or not domains[cid]:continue
            p=(rng.choice(c['times']),rng.choice(domains[cid]))
            old=schedule[cid]
            if old==p:continue
            # Incremental local approximation for ranking candidates.
            delta=local_conflicts(cid,p,schedule,classes,rooms)-local_conflicts(cid,old,schedule,classes,rooms)
            delta_soft=placement_cost(cid,p,classes,rooms)-placement_cost(cid,old,classes,rooms)
            key=(cid,p[0]['days'],p[0]['start'],p[0]['length'],p[1])
            approx=(delta,delta_soft)
            if tabu.get(key,-1)>it and not (delta<0):continue
            if selected_obj is None or approx<selected_obj:selected=(cid,p,old);selected_key=key;selected_obj=approx
        if selected is None:break
        cid,p,old=selected;schedule[cid]=p
        if old is not None:
            tabu[(cid,old[0]['days'],old[0]['start'],old[0]['length'],old[1])]=it+args.tenure
        current=score(schedule,classes,rooms)
        if current<best:best=current;best_schedule=dict(schedule)
        curve.append((it+1,current[0],current[1],best[0],best[1]))
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    with (out/'schedule.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['section_id','days','start_slot','length_slots','room_ids','committed'])
        for cid,p in sorted(best_schedule.items()):
            t,rr=p if p is not None else (None,())
            w.writerow([cid,t['days'] if t else '',t['start'] if t else '',t['length'] if t else '',';'.join(map(str,rr)),classes[cid]['committed']])
    with (out/'quality_curve.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['iteration','current_hard','current_soft','best_hard','best_soft']);w.writerows(curve)
    with (out/'conflicts.csv').open('w', newline='') as f:
        w=csv.writer(f)
        w.writerow(['type', 'section_a', 'section_b_or_room'])
        w.writerows(conflict_report(best_schedule, classes, rooms))
    metrics={'classes':len(classes),'rooms':len(rooms),'initial_hard':initial[0],'initial_soft':initial[1],'after_repair_hard':repaired[0],'repair_moves':repairs,'best_hard':best[0],'best_soft':best[1],'iterations_completed':len(curve),'runtime_seconds':round(time.perf_counter()-started,2),'seed':args.seed,'scope':'Partial UniTime evaluator; NOT full feasibility certification', 'conflict_report':'out/conflicts.csv'}
    (out/'metrics.json').write_text(json.dumps(metrics,indent=2));print(json.dumps(metrics,indent=2))
if __name__=='__main__':main()
