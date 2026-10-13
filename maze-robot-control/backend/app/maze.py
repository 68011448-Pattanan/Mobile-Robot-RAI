import base64, io, json, math, csv, random, xml.etree.ElementTree as ET
import cv2, numpy as np
from skimage.morphology import skeletonize
from scipy.spatial import cKDTree
from .core import ANGLES

def png(a):
    return 'data:image/png;base64,'+base64.b64encode(cv2.imencode('.png',a)[1]).decode()

def model(nodes, edges, name='Imported maze', width=800, height=600, source='drawing', start=None, finish=None):
    if not nodes: raise ValueError('No maze centerline detected. Adjust polarity/threshold or draw the maze.')
    if len({n['id'] for n in nodes})!=len(nodes): raise ValueError('Duplicate node identifiers')
    if any(not math.isfinite(float(n[k])) for n in nodes for k in ('x','y')): raise ValueError('Invalid node coordinates')
    degree={n['id']:0 for n in nodes}
    ids=set(degree)
    for e in edges:
        if e['a'] not in ids or e['b'] not in ids: raise ValueError('Edge references unknown node')
        degree[e['a']]+=1; degree[e['b']]+=1
        e['length']=sum(math.dist((p['x'],p['y']),(q['x'],q['y'])) for p,q in zip(e['points'],e['points'][1:]))
    for n in nodes: n['degree']=degree[n['id']]; n['kind']='dead end' if n['degree']==1 else 'cross' if n['degree']>=4 else 'T junction' if n['degree']==3 else 'bend'
    if start is not None and start not in ids: raise ValueError('Unknown start node')
    if finish is not None and finish not in ids: raise ValueError('Unknown finish node')
    ends=[n['id'] for n in nodes if n['degree']==1]
    m=dict(id=f'maze-{random.randrange(10**9)}',name=name,width=width,height=height,lineWidth=12,scale=1,heading=0,start=start or (ends[0] if ends else nodes[0]['id']),finish=finish or (ends[-1] if ends else nodes[-1]['id']),sourceType=source,graph={'nodes':nodes,'edges':edges},segments=edges,intersections=nodes,centerline=[p for e in edges for p in e['points']],warnings=[],confidence=None,verified=False)
    a=analysis(m)
    if a['components']>1: m['warnings'].append('Disconnected lines: inspect endpoints and connect only confirmed gaps.')
    if a['cycles']: m['warnings'].append('Contains loops: LSRB may cycle and its reduced route is not guaranteed shortest.')
    if len(ends)<2: m['warnings'].append('Select start and finish manually.')
    return m

def analysis(m):
    ns=m['graph']['nodes']; es=m['graph']['edges']; adj={n['id']:[] for n in ns}
    for e in es:
        if e['a'] not in adj or e['b'] not in adj: raise ValueError('Unknown edge node')
        adj[e['a']].append(e['b']); adj[e['b']].append(e['a'])
    seen=set(); components=0
    for n in adj:
        if n in seen: continue
        components+=1; todo=[n]
        while todo:
            u=todo.pop()
            if u in seen: continue
            seen.add(u); todo.extend(adj[u])
    # Dijkstra, with geometric lengths
    import heapq
    start=m['start']; finish=m['finish']; dist={start:0}; prev={}; heap=[(0,start)]
    while heap:
        d,u=heapq.heappop(heap)
        if d!=dist[u]: continue
        for e in es:
            v=e['b'] if e['a']==u else e['a'] if e['b']==u else None
            if v is None: continue
            w=e.get('length') or sum(math.dist((p['x'],p['y']),(q['x'],q['y'])) for p,q in zip(e['points'],e['points'][1:]))
            if d+w<dist.get(v,float('inf')): dist[v]=d+w; prev[v]=(u,e['id']); heapq.heappush(heap,(d+w,v))
    route=[]; u=finish
    while u in prev: u,eid=prev[u]; route.insert(0,eid)
    shortest_nodes=[start]; u=start
    for eid in route:
        e=next(e for e in es if e['id']==eid); u=e['b'] if e['a']==u else e['a']; shortest_nodes.append(u)
    # Geometry measures
    scale=max(.0001,float(m.get('scale',1))); minimum=min([e.get('length',0)*scale for e in es] or [0])
    radius=float('inf')
    for e in es:
        points=e['points']
        for p,q,r in zip(points,points[1:],points[2:]):
            a=np.array([p['x'],p['y']],float); b=np.array([q['x'],q['y']],float); c=np.array([r['x'],r['y']],float)
            ab=np.linalg.norm(a-b); bc=np.linalg.norm(b-c); ac=np.linalg.norm(a-c); cross=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
            if cross>1e-6: radius=min(radius,float(ab*bc*ac/(2*cross))*scale)
    return dict(components=components,cycles=max(0,len(es)-len(ns)+components),deadEnds=sum(len(x)==1 for x in adj.values()),intersections=sum(len(x)>=3 for x in adj.values()),distance=dist.get(finish),shortestEdges=route,shortestNodes=shortest_nodes,minimumSegment=minimum,minimumRadius=radius if math.isfinite(radius) else None,turns=max(0,len(route)-1))

def skeleton_graph(binary, min_size=8):
    # Remove tiny components, preserving topology (never automatically bridge gaps).
    count,labels,stats,_=cv2.connectedComponentsWithStats(binary.astype(np.uint8),8)
    mask=np.zeros_like(binary,dtype=bool)
    for i in range(1,count):
        if stats[i,cv2.CC_STAT_AREA]>=min_size: mask|=labels==i
    sk=skeletonize(mask); pixels=set(map(tuple,np.argwhere(sk)))
    def neighbors(p):
        y,x=p; result=[]
        for dy,dx in ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)):
            q=(y+dy,x+dx)
            if q not in pixels: continue
            # Suppress diagonal shortcuts if an orthogonal neighbor bridges them.
            if dy and dx and ((y+dy,x) in pixels or (y,x+dx) in pixels): continue
            result.append(q)
        return result
    critical={p for p in pixels if len(neighbors(p))!=2}
    # Closed loops need an anchor so they remain represented.
    unseen=set(pixels)
    while unseen:
        seed=next(iter(unseen)); stack=[seed]; component=set()
        while stack:
            p=stack.pop()
            if p in component: continue
            component.add(p); unseen.discard(p); stack.extend(q for q in neighbors(p) if q not in component)
        if not component & critical: critical.add(seed)
    clusters=[]; unseen=set(critical)
    while unseen:
        seed=unseen.pop(); group={seed}; todo=[seed]
        while todo:
            p=todo.pop()
            for q in neighbors(p):
                if q in unseen: unseen.remove(q); group.add(q); todo.append(q)
        clusters.append(group)
    nodes=[]; lookup={}
    for i,g in enumerate(clusters):
        y,x=np.mean(list(g),axis=0); nid=str(i); nodes.append({'id':nid,'x':float(x),'y':float(y)})
        for p in g: lookup[p]=nid
    byid={n['id']:n for n in nodes}; edges=[]; visited=set()
    for g in clusters:
        for p in g:
            for q in neighbors(p):
                if q in g or frozenset((p,q)) in visited: continue
                track=[p,q]; visited.add(frozenset((p,q))); previous=p; current=q
                while current not in lookup:
                    options=[n for n in neighbors(current) if n!=previous]
                    if not options: break
                    nxt=options[0]; visited.add(frozenset((current,nxt))); track.append(nxt); previous,current=current,nxt
                if current not in lookup: continue
                a=lookup[p]; b=lookup[current]
                coords=np.array([[x,y] for y,x in track],np.float32).reshape(-1,1,2)
                simp=cv2.approxPolyDP(coords,1.2,False).reshape(-1,2)
                points=[{'x':float(x),'y':float(y)} for x,y in simp]
                points[0]={'x':byid[a]['x'],'y':byid[a]['y']}; points[-1]={'x':byid[b]['x'],'y':byid[b]['y']}
                edges.append({'id':str(len(edges)),'a':a,'b':b,'points':points})
    return nodes,edges,sk

def grid_model(rows,name):
    if any(str(v).strip() not in ('0','1','S','F') for row in rows for v in row): raise ValueError('Grid cells must use 0,1,S,F or configured open/wall values')
    if not rows or any(len(r)!=len(rows[0]) for r in rows): raise ValueError('Grid must be rectangular')
    nodes=[]; edges=[]; mapping={}; start=finish=None
    for y,row in enumerate(rows):
        for x,v in enumerate(row):
            if str(v).strip() in ('0','S','F'):
                nid=f'{x}:{y}'; mapping[x,y]=nid; nodes.append(dict(id=nid,x=40+x*40,y=40+y*40))
                if str(v)=='S': start=nid
                if str(v)=='F': finish=nid
    byid={n['id']:n for n in nodes}
    for (x,y),a in mapping.items():
        for q in ((x+1,y),(x,y+1)):
            if q in mapping:
                b=mapping[q]; edges.append(dict(id=str(len(edges)),a=a,b=b,points=[{k:byid[a][k] for k in ('x','y')},{k:byid[b][k] for k in ('x','y')}]))
    return model(nodes,edges,name,(len(rows[0])+1)*40,(len(rows)+1)*40,'grid',start,finish)

def import_maze(data,filename,o):
    ext=filename.rsplit('.',1)[-1].lower()
    if ext=='json':
        d=json.loads(data)
        if 'grid' in d: return grid_model(d['grid'],filename)
        g=d.get('graph',d); ns=g.get('nodes',d.get('intersections',[])); es=g.get('edges',d.get('segments',[]))
        m=model(ns,es,d.get('name',filename),d.get('width',800),d.get('height',600),'json',d.get('start'),d.get('finish'))
        for key in ('scale','heading','lineWidth','verified'): m[key]=d.get(key,m[key])
        return m
    if ext in ('csv','txt'):
        rows=list(csv.reader(io.StringIO(data.decode('utf-8-sig'))))
        if len(rows[0])==1: rows=[list(r[0].replace(' ','')) for r in rows if r]
        rows=[[('0' if str(v).strip()==str(o.get('gridOpen','0')) else '1' if str(v).strip()==str(o.get('gridWall','1')) else str(v).strip()) for v in row] for row in rows]
        return grid_model(rows,filename)
    if ext=='svg' and o.get('vector',True):
        from svgpathtools import parse_path
        root=ET.fromstring(data)
        # Transforms are safely rasterized rather than silently ignored.
        if not any('transform' in el.attrib for el in root.iter()):
            segments=[]; selected=o.get('svgIds',[])
            for idx,el in enumerate(root.iter()):
                tag=el.tag.split('}')[-1]; ident=el.get('id',str(idx))
                if selected and ident not in selected: continue
                pts=[]
                if tag=='path':
                    path=parse_path(el.get('d',''))
                    for subpath in path.continuous_subpaths():
                        sampled=[]
                        for seg in subpath:
                            n=max(2,min(200,int(seg.length()/4)+1)); sampled.extend([dict(x=float(seg.point(t).real),y=float(seg.point(t).imag)) for t in np.linspace(0,1,n)])
                        if len(sampled)>1: segments.append(sampled)
                elif tag in ('polyline','polygon'):
                    nums=[float(v) for v in el.get('points','').replace(',',' ').split()]; pts=[dict(x=x,y=y) for x,y in zip(nums[::2],nums[1::2])]
                    if tag=='polygon' and pts: pts.append(pts[0])
                elif tag=='line': pts=[dict(x=float(el.get('x1',0)),y=float(el.get('y1',0))),dict(x=float(el.get('x2',0)),y=float(el.get('y2',0)))]
                if len(pts)>1: segments.append(pts)
            if segments:
                # Split at intersections while retaining sampled curve geometry.
                from shapely.geometry import LineString
                from shapely.ops import unary_union
                joined=unary_union([LineString([(p['x'],p['y']) for p in ps]) for ps in segments])
                lines=list(joined.geoms) if hasattr(joined,'geoms') else [joined]
                nodes=[]; edges=[]; coords={}
                def node(p):
                    key=(round(p[0],3),round(p[1],3))
                    if key not in coords: coords[key]=str(len(nodes)); nodes.append(dict(id=coords[key],x=p[0],y=p[1]))
                    return coords[key]
                for line in lines:
                    ps=list(line.coords); edges.append(dict(id=str(len(edges)),a=node(ps[0]),b=node(ps[-1]),points=[dict(x=x,y=y) for x,y in ps]))
                view=root.get('viewBox','0 0 800 600').replace(',',' ').split(); m=model(nodes,edges,filename,float(view[2]),float(view[3]),'svg'); m['svgElements']=[el.get('id',str(i)) for i,el in enumerate(root.iter()) if el.tag.split('}')[-1] in ('path','polyline','polygon','line')]; return m
    if ext=='svg':
        import cairosvg
        data=cairosvg.svg2png(bytestring=data,output_width=1000)
    elif ext=='pdf':
        import fitz
        doc=fitz.open(stream=data,filetype='pdf'); page=int(o.get('page',1))-1
        if not 0<=page<len(doc): raise ValueError('PDF page out of range')
        pix=doc[page].get_pixmap(matrix=fitz.Matrix(2,2)); data=pix.tobytes('png')
    image=cv2.imdecode(np.frombuffer(data,np.uint8),cv2.IMREAD_COLOR)
    if image is None: raise ValueError('Unsupported or unreadable image')
    if max(image.shape[:2])>1400: image=cv2.resize(image,None,fx=1400/max(image.shape[:2]),fy=1400/max(image.shape[:2]))
    original=image.copy()
    corners=o.get('corners')
    if corners and len(corners)==4:
        src=np.float32(corners); w=int(max(np.linalg.norm(src[0]-src[1]),np.linalg.norm(src[2]-src[3]))); h=int(max(np.linalg.norm(src[0]-src[3]),np.linalg.norm(src[1]-src[2])))
        if min(w,h)<10: raise ValueError('Perspective corners are too close')
        image=cv2.warpPerspective(image,cv2.getPerspectiveTransform(src,np.float32([[0,0],[w-1,0],[w-1,h-1],[0,h-1]])),(w,h))
    crop=o.get('crop')
    if crop:
        x,y,w,h=map(int,crop); image=image[max(0,y):max(0,y)+h,max(0,x):max(0,x)+w]
        if not image.size: raise ValueError('Crop is empty')
    rotation=float(o.get('rotation',0))
    if rotation:
        h,w=image.shape[:2]; mat=cv2.getRotationMatrix2D((w/2,h/2),rotation,1); image=cv2.warpAffine(image,mat,(w,h),borderValue=(255,255,255))
    if o.get('flip'): image=cv2.flip(image,1)
    gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY); gray=cv2.convertScaleAbs(gray,alpha=float(o.get('contrast',1)))
    blur=int(o.get('blur',1)); blur=max(1,min(31,blur|1)); gray=cv2.GaussianBlur(gray,(blur,blur),0)
    polarity=o.get('polarity','auto'); inv=polarity=='black' or (polarity=='auto' and np.median(gray)>127)
    if o.get('interpretation')=='wall': inv=not inv
    typ=cv2.THRESH_BINARY_INV if inv else cv2.THRESH_BINARY
    if o.get('adaptive'): binary=cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,typ,31,5)
    else: _,binary=cv2.threshold(gray,int(o.get('threshold',127)),255,typ)
    strength=int(o.get('morphology',0))
    if strength: binary=cv2.morphologyEx(binary,cv2.MORPH_OPEN,np.ones((strength,strength),np.uint8))
    ns,es,sk=skeleton_graph(binary>0,int(o.get('minimumSize',8)))
    if len(ns)>1500 or len(es)>2500: raise ValueError('Extraction is too complex. Crop the maze, remove noise, or adjust threshold before retrying.')
    m=model(ns,es,filename,binary.shape[1],binary.shape[0],ext)
    m['previewWidth']=original.shape[1]; m['previewHeight']=original.shape[0]
    m['previews']={'original':png(original),'corrected':png(image),'binary':png(binary),'centerline':png(sk.astype(np.uint8)*255)}
    foreground=float(np.mean(binary>0)); a=analysis(m)
    m['confidence']=round(max(0,min(95,95-15*(a['components']-1)-20*(foreground>.6)-10*(len(ns)>100))))
    m['warnings'].insert(0,'Maze extraction requires correction. Confirm topology, start and finish before running.')
    if o.get('interpretation')=='wall': m['warnings'].append('Converted Path: corridor centerline; this is not an original physical line.')
    # Estimate stroke width from distance transform at skeleton pixels.
    vals=cv2.distanceTransform(binary,cv2.DIST_L2,3)[sk]
    if len(vals): m['lineWidth']=float(np.median(vals)*2)
    ends=[n for n in ns if n['degree']==1]; gaps=[]
    for i,p in enumerate(ends):
        for q in ends[i+1:]:
            d=math.dist((p['x'],p['y']),(q['x'],q['y']))
            if d<max(25,m['lineWidth']*3): gaps.append([p['id'],q['id'],round(d,1)])
    m['possibleGaps']=gaps
    return m
