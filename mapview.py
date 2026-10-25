"""Qt map: local track rendering; optional, explicitly enabled online OSM tiles."""
import math
import time
from collections import Counter
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QUrl, QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QPainterPath, QImage, QPalette
from PySide6.QtWidgets import QWidget
from PySide6.QtNetwork import QNetworkAccessManager,QNetworkRequest
from datahub import trim_track

COLORS=['#087eaa','#e16b25','#8c4db0','#18845c','#c33b60','#a87906','#4070cd','#564c40']

DARK_COLORS=['#7dd3fc','#ffb477','#d8b4fe','#79deb0','#ff9cbc','#f7d47a','#9bbcff','#d5c4b4']

def route_color(index,palette):
    values=DARK_COLORS if palette.color(QPalette.ColorRole.Window).lightness()<128 else COLORS
    return QColor(values[index%len(values)])

def project(lat,lon):
    lat=max(-85.05112878,min(85.05112878,lat))
    return ((lon+180)/360,(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2)

def unproject(x,y):
    return math.degrees(math.atan(math.sinh(math.pi*(1-2*y)))),(x%1)*360-180

def route_cells(points,grid):
    """Traverse crossed grid cells independently of sampling density."""
    visited=set();last=None
    for point in points:
        if point is None:last=None;continue
        x,y=project(*point)
        if last:
            x+=round(last[0]-x)
            ax,ay=last[0]*grid,last[1]*grid;bx,by=x*grid,y*grid
            ix,iy=math.floor(ax),math.floor(ay);ex,ey=math.floor(bx),math.floor(by)
            dx,dy=bx-ax,by-ay;sx=1 if dx>0 else -1;sy=1 if dy>0 else -1
            tx=((ix+1-ax) if dx>0 else (ax-ix))/abs(dx) if dx else math.inf
            ty=((iy+1-ay) if dy>0 else (ay-iy))/abs(dy) if dy else math.inf
            stepx=1/abs(dx) if dx else math.inf;stepy=1/abs(dy) if dy else math.inf
            if abs(ex-ix)+abs(ey-iy)<10000:
                for _ in range(10002):
                    visited.add((ix%grid,iy))
                    if ix==ex and iy==ey:break
                    if tx<ty:ix+=sx;tx+=stepx
                    else:iy+=sy;ty+=stepy
        visited.add((math.floor(x*grid)%grid,math.floor(y*grid)));last=(x,y)
    return visited

def density_segments(tracks):
    """~150m equatorial grid; each activity votes once per visited cell."""
    counts=Counter();grid=262144
    for points in tracks:counts.update(route_cells(points,grid))
    return counts,grid

class TrackMap(QWidget):
    def __init__(self,cache_dir,parent=None):
        super().__init__(parent)
        self.setMinimumSize(280,240);self.setMouseTracking(True)
        self.cache=Path(cache_dir);self.cache.mkdir(parents=True,exist_ok=True)
        self.network=QNetworkAccessManager(self);self.online=False
        self.tile_url='https://tile.openstreetmap.org/{z}/{x}/{y}.png'
        self.pixmaps={};self.pending={};self.failed=set();self.visible_keys=set()
        self.center=(.51,.33);self.zoom=5;self.routes=[];self.heat=False;self.density=({},1);self.drag=None
        self.lang='de';self.tile_errors=0
        self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.timeout.connect(self.fetch_visible)

    def set_online(self,value):
        self.online=bool(value)
        if value:self.failed.clear();self.tile_errors=0
        if not value:
            for reply in list(self.pending.values()):reply.abort()
        self.timer.start(120);self.update()

    def set_routes(self,routes,heat=False):
        self.routes=routes;self.heat=heat
        self.density=density_segments([r[1] for r in routes]) if heat else ({},1)
        points=[project(*p) for _,pts in routes for p in pts if p is not None]
        if points:
            ref=points[0][0];points=[(x+round(ref-x),y) for x,y in points]
            lo_x,hi_x=min(p[0] for p in points),max(p[0] for p in points)
            lo_y,hi_y=min(p[1] for p in points),max(p[1] for p in points)
            self.center=((lo_x+hi_x)/2,(lo_y+hi_y)/2)
            size=max((hi_x-lo_x)*256/max(100,self.width()-60),(hi_y-lo_y)*256/max(100,self.height()-100),1/2**17)
            self.zoom=max(1,min(17,int(math.floor(math.log2(1/size)))))
        self.update();self.timer.start(150)

    def screen(self,x,y):
        scale=256*2**self.zoom
        x+=round(self.center[0]-x)
        return QPointF(self.width()/2+(x-self.center[0])*scale,self.height()/2+(y-self.center[1])*scale)

    def tiles(self):
        n=2**self.zoom;scale=256*n;cx,cy=self.center
        xmin=math.floor((cx*scale-self.width()/2)/256);xmax=math.floor((cx*scale+self.width()/2)/256)
        ymin=max(0,math.floor((cy*scale-self.height()/2)/256));ymax=min(n-1,math.floor((cy*scale+self.height()/2)/256))
        for x in range(xmin,xmax+1):
            for y in range(ymin,ymax+1):
                yield (self.zoom,x%n,y),QRectF(x*256-cx*scale+self.width()/2,y*256-cy*scale+self.height()/2,256,256)

    def tile_path(self,key):
        import hashlib
        source=hashlib.sha256(self.tile_url.encode()).hexdigest()[:10]
        return self.cache/(source+'-'+'-'.join(map(str,key))+'.png')

    def fetch_visible(self):
        if not self.online or not self.isVisible():return
        self.visible_keys={key for key,_ in self.tiles()}
        for key in list(self.visible_keys):
            if key in self.pixmaps or key in self.pending or key in self.failed:continue
            path=self.tile_path(key)
            if path.exists() and time.time()-path.stat().st_mtime<7*86400:
                pix=QPixmap(str(path))
                if not pix.isNull():self.pixmaps[key]=pix;continue
            if len(self.pending)>=2:break
            z,x,y=key;request=QNetworkRequest(QUrl(self.tile_url.format(z=z,x=x,y=y)))
            request.setRawHeader(b'User-Agent',b'GarminExportStudio/0.2.0 (local desktop map)')
            request.setTransferTimeout(15000)
            reply=self.network.get(request);self.pending[key]=reply
            reply.finished.connect(lambda key=key,reply=reply:self.tile_done(key,reply))
        self.update()

    def tile_done(self,key,reply):
        self.pending.pop(key,None)
        if self.online and reply.error()==reply.NetworkError.NoError:
            data=bytes(reply.readAll());pix=QPixmap()
            if len(data)<2*1024*1024 and pix.loadFromData(data):
                self.pixmaps[key]=pix
                try:self.tile_path(key).write_bytes(data)
                except OSError:pass
            else:self.failed.add(key)
        elif self.online:self.failed.add(key);self.tile_errors+=1
        reply.deleteLater()
        if len(self.pixmaps)>300:
            self.pixmaps={k:v for k,v in self.pixmaps.items() if k in self.visible_keys}
        self.update();self.timer.start(100)

    def paintEvent(self,event):
        p=QPainter(self);p.setClipRect(self.rect());p.setRenderHint(QPainter.RenderHint.Antialiasing);p.fillRect(self.rect(),self.palette().color(QPalette.ColorRole.Base))
        p.setPen(QPen(self.palette().color(QPalette.ColorRole.Mid),1))
        for x in range(0,self.width(),50):p.drawLine(x,0,x,self.height())
        for y in range(0,self.height(),50):p.drawLine(0,y,self.width(),y)
        if self.online:
            for key,rect in self.tiles():
                if key in self.pixmaps:p.drawPixmap(rect,self.pixmaps[key],QRectF(0,0,256,256))
        if self.heat:
            counts,grid=self.density;maximum=max(counts.values(),default=1)
            for (x,y),count in counts.items():
                at=self.screen(x/grid,y/grid)
                if not self.rect().adjusted(-20,-20,20,20).contains(at.toPoint()):continue
                color=QColor.fromHsvF(.64*(1-count/maximum),.9,.95,.32 if count<2 else .6)
                p.setPen(Qt.PenStyle.NoPen);p.setBrush(color);radius=max(3,min(12,256*2**self.zoom/grid))
                p.drawEllipse(at,radius,radius)
        else:
            for i,(name,points) in enumerate(self.routes):
                path=QPainterPath();active=False;last=None
                # Rendering is bounded; source files remain untouched.
                step=max(1,len(points)//6000)
                for n,point in enumerate(points):
                    if point is None:active=False;last=None;continue
                    if n%step and n!=len(points)-1:continue
                    xy=project(*point);screen=self.screen(*xy)
                    if last and abs(screen.x()-last.x())>self.width()*2:active=False
                    if active:path.lineTo(screen)
                    else:path.moveTo(screen);active=True
                    last=screen
                pen=QPen(route_color(i,self.palette()),3);pen.setCapStyle(Qt.PenCapStyle.RoundCap);p.setPen(pen);p.setBrush(Qt.BrushStyle.NoBrush);p.drawPath(path)
        p.fillRect(0,0,self.width(),28,self.palette().color(QPalette.ColorRole.Base));p.setPen(self.palette().color(QPalette.ColorRole.Text))
        title=('Heatmap · Fahrthäufigkeit' if self.lang=='de' else 'Heatmap · trip frequency') if self.heat else ('GPS-Strecken' if self.lang=='de' else 'GPS tracks')
        p.drawText(9,19,title+f' · {len(self.routes)}')
        if not self.heat and self.routes:
            for i,(name,_) in enumerate(self.routes[:5]):
                p.fillRect(5,32+i*19,min(290,self.width()-10),19,self.palette().color(QPalette.ColorRole.Base));p.setPen(route_color(i,self.palette()))
                p.drawText(10,46+i*19,p.fontMetrics().elidedText(name,Qt.TextElideMode.ElideRight,min(275,self.width()-20)))
        if not self.routes:p.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,'Aktivität mit GPS auswählen' if self.lang=='de' else 'Select an activity with GPS')
        bottom='© OpenStreetMap contributors · openstreetmap.org/copyright' if self.online else ('Offline · GPS ohne Kartenhintergrund' if self.lang=='de' else 'Offline · GPS without basemap')
        if self.online and self.tile_errors:bottom+=' · '+('Kartenabruf teilweise fehlgeschlagen' if self.lang=='de' else 'Some tiles unavailable')
        p.fillRect(0,self.height()-26,self.width(),26,self.palette().color(QPalette.ColorRole.Base));p.setPen(self.palette().color(QPalette.ColorRole.Text));p.drawText(7,self.height()-9,bottom)
        p.end()

    def wheelEvent(self,event):
        self.zoom=max(1,min(18,self.zoom+(1 if event.angleDelta().y()>0 else -1)))
        self.update();self.timer.start(180);event.accept()
    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:self.drag=event.position();self.setCursor(Qt.CursorShape.ClosedHandCursor)
    def mouseMoveEvent(self,event):
        if self.drag is not None:
            delta=event.position()-self.drag;scale=256*2**self.zoom
            self.center=(self.center[0]-delta.x()/scale,max(0,min(1,self.center[1]-delta.y()/scale)))
            self.drag=event.position();self.update();self.timer.start(180)
    def mouseReleaseEvent(self,event):self.drag=None;self.unsetCursor()
    def resizeEvent(self,event):self.timer.start(200);super().resizeEvent(event)

    def poster(self,path,title,stats):
        image=QImage(max(1200,self.width()),900,QImage.Format.Format_ARGB32);image.fill(QColor('white'))
        painter=QPainter(image);painter.setPen(QColor('#192b43'));font=painter.font();font.setPixelSize(28);font.setBold(True);painter.setFont(font)
        painter.drawText(35,50,title);font.setPixelSize(19);font.setBold(False);painter.setFont(font);painter.drawText(35,86,stats)
        pix=self.grab();painter.drawPixmap(QRectF(30,115,image.width()-60,730),pix,QRectF(pix.rect()))
        font.setPixelSize(14);painter.setFont(font);painter.drawText(35,880,'TTN Garmin Export · '+('Heatmap' if self.heat else 'GPS'))
        painter.end()
        if not image.save(path,'PNG'):raise OSError('Image could not be saved')
