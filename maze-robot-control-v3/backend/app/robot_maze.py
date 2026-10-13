"""Version 1 compact Uno maze format; no image pixels or Python objects on board."""
import math, struct
MAX_NODES=64
MAX_EDGES=128
MAX_BYTES=888

def encode_maze(m):
    try:
        if m.get('verified') is not True: raise ValueError('Review topology and check Topology reviewed before uploading.')
        scale=float(m['scale']); width=float(m['lineWidth'])*scale; heading=float(m['heading'])
        if not all(math.isfinite(v) for v in (scale,width,heading)) or scale<=0 or not 1<=round(width)<=65535:
            raise ValueError('Scale must be positive; physical line width must be 1–65535 mm.')
        original=m['graph']['nodes']; edges=m['graph']['edges']; ids={n['id']:i for i,n in enumerate(original)}
        if len(ids)!=len(original) or not 2<=len(ids)<=MAX_NODES: raise ValueError('Robot maze requires 2–64 unique nodes including geometry points.')
        start=ids[m['start']]; finish=ids[m['finish']]
        if start==finish: raise ValueError('Start and finish must differ.')
        def point(p):
            values=[float(p[k])*scale for k in ('x','y')]
            if not all(math.isfinite(v) and -32768<=v<=32767 for v in values): raise ValueError('Maze coordinates must fit signed 16-bit millimeters.')
            return tuple(round(v) for v in values)
        nodes=[point(n) for n in original]; links=[]
        for e in edges:
            a=ids[e['a']]; b=ids[e['b']]; pts=[point(p) for p in e['points']]
            if len(pts)<2 or pts[0]!=nodes[a] or pts[-1]!=nodes[b]: raise ValueError('Edge geometry must run from its a node to its b node.')
            chain=[a]
            for p in pts[1:-1]:
                nodes.append(p); chain.append(len(nodes)-1)
            chain.append(b); links.extend(zip(chain,chain[1:]))
        if len(nodes)>MAX_NODES or len(links)>MAX_EDGES: raise ValueError('Robot capacity: 64 nodes (including curve samples), 128 segments. Simplify geometry explicitly before upload.')
        adj={i:[] for i in range(len(nodes))}
        for a,b in links:
            if a==b or nodes[a]==nodes[b]: raise ValueError('Maze contains a zero-length segment after millimeter rounding.')
            adj[a].append(b); adj[b].append(a)
        seen=set(); todo=[start]
        while todo:
            u=todo.pop()
            if u not in seen: seen.add(u); todo.extend(adj[u])
        if len(seen)!=len(nodes): raise ValueError('All maze nodes must be connected to the start.')
        payload=struct.pack('<BBBBBhH',1,len(nodes),len(links),start,finish,round((heading%360)*10)%3600,round(width))
        payload+=b''.join(struct.pack('<hh',*p) for p in nodes)+bytes(v for pair in links for v in pair)
        if len(payload)>MAX_BYTES: raise ValueError('Maze exceeds EEPROM capacity.')
        return payload,dict(bytes=len(payload),capacity=MAX_BYTES,nodes=len(nodes),segments=len(links),checksum=sum(payload)%65536)
    except (KeyError,TypeError,OverflowError) as e: raise ValueError('Invalid MazeModel: missing or malformed graph/geometry.') from e


def decode_maze(payload):
    """Read the compact EEPROM representation into an editable MazeModel."""
    if len(payload)<19 or len(payload)>MAX_BYTES: raise ValueError('Invalid stored maze length')
    version,n,e,start,finish,heading,width=struct.unpack('<BBBBBhH',payload[:9])
    if version!=1 or not 2<=n<=MAX_NODES or not 1<=e<=MAX_EDGES or len(payload)!=9+4*n+2*e or start>=n or finish>=n or start==finish or not 0<=heading<3600 or width<1:
        raise ValueError('Invalid stored maze header')
    nodes=[dict(id=str(i),x=x,y=y) for i,(x,y) in enumerate(struct.iter_unpack('<hh',payload[9:9+4*n]))]
    links=list(struct.iter_unpack('<BB',payload[9+4*n:]))
    if any(a>=n or b>=n or a==b for a,b in links): raise ValueError('Invalid stored maze segment')
    # Preserve absolute EEPROM millimeters, including negative coordinates.
    from .maze import model
    edges=[dict(id=str(i),a=str(a),b=str(b),points=[{k:nodes[j][k] for k in ('x','y')} for j in (a,b)]) for i,(a,b) in enumerate(links)]
    m=model(nodes,edges,name='Maze read from robot EEPROM',width=max(p['x'] for p in nodes)+50,height=max(p['y'] for p in nodes)+50,source='robot',start=str(start),finish=str(finish))
    m.update(scale=1,lineWidth=width,heading=heading/10,verified=True)
    # Round-trip structural validation also checks connectivity and zero-length segments.
    encode_maze(m)
    return m
