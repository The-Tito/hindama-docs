"""Genera el símbolo y el logotipo de Hindama (04-ui/identidad).

Uso: python3 build.py <carpeta-de-salida>
Escribe hindama-symbol.svg y hindama-wordmark.svg. Trazo 40, x-height 84-228, ascendente 28.
"""
import sys, os
out = sys.argv[1]
W = 40; B = 228; XT = 84; ASC = 28
def rect(x0,x1,y0,y1): return f'<path d="M{x0} {y0}H{x1}V{y1}H{x0}Z"/>'
def arch(L,R,cy,bot=None):
    bot = B if bot is None else bot
    rc=(R-L)/2; ro=rc+W/2; ri=rc-W/2
    return f'<path d="M{L-W/2} {cy}A{ro} {ro} 0 0 1 {R+W/2} {cy}V{bot}H{R-W/2}V{cy}A{ri} {ri} 0 0 0 {L+W/2} {cy}Z"/>'
def ring(cx,cy,ro,ri):
    return (f'<path fill-rule="evenodd" d="M{cx-ro} {cy}a{ro} {ro} 0 1 0 {2*ro} 0a{ro} {ro} 0 1 0 {-2*ro} 0Z'
            f'M{cx-ri} {cy}a{ri} {ri} 0 1 0 {2*ri} 0a{ri} {ri} 0 1 0 {-2*ri} 0Z"/>')
def circ(cx,cy,r): return f'<circle cx="{cx}" cy="{cy}" r="{r}"/>'
def h_node(x):  # símbolo: h con nodo
    return [rect(x,x+40,ASC,B), arch(x+20,x+132,160,178), circ(x+132,199,30)]
def h_plain(x): return [rect(x,x+40,ASC,B), arch(x+20,x+132,160)]
def i(x): return [rect(x,x+40,XT,B), circ(x+20,46,22)]
def n(x): return [rect(x,x+40,XT,B), arch(x+20,x+132,160)]
def bowl(x): cx=x+74; return [ring(cx,156,74,34)], cx
def d(x): p,cx=bowl(x); return p+[rect(cx+34,cx+74,ASC,B)]
def a(x): p,cx=bowl(x); return p+[rect(cx+34,cx+74,XT,B)]
def m(x): return [rect(x,x+40,XT,B), arch(x+20,x+112,150), arch(x+112,x+204,150)]
def svg(vb,parts,title="Hindama",fill="#000"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}"><title>{title}</title>'
            f'<g fill="{fill}">{"".join(parts)}</g></svg>\n')
def wordmark(node=True):
    P=[]; x=0
    P+= h_node(x) if node else h_plain(x); x+=162+26
    P+= i(x); x+=40+28
    P+= n(x); x+=152+24
    P+= d(x); x+=152+24
    P+= a(x); x+=152+28
    P+= m(x); x+=224+24
    P+= a(x); x+=152
    return P, x
def write(name, s):
    open(os.path.join(out,name),'w').write(s)
# símbolo centrado ópticamente (bbox 0..162 → desplazar)
sym = h_node(0); ox=47
write('hindama-symbol.svg', svg("0 0 256 256", [f'<g transform="translate({ox} 0)">'+''.join(sym)+'</g>']))
P,wd = wordmark(True)
write('hindama-wordmark.svg', svg(f"-8 0 {wd+16} 256", P))
print("wordmark width", wd)
