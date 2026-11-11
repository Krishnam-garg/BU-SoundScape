"""
Campus noise map builder.   python build_noise_map.py   ->  noise_map.html

Inputs (same folder as this script):
  noise_data_slot_avg_from_inconsistent.csv   per-location, per-slot averages
  zones_with_centers_and_vertices.csv     zone centers / polygons (fallback)
  zones.geojson                           OPTIONAL - your GeoJSON; used if present
Set ZONE_NAME_PROP if the zone-name field in your GeoJSON isn't auto-detected.
"""
import json, os, numpy as np, pandas as pd, folium

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)
SLOTS = ['Morning', 'Afternoon', 'Evening', 'Night', 'Midnight']
ZONE_NAME_PROP = None          # e.g. "Zone"; None = auto-detect
GEOJSON_FILE = P('zones.geojson')

# ---------------------------------------------------------------- data
# one row per location per slot: zone, point_id, time_slot, latitude, longitude, decibels, readings
DATA_FILE = P('NoiseDataAvg.csv')
df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')

def cat(db):   # category labels
    return 'Silent' if db < 50 else 'Moderate' if db < 59 else 'Noisy' if db < 68 else 'Chaotic'

points = []
for pid, g in df.groupby('point_id'):
    slots = {}
    for s in SLOTS:
        x = g[g.time_slot == s]
        if len(x):
            r = x.iloc[0]
            slots[s] = dict(avg=round(float(r.decibels), 1), n=int(r.readings), cat=cat(r.decibels))
    points.append(dict(id=pid, zone=g.zone.iloc[0], lat=round(g.latitude.mean(), 6),
                       lon=round(g.longitude.mean(), 6), slots=slots))

zone_stats = {z: {s: round(g[g.time_slot == s].decibels.mean(), 1) for s in SLOTS}
              for z, g in df.groupby('zone')}

# ---------------------------------------------------------------- zone polygons
if os.path.exists(GEOJSON_FILE):
    zones_geo = json.load(open(GEOJSON_FILE, encoding='utf-8'))
    print('Using', GEOJSON_FILE)
else:
    zc = pd.read_csv(P('zones_with_centers_and_vertices.csv'), encoding='utf-8-sig')
    feats = []
    for _, r in zc.iterrows():
        v = json.loads(r['Vertices']) if isinstance(r['Vertices'], str) else []
        if len(v) < 3: continue
        ring = [[p['longitude'], p['latitude']] for p in v]; ring.append(ring[0])
        feats.append(dict(type='Feature', properties={'Zone': r['Zone']},
                          geometry=dict(type='Polygon', coordinates=[ring])))
    zones_geo = dict(type='FeatureCollection', features=feats)
    print('No zones.geojson found - built zones from the vertices CSV')

if ZONE_NAME_PROP is None:
    props = zones_geo['features'][0]['properties']
    ZONE_NAME_PROP = next((k for k in props if k.lower() in ('zone', 'name', 'zone_name', 'zonename')), list(props)[0])

for f in zones_geo['features']:   # tidy names like "Paid<br>Mess" -> "Paid Mess"
    f['properties'][ZONE_NAME_PROP] = f['properties'][ZONE_NAME_PROP].replace('<br>', ' ').strip()
zone_cat = {f['properties'][ZONE_NAME_PROP]: f['properties'].get('zone_category', '') for f in zones_geo['features']}

# ---------------------------------------------------------------- map
m = folium.Map(location=[df.latitude.mean(), df.longitude.mean()], zoom_start=17, max_zoom=21,
               tiles=None, control_scale=True, zoom_control=False)
G = 'https://mt1.google.com/vt/lyrs=%s&x={x}&y={y}&z={z}'
folium.TileLayer(G % 's', attr='Google', name='Satellite', max_zoom=21, overlay=False, show=True).add_to(m)
folium.TileLayer(G % 'm', attr='Google', name='Google Maps', max_zoom=21, overlay=False, show=False).add_to(m)
folium.TileLayer(G % 'y', attr='Google', name='Satellite + labels', max_zoom=21, overlay=False, show=False).add_to(m)
m.fit_bounds([[df.latitude.min(), df.longitude.min()], [df.latitude.max(), df.longitude.max()]])

TEMPLATE = r"""
<style>
 :root{--ink:#f4f1ff;--mut:#a39dbd;--glass:rgba(12,10,22,.6);--line:rgba(244,241,255,.13);--acc:#d2ff1a;--pop:rgba(14,11,26,.8)}
 .glass{background:var(--glass);backdrop-filter:blur(16px) saturate(1.3);-webkit-backdrop-filter:blur(16px) saturate(1.3);border:1px solid rgba(255,255,255,.14);
  box-shadow:0 8px 32px rgba(0,0,0,.45);border-radius:18px;font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink)}
 #bar{position:absolute;z-index:9999;top:16px;left:50%;transform:translateX(-50%);display:flex;align-items:center;gap:8px;padding:6px}
 #seg{position:relative;display:flex;background:rgba(255,255,255,.07);border-radius:14px;padding:4px}
 #thumb{position:absolute;top:4px;bottom:4px;left:4px;border-radius:11px;background:var(--acc);box-shadow:0 0 18px rgba(210,255,26,.4);
  transition:transform .28s cubic-bezier(.4,.1,.2,1)}
 #seg button{position:relative;z-index:1;border:0;background:none;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:1px;
  padding:7px 16px;min-width:84px;font:600 12.5px inherit;font-family:inherit;color:#b9b3d1;border-radius:11px;transition:color .2s}
 #seg button .ic{font-size:17px;line-height:1} #seg button.on{color:#07060c}
 #play{border:0;cursor:pointer;width:40px;height:40px;border-radius:50%;background:var(--acc);color:#07060c;font-size:14px;flex:none}
 #title{position:absolute;z-index:9999;top:16px;left:16px;padding:10px 14px}
 #title b{display:block;font-size:15px} #title span{font-size:11.5px;color:var(--mut)}
 #legend{position:absolute;z-index:9999;left:16px;bottom:28px;padding:12px 14px;width:240px}
 #legend h5{margin:0 0 8px;font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:var(--mut)}
 #lbar{height:10px;border-radius:6px} #lt{position:relative;height:26px;margin-top:4px;font-size:10.5px;color:var(--mut)}
 #lt span{position:absolute;transform:translateX(-50%);text-align:center;line-height:1.15;white-space:nowrap}
 #lt span i{display:block;font-style:normal;font-weight:700;color:var(--ink)}
 .sw{display:flex;align-items:center;justify-content:space-between;font-size:13px;margin-top:8px;cursor:pointer;user-select:none}
 .sw input{display:none} .sw .t{width:36px;height:20px;border-radius:20px;background:rgba(255,255,255,.2);position:relative;transition:.2s}
 .sw .t:after{content:"";position:absolute;top:2px;left:2px;width:16px;height:16px;border-radius:50%;background:#fff;transition:.2s;box-shadow:0 1px 3px rgba(0,0,0,.3)}
 .sw input:checked+.t{background:var(--acc)} .sw input:checked+.t:after{transform:translateX(16px)}
 #toast{position:absolute;z-index:10000;left:50%;top:84px;transform:translate(-50%,-8px);padding:9px 16px;font-size:13px;opacity:0;pointer-events:none;transition:.25s}
 #toast.show{opacity:1;transform:translate(-50%,0)}
 .np .leaflet-popup-content-wrapper{border-radius:18px;padding:0;background:var(--pop);color:var(--ink);backdrop-filter:blur(16px) saturate(1.3);-webkit-backdrop-filter:blur(16px) saturate(1.3);border:1px solid rgba(255,255,255,.14);box-shadow:0 12px 40px rgba(0,0,0,.55)}
 .np .leaflet-popup-tip{background:var(--pop)} .np a.leaflet-popup-close-button{color:var(--mut)} .np a.leaflet-popup-close-button:hover{color:var(--ink)}
 .np .leaflet-popup-content{margin:0;width:268px!important;font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
 .np .leaflet-popup-tip{box-shadow:none;border:1px solid rgba(255,255,255,.1)}
 .pc{padding:14px 16px 12px} .pc .z{font-weight:700;font-size:15px;padding-right:14px} .pc .sub{font-size:11.5px;color:var(--mut);margin-top:1px}
 .pc .db{font-size:34px;font-weight:800;line-height:1.1;margin-top:8px} .pc .db small{font-size:14px;font-weight:600;color:var(--mut)}
 .chip{display:inline-block;padding:3px 9px;border-radius:20px;font-size:11.5px;font-weight:700;color:#fff;margin-top:6px}
 .pc .meta{font-size:12px;color:#cfc9e6;margin-top:8px;display:grid;grid-template-columns:1fr auto;gap:3px 10px}
 .pc .meta b{font-weight:600;text-align:right}
 .pc hr{border:0;border-top:1px solid var(--line);margin:10px 0 8px}
 .row{display:grid;grid-template-columns:62px 1fr 38px;align-items:center;gap:8px;font-size:11.5px;margin:4px 0;color:#b9b3d1}
 .row.cur{font-weight:700;color:var(--ink)} .trk{position:relative;height:7px;border-radius:5px;background:rgba(255,255,255,.12)}
 .trk i{position:absolute;left:0;top:0;bottom:0;border-radius:5px} .trk u{position:absolute;top:-2px;bottom:-2px;width:2px;background:#f4f1ff;opacity:.7}
 .row span:last-child{text-align:right}
 .foot{font-size:10.5px;color:var(--mut);margin-top:6px}
 .leaflet-tooltip{background:var(--pop);color:var(--ink);border:1px solid rgba(255,255,255,.15);border-radius:10px;box-shadow:0 6px 20px rgba(0,0,0,.4);backdrop-filter:blur(10px);font-family:Inter,system-ui,sans-serif}
 .leaflet-tooltip:before{display:none}
 .leaflet-control-layers{background:var(--glass)!important;color:var(--ink)!important;border:1px solid rgba(255,255,255,.14)!important;border-radius:14px!important;backdrop-filter:blur(16px);box-shadow:0 8px 32px rgba(0,0,0,.45)!important}
 .leaflet-control-layers-toggle{filter:invert(1) brightness(1.2)}
 .leaflet-control-attribution{background:rgba(12,10,22,.55)!important;color:var(--mut)!important}.leaflet-control-attribution a{color:var(--ink)!important}
 .leaflet-control-scale-line{background:rgba(12,10,22,.55)!important;color:var(--ink)!important;border-color:var(--ink)!important}
 @media(max-width:700px){#bar{top:auto;bottom:14px;width:calc(100vw - 20px)} #seg{flex:1} #seg button{min-width:0;flex:1;padding:7px 2px;font-size:11px}
  #title{display:none} #legend{bottom:86px;left:10px;width:200px;padding:10px 12px} #toast{top:20px}}
</style>
<div id="title" class="glass"><b>Campus Noise Map</b><span>Average noise level, dB(A)</span></div>
<div id="bar" class="glass">
 <div id="seg"><div id="thumb"></div>
  <button data-i="0"><span class="ic">&#127749;</span>Morning</button>
  <button data-i="1"><span class="ic">&#9728;&#65039;</span>Afternoon</button>
  <button data-i="2"><span class="ic">&#127751;</span>Evening</button>
  <button data-i="3"><span class="ic">&#127769;</span>Night</button>
  <button data-i="4"><span class="ic">&#127756;</span>Midnight</button>
 </div>
 <button id="play" title="Play through the day">&#9654;</button>
</div>
<div id="legend" class="glass">
 <h5>Noise level &middot; dB(A)</h5><div id="lbar"></div><div id="lt"></div>
 <label class="sw">Heat map<input type="checkbox" id="t-heat" checked><span class="t"></span></label>
 <label class="sw">Zone outlines<input type="checkbox" id="t-zones" checked><span class="t"></span></label>
</div>
<div id="toast" class="glass">No reading close by &ndash; tap nearer to a measured spot</div>
<script>
window.addEventListener('load', function(){
 var map = __MAP__;
 var SLOTS=__SLOTS__, POINTS=__POINTS__, ZSTATS=__ZSTATS__, ZGEO=__ZGEO__, ZPROP=__ZPROP__, ZCAT=__ZCAT__;
 var MIN=38, MAX=78, slot=0, selected=null;
 // green ~ WHO night limit (45), yellow ~ WHO daytime limit (55), orange/red = clearly above the limits
 var ANCH=[[38,'#2b83ba'],[46,'#66bd63'],[54,'#e5e84f'],[62,'#fdae61'],[70,'#e0301e'],[78,'#7f0000']];
 var hex=function(c){return [1,3,5].map(function(k){return parseInt(c.substr(k,2),16)})};
 function color(db){db=Math.max(MIN,Math.min(MAX,db));
   for(var i=0;i<ANCH.length-1;i++){var a=ANCH[i],b=ANCH[i+1];
     if(db<=b[0]){var f=(db-a[0])/(b[0]-a[0]),x=hex(a[1]),y=hex(b[1]);
       return 'rgb('+x.map(function(v,k){return Math.round(v+(y[k]-v)*f)}).join(',')+')'}}
   return ANCH[ANCH.length-1][1]}
 var pos=function(db){return (db-MIN)/(MAX-MIN)};
 var grad={}; ANCH.forEach(function(a){grad[pos(a[0]).toFixed(3)]=a[1]});
 document.getElementById('lbar').style.background='linear-gradient(90deg,'+ANCH.map(function(a){return a[1]+' '+(pos(a[0])*100).toFixed(1)+'%'}).join(',')+')';
 document.getElementById('lt').innerHTML=[[45,'WHO night'],[55,'WHO day'],[70,'']].map(function(t){
   return '<span style="left:'+pos(t[0])*100+'%"><i>'+t[0]+'</i>'+t[1]+'</span>'}).join('')+
   '<span style="left:0;transform:none"><i>38</i></span><span style="left:100%;transform:translateX(-100%)"><i>78</i></span>';
 var norm=function(s){return String(s).trim().toLowerCase()};
 var zs={}; Object.keys(ZSTATS).forEach(function(k){zs[norm(k)]=ZSTATS[k]});
 var limit=function(n){return (n==='Night'||n==='Midnight')?45:55};
 function status(db,n){var o=db-limit(n);
   if(o<=0) return ['Within WHO limit','#16a34a',o]; if(o<=10) return ['Above WHO limit','#ea8a0c',o];
   if(o<=20) return ['Well above WHO limit','#dc2626',o]; return ['Severely above WHO limit','#7f1d1d',o]}

 // smooth noise surface: inverse-distance-weighted dB painted on a canvas (true dB colours, no additive saturation)
 var LA=POINTS.map(function(p){return p.lat}), LO=POINTS.map(function(p){return p.lon}), PAD=.0016;
 var S=Math.min.apply(null,LA)-PAD, N=Math.max.apply(null,LA)+PAD, W=Math.min.apply(null,LO)-PAD, E=Math.max.apply(null,LO)+PAD;
 var LAT0=(S+N)/2, KX=111320*Math.cos(LAT0*Math.PI/180), KY=110574;
 var GW=190, GH=Math.max(40,Math.round(GW*((N-S)*KY)/((E-W)*KX)));
 var PX=POINTS.map(function(p){return [(p.lon-W)*KX,(p.lat-S)*KY]});
 var cv=document.createElement('canvas'); cv.width=GW; cv.height=GH; var cx=cv.getContext('2d');
 var COL=[]; for(var q=0;q<=200;q++){COL.push(color(MIN+(MAX-MIN)*q/200).match(/\d+/g).map(Number))}
 function surface(name){
  var img=cx.createImageData(GW,GH), v=POINTS.map(function(p){return p.slots[name].avg});
  var cw=(E-W)*KX/GW, ch=(N-S)*KY/GH;
  for(var gy=0;gy<GH;gy++){ for(var gx=0;gx<GW;gx++){
    var x=(gx+.5)*cw, y=(GH-gy-.5)*ch, sw=0, sv=0, dmin=1e9;
    for(var i=0;i<PX.length;i++){var dx=x-PX[i][0], dy=y-PX[i][1], d2=dx*dx+dy*dy+25;
      if(d2<dmin) dmin=d2; var w=1/(d2*d2); sw+=w; sv+=w*v[i]}
    var db=sv/sw, c=COL[Math.max(0,Math.min(200,Math.round((db-MIN)/(MAX-MIN)*200)))];
    var dm=Math.sqrt(dmin), a=Math.max(0,Math.min(1,(105-dm)/60));
    var o=4*(gy*GW+gx); img.data[o]=c[0]; img.data[o+1]=c[1]; img.data[o+2]=c[2]; img.data[o+3]=Math.round(a*215);
  }}
  cx.putImageData(img,0,0); return cv.toDataURL();
 }
 var heat=L.imageOverlay(surface(SLOTS[0]),[[S,W],[N,E]],{opacity:.85,interactive:false}).addTo(map);
 var zoneLayer=L.geoJSON(ZGEO,{
   style:function(){return {color:'#1f2937',weight:1.6,fillOpacity:.1,fillColor:'#1f2937'}},
   onEachFeature:function(f,l){
     l.on('mouseover',function(){l.setStyle({weight:3,fillOpacity:.2})});
     l.on('mouseout',function(){zoneLayer.resetStyle(l)});
     var n=f.properties[ZPROP], c=ZCAT[n];
     l.bindTooltip(function(){var z=zs[norm(n)],h='<b>'+n+'</b>'+(c?' <span style="opacity:.7">&middot; '+c+'</span>':'');
       if(z){var sn=SLOTS[slot];h+='<br>'+sn+' avg: '+z[sn]+' dB'} return h},{sticky:true});
   }}).addTo(map);
 var ring=null;
 function popup(p){
  var n=SLOTS[slot], s=p.slots[n], st=status(s.avg,n), lim=limit(n), z=zs[norm(p.zone)], zc=ZCAT[p.zone]||'';
  var d=z?s.avg-z[n]:null;
  var rows=SLOTS.map(function(nm,i){var q=p.slots[nm]; if(!q) return '';
    return '<div class="row'+(i==slot?' cur':'')+'"><span>'+nm+'</span><div class="trk"><i style="width:'+Math.max(2,pos(q.avg)*100)+'%;background:'+color(q.avg)+'"></i><u style="left:'+pos(limit(nm))*100+'%"></u></div><span>'+q.avg+'</span></div>'}).join('');
  return '<div class="pc"><div class="z">'+p.zone+'</div><div class="sub">'+(zc?zc+' &middot; ':'')+'Spot '+p.id+'</div>'+
   '<div class="db" style="color:'+color(s.avg)+'">'+s.avg+' <small>dB &middot; '+n+'</small></div>'+
   '<span class="chip" style="background:'+st[1]+'">'+st[0]+(st[2]>0?' (+'+st[2].toFixed(1)+' dB)':'')+'</span>'+
   '<div class="meta"><span>Category</span><b>'+s.cat+'</b><span>WHO outdoor limit ('+(lim==45?'night':'day')+')</span><b>'+lim+' dB</b>'+
   '<span>Zone average</span><b>'+(z?z[n]+' dB':'n/a')+'</b>'+(d!==null?'<span>This spot vs zone</span><b>'+(d>=0?'+':'')+d.toFixed(1)+' dB</b>':'')+
   '<span>Readings averaged</span><b>'+s.n+'</b></div><hr>'+rows+
   '<div class="foot">Black tick = WHO limit for that time of day</div></div>';
 }
 function openFor(p){
  selected=p;
  if(ring) map.removeLayer(ring);
  ring=L.circleMarker([p.lat,p.lon],{radius:9,color:'#111827',weight:3,fillColor:'#fff',fillOpacity:.9,interactive:false}).addTo(map);
  L.popup({className:'np',maxWidth:290,autoPanPadding:[20,110],offset:[0,-4]}).setLatLng([p.lat,p.lon]).setContent(popup(p)).openOn(map);
 }
 map.on('popupclose',function(){selected=null; if(ring){map.removeLayer(ring);ring=null}});
 var toast=document.getElementById('toast'), tt=null;
 map.on('click',function(e){
  var mpp=156543.03392*Math.cos(e.latlng.lat*Math.PI/180)/Math.pow(2,map.getZoom());
  var R=Math.max(30,55*mpp), best=null, bd=1e9;
  POINTS.forEach(function(p){var d=map.distance(e.latlng,[p.lat,p.lon]); if(d<bd){bd=d;best=p}});
  if(best&&bd<=R){openFor(best)} else {toast.classList.add('show');clearTimeout(tt);tt=setTimeout(function(){toast.classList.remove('show')},2200)}
 });
 function update(){
  var n=SLOTS[slot];
  heat.setUrl(surface(n));
  if(selected&&map._popup) map._popup.setContent(popup(selected));
  document.getElementById('thumb').style.width='calc((100% - 8px) / 5)';
  document.getElementById('thumb').style.transform='translateX('+slot*100+'%)';
  Array.prototype.forEach.call(document.querySelectorAll('#seg button'),function(b,i){b.classList.toggle('on',i===slot)});
 }
 Array.prototype.forEach.call(document.querySelectorAll('#seg button'),function(b){
   b.onclick=function(){slot=+b.dataset.i;update()}});
 document.addEventListener('keydown',function(e){
   if(e.key==='ArrowRight'){slot=(slot+1)%5;update()} if(e.key==='ArrowLeft'){slot=(slot+4)%5;update()}});
 var timer=null, btn=document.getElementById('play');
 btn.onclick=function(){ if(timer){clearInterval(timer);timer=null;btn.innerHTML='&#9654;';return}
   btn.innerHTML='&#10074;&#10074;'; timer=setInterval(function(){slot=(slot+1)%5;update()},2000)};
 function bind(id,layer){document.getElementById(id).onchange=function(){this.checked?map.addLayer(layer):map.removeLayer(layer)}}
 bind('t-heat',heat); bind('t-zones',zoneLayer);
 // keep the campus in view: can't zoom out past the campus, can't pan away from it
 var CB=zoneLayer.getBounds(); POINTS.forEach(function(p){CB.extend([p.lat,p.lon])}); CB=CB.pad(.08);
 var PAN=.7; // how far past the campus the map can be dragged (0.25 = tight, 1 = a full campus-size margin)
 function lock(){map.setMinZoom(0); map.setMinZoom(map.getBoundsZoom(CB)); map.setMaxBounds(CB.pad(PAN)); map.options.maxBoundsViscosity=1;
   if(map.getZoom()<map.getMinZoom()) map.setZoom(map.getMinZoom())}
 map.fitBounds(CB,{animate:false}); lock(); map.on('resize',function(){lock(); map.panInsideBounds(CB.pad(PAN),{animate:false})});
 map.getContainer().style.cursor='pointer'; update();
});
</script>
"""
vals = dict(MAP=m.get_name(), SLOTS=json.dumps(SLOTS), POINTS=json.dumps(points),
            ZSTATS=json.dumps(zone_stats), ZGEO=json.dumps(zones_geo), ZPROP=json.dumps(ZONE_NAME_PROP), ZCAT=json.dumps(zone_cat))
html = TEMPLATE
for k, v in vals.items():
    html = html.replace('__%s__' % k, v)
m.get_root().html.add_child(folium.Element('{% raw %}' + html + '{% endraw %}'))
folium.LayerControl(collapsed=True, position='topright').add_to(m)
out = P('noise_map.html'); m.save(out)
print('Saved', out, '|', len(points), 'points |', len(zones_geo['features']), 'zones | name field:', ZONE_NAME_PROP)
