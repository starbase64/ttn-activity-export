"""Optional Google Maps view; API key remains in a temporary off-record web page."""
import json
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QDialog,QVBoxLayout,QLabel,QInputDialog,QLineEdit

def show_google_map(parent,routes,lang,heat=False):
    t=lambda de,en:de if lang=='de' else en
    if not routes:parent.host.message('Zuerst GPS-Strecken auswählen.','Select GPS tracks first.');return
    key,ok=QInputDialog.getText(parent,'Google Maps',t('Google-Maps-JavaScript-API-Schlüssel eingeben. Google lädt Onlineinhalte; Kosten und Schlüsselbeschränkungen gelten. Der Schlüssel wird nicht gespeichert.','Enter a Google Maps JavaScript API key. Google loads online content; billing and key restrictions apply. The key is not saved.'),QLineEdit.EchoMode.Password)
    if not ok or not key.strip():return
    try:
        from PySide6.QtWebEngineWidgets import QWebEngineView
        from PySide6.QtWebEngineCore import QWebEnginePage,QWebEngineProfile
        # Bound the local page size; do not join track segments across GPS gaps.
        budget=max(20,50000//max(1,len(routes)));lines=[]
        for i,(name,points) in enumerate(routes):
            step=max(1,len(points)//budget);segments=[];segment=[]
            for n,p in enumerate(points):
                if p is None:
                    if segment:segments.append(segment)
                    segment=[]
                elif n%step==0 or n==len(points)-1:segment.append({'lat':p[0],'lng':p[1]})
            if segment:segments.append(segment)
            lines.append({'name':name,'segments':segments})
        from mapview import COLORS,density_segments
        cells=[]
        if heat:
            counts,grid=density_segments([points for _,points in routes])
            from mapview import unproject
            if len(counts)>50000:raise ValueError('Too many heatmap cells for this view')
            cells=[[*unproject(x/grid,y/grid),v] for (x,y),v in counts.items()]
        payload=json.dumps({'lines':lines,'colors':COLORS,'cells':cells},ensure_ascii=True).replace('<','\\u003c')
        from urllib.parse import quote
        html='''<!doctype html><html><head><meta charset="utf-8"><style>html,body,#map{height:100%;margin:0}#error{position:absolute;top:10px;left:10px;background:white;padding:8px;z-index:9}</style></head><body><div id="map"></div><script>
        const data=PAYLOAD;
        window.gm_authFailure=()=>document.body.innerText='Google Maps: API key / billing / referrer restriction error';
        window.initMap=()=>{
          const map=new google.maps.Map(document.getElementById('map'),{zoom:8,center:{lat:51,lng:8}});
          const bounds=new google.maps.LatLngBounds();
          data.lines.forEach((line,i)=>line.segments.forEach(path=>{
            path.forEach(p=>bounds.extend(p));
            if(!data.cells.length)new google.maps.Polyline({path,map,strokeColor:data.colors[i%data.colors.length],strokeWeight:3});
          }));
          if(!bounds.isEmpty())map.fitBounds(bounds);
          if(data.cells.length){
            const max=Math.max(...data.cells.map(c=>c[2]));
            class Heat extends google.maps.OverlayView {
              onAdd(){this.canvas=document.createElement('canvas');this.canvas.style.cssText='position:absolute;pointer-events:none';this.getPanes().overlayLayer.appendChild(this.canvas);}
              draw(){const d=map.getDiv(),w=d.clientWidth,h=d.clientHeight;this.canvas.width=w;this.canvas.height=h;const projection=this.getProjection();const origin=projection.fromContainerPixelToLatLng(new google.maps.Point(0,0));const offset=projection.fromLatLngToDivPixel(origin);this.canvas.style.left=offset.x+'px';this.canvas.style.top=offset.y+'px';const ctx=this.canvas.getContext('2d');data.cells.forEach(c=>{const p=projection.fromLatLngToDivPixel(new google.maps.LatLng(c[0],c[1]));ctx.fillStyle='hsla('+Math.round(230*(1-c[2]/max))+',90%,50%,0.45)';ctx.beginPath();ctx.arc(p.x-offset.x,p.y-offset.y,7,0,Math.PI*2);ctx.fill();});}
              onRemove(){this.canvas.remove();}
            } new Heat().setMap(map);
          }
        };
        </script><script async src="https://maps.googleapis.com/maps/api/js?key=APIKEY&amp;callback=initMap"></script></body></html>'''.replace('PAYLOAD',payload).replace('APIKEY',quote(key.strip(),safe=''))
        if len(html.encode())>1800000:raise ValueError('Map selection too large')
        dialog=QDialog(parent);dialog.setWindowTitle('Google Maps');dialog.resize(1000,720);layout=QVBoxLayout(dialog)
        layout.addWidget(QLabel(t('Onlineansicht · tatsächliche GPS-Strecken · Teilen über KML / Google My Maps','Online view · recorded GPS tracks · Share through KML / Google My Maps')))
        view=QWebEngineView(dialog);profile=QWebEngineProfile(view);profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
        page=QWebEnginePage(profile,view);view.setPage(page);layout.addWidget(view)
        view.setHtml(html,QUrl('https://garmin-export-studio.invalid/'));dialog.exec()
        view.setHtml('');page.deleteLater();view.deleteLater();profile.deleteLater()
    except Exception as exc:parent.error(exc)
