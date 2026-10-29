import json, os, sys
pal = json.load(open(sys.argv[1])); out = sys.argv[2]
def c(f,k): return pal[f]['colors'][k]['hex']
def lum(h):
    r,g,b=[int(h[i:i+2],16)/255 for i in (1,3,5)]
    f=lambda x: x/12.92 if x<=0.03928 else ((x+0.055)/1.055)**2.4
    return 0.2126*f(r)+0.7152*f(g)+0.0722*f(b)
def cr(a,b):
    la,lb=sorted([lum(a),lum(b)],reverse=True); return (la+0.05)/(lb+0.05)
def mix(a,b,t):
    pa=[int(a[i:i+2],16) for i in (1,3,5)]; pb=[int(b[i:i+2],16) for i in (1,3,5)]
    return '#'+''.join('%02x'%round(x+(y-x)*t) for x,y in zip(pa,pb))
def ensure(col,bg,toward,minr,label,notes):
    t=0; x=col
    while cr(x,bg)<minr and t<1: t+=0.02; x=mix(col,toward,t)
    if x!=col: notes.append(f'{label}: {col} -> {x} ({cr(col,bg):.2f} -> {cr(x,bg):.2f})')
    return x
SYNTAX=[ # (name, scopes, palette key, fontStyle)
 ('Comments',['comment','punctuation.definition.comment'],'overlay2','italic'),
 ('Keywords',['keyword','storage.type','storage.modifier'],'mauve',None),
 ('Operators',['keyword.operator','punctuation.accessor'],'sky',None),
 ('Strings',['string','punctuation.definition.string','markup.inline.raw','markup.raw'],'green',None),
 ('Symbols and atoms',['constant.other.symbol','constant.other.atom'],'red',None),
 ('Escapes and regular expressions',['constant.character.escape','string.regexp'],'pink',None),
 ('Constants and numbers',['constant','constant.numeric','constant.language','support.constant','variable.other.constant'],'peach',None),
 ('Functions',['entity.name.function','support.function','meta.function-call'],'blue',None),
 ('Parameters',['variable.parameter'],'maroon','italic'),
 ('Builtins',['variable.language','support.function.builtin','support.variable'],'red',None),
 ('Types',['entity.name.type','entity.name.class','entity.name.namespace','entity.other.inherited-class','support.type','support.class'],'yellow',None),
 ('Enum members',['variable.other.enummember'],'teal',None),
 ('Properties',['support.type.property-name','meta.object-literal.key','variable.other.property'],'blue',None),
 ('Attributes',['entity.other.attribute-name'],'yellow','italic'),
 ('Annotations',['meta.decorator','entity.name.function.decorator','storage.type.annotation'],'yellow',None),
 ('Macros',['entity.name.function.preprocessor','entity.name.function.macro','meta.preprocessor'],'rosewater',None),
 ('Tags',['entity.name.tag'],'blue',None),
 ('Variables',['variable'],'text',None),
 ('Punctuation',['punctuation','meta.brace'],'overlay2',None),
 ('Headings',['markup.heading','entity.name.section'],'red','bold'),
 ('Bold',['markup.bold'],None,'bold'),
 ('Italic',['markup.italic'],None,'italic'),
 ('Links',['markup.underline.link','string.other.link'],'blue','underline'),
 ('Quotes',['markup.quote'],'overlay2','italic'),
 ('Inserted',['markup.inserted'],'green',None),
 ('Deleted',['markup.deleted'],'red',None),
 ('Invalid',['invalid'],'red',None),
]
TERM={'mocha':dict(black='#45475a',red='#f38ba8',green='#a6e3a1',yellow='#f9e2af',blue='#89b4fa',magenta='#f5c2e7',cyan='#94e2d5',white='#bac2de',brightBlack='#585b70',brightRed='#f37799',brightGreen='#89d88b',brightYellow='#ebd391',brightBlue='#74a8fc',brightMagenta='#f2aede',brightCyan='#6bd7ca',brightWhite='#a6adc8'),
      'latte':dict(black='#5c5f77',red='#d20f39',green='#40a02b',yellow='#df8e1d',blue='#1e66f5',magenta='#ea76cb',cyan='#179299',white='#acb0be',brightBlack='#6c6f85',brightRed='#de293e',brightGreen='#49af3d',brightYellow='#eea02d',brightBlue='#456eff',brightMagenta='#fe85d8',brightCyan='#2d9fa8',brightWhite='#bcc0cc')}
notes=[]
for f,base in (('mocha','dark'),('latte','light')):
    k=lambda n: c(f,n)
    dark=base=='dark'
    tok={'--background':k('base'),'--editor-surface':k('base'),'--foreground':k('text'),
     '--card':k('mantle'),'--card-foreground':k('text'),'--popover':k('mantle'),'--popover-foreground':k('text'),
     '--primary':k('mauve'),'--primary-foreground':k('crust') if dark else k('base'),
     '--secondary':k('surface0'),'--secondary-foreground':k('text'),
     '--muted':k('surface0') if dark else k('mantle'),'--muted-foreground':k('subtext0') if dark else k('subtext1'),
     '--accent':k('surface1') if dark else k('surface0'),'--accent-foreground':k('text'),
     '--border':k('surface0'),'--input':k('surface1'),'--ring':k('lavender'),
     '--chart-1':k('mauve'),'--chart-2':k('blue'),'--chart-3':k('green'),'--chart-4':k('peach'),'--chart-5':k('pink'),
     '--sidebar':k('mantle'),'--sidebar-foreground':k('text'),'--sidebar-primary':k('mauve'),
     '--sidebar-primary-foreground':k('crust') if dark else k('base'),
     '--sidebar-accent':k('surface0'),'--sidebar-accent-foreground':k('text'),
     '--sidebar-border':k('crust') if dark else k('surface0'),'--sidebar-ring':k('lavender'),
     '--worktree-sidebar':k('crust') if dark else k('mantle'),'--worktree-sidebar-foreground':k('text'),
     '--worktree-sidebar-accent':k('surface0'),'--worktree-sidebar-accent-foreground':k('text'),
     '--worktree-sidebar-border':k('crust') if dark else k('surface0'),'--worktree-sidebar-ring':k('lavender')}
    for fg,bg in [('--foreground','--background'),('--card-foreground','--card'),('--popover-foreground','--popover'),('--primary-foreground','--primary'),('--secondary-foreground','--secondary'),('--muted-foreground','--muted'),('--accent-foreground','--accent'),('--sidebar-foreground','--sidebar'),('--sidebar-primary-foreground','--sidebar-primary'),('--sidebar-accent-foreground','--sidebar-accent'),('--worktree-sidebar-foreground','--worktree-sidebar'),('--worktree-sidebar-accent-foreground','--worktree-sidebar-accent')]:
        r=cr(tok[fg],tok[bg])
        if r<4.5: notes.append(f'{f} PAIR FAIL {fg}/{bg} {r:.2f}')
    tc=[]
    for name,scopes,key,style in SYNTAX:
        s={}
        if key:
            s['foreground']=ensure(k(key),k('base'),k('text') if dark else '#000000',3.0,f'{f} {name}',notes)
        if style: s['fontStyle']=style
        tc.append({'name':name,'scope':scopes,'settings':s})
    os.makedirs(f'{out}/themes',exist_ok=True); os.makedirs(f'{out}/terminal',exist_ok=True)
    json.dump({'base':base,'tokens':tok,'tokenColors':tc},open(f'{out}/themes/{f}.json','w'),indent=2)
    t={'background':k('base'),'foreground':k('text'),'cursor':k('rosewater'),'cursorAccent':k('crust') if dark else k('base'),'selectionBackground':k('surface2') if dark else k('surface1')}
    t.update(TERM[f])
    json.dump({'schemaVersion':1,'mode':base,'terminal':t},open(f'{out}/terminal/{f}.json','w'),indent=2)
    for p in (f'{out}/themes/{f}.json',f'{out}/terminal/{f}.json'):
        open(p,'a').write('\n'); print(p, os.path.getsize(p),'bytes')
print('\n'.join(notes) or 'all pairs pass')
