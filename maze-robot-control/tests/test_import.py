import sys,pathlib,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'backend'))
import cv2,numpy as np,pytest
from app.maze import import_maze,analysis

def image(white=False,contrast=False,gap=False):
    im=np.full((240,300,3),190 if contrast else 255,np.uint8);color=(70,70,70) if contrast else (0,0,0)
    cv2.line(im,(30,160),(260,160),color,12);cv2.line(im,(140,160),(140,40),color,12)
    if gap: cv2.rectangle(im,(180,150),(190,170),(255,255,255),-1)
    return 255-im if white else im
@pytest.mark.parametrize('ext',['png','jpg','webp','bmp'])
def test_formats(ext):
    im=image(); m=import_maze(cv2.imencode('.'+ext,im)[1].tobytes(),'new.'+ext,{'polarity':'black'});assert len(m['graph']['edges'])>=3;assert analysis(m)['components']==1
@pytest.mark.parametrize('kind',['white','contrast','rotated','perspective','broken'])
def test_variants(kind):
    im=image(white=kind=='white',contrast=kind=='contrast',gap=kind=='broken');opts={'polarity':'white' if kind=='white' else 'black'}
    if kind=='rotated':im=cv2.rotate(im,cv2.ROTATE_90_CLOCKWISE)
    if kind=='perspective':
        src=np.float32([[0,0],[299,0],[299,239],[0,239]]);dest=np.float32([[20,10],[280,30],[299,239],[0,220]]);im=cv2.warpPerspective(im,cv2.getPerspectiveTransform(src,dest),(300,240),borderValue=(255,255,255));opts['corners']=dest.tolist()
    m=import_maze(cv2.imencode('.png',im)[1].tobytes(),'test.png',opts);assert len(m['graph']['nodes'])>=4
    if kind=='broken':assert analysis(m)['components']==2;assert m['possibleGaps']
    else:assert analysis(m)['components']==1

def test_grid():
    m=import_maze(b'1,1,1,1,1\n1,S,0,F,1\n1,1,1,1,1','grid.csv',{});assert analysis(m)['distance']==80
    again=import_maze(json.dumps(m).encode(),'graph.json',{});assert analysis(again)['distance']==80

def test_svg():
    svg=b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 200"><path id="track" d="M 20 100 L 280 100" fill="none" stroke="black"/><path id="branch" d="M150 20 L150 100" fill="none" stroke="black"/></svg>'
    m=import_maze(svg,'vector.svg',{});assert analysis(m)['intersections']==1;assert len(m['graph']['edges'])==3

def test_pdf():
    import fitz
    doc=fitz.open();p=doc.new_page(width=300,height=240);p.draw_line((30,160),(260,160),color=(0,0,0),width=12);p.draw_line((140,160),(140,40),color=(0,0,0),width=12)
    m=import_maze(doc.tobytes(),'maze.pdf',{'page':1,'polarity':'black'});assert analysis(m)['intersections']>=1

@pytest.mark.parametrize('kind',['left','right','T','cross','dead'])
def test_junctions(kind):
    im=np.full((180,180),255,np.uint8);cv2.line(im,(20,90),(90,90),0,10)
    if kind!='dead':cv2.line(im,(90,90),(90,20 if kind in ('left','T','cross') else 160),0,10)
    if kind in ('T','cross'):cv2.line(im,(90,90),(160,90),0,10)
    if kind=='cross':cv2.line(im,(90,90),(90,160),0,10)
    m=import_maze(cv2.imencode('.png',im)[1].tobytes(),kind+'.png',{'polarity':'black'});a=analysis(m);assert a['components']==1
    if kind in ('T','cross'):assert a['intersections']==1
    else:assert a['deadEnds']==2
