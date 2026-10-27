// Observe actual CSS, text rectangles and ancestor clip edges independently.
exports.observe = element => {
    const rect = e => e.getBoundingClientRect().toJSON();
    const b = rect(element), s = getComputedStyle(element);
    const rgba=c=>{const n=c.match(/[\d.]+/g)?.map(Number)||[0,0,0,0];return[n[0],n[1],n[2],n.length>3?n[3]:1]};
    const mix=(f,b)=>[0,1,2].map(i=>f[i]*f[3]+b[i]*(1-f[3])).concat(1);
    const bg=node=>{const stack=[];for(let p=node;p;p=p.parentElement)stack.push(p);let c=[255,255,255,1];for(const p of stack.reverse())c=mix(rgba(getComputedStyle(p).backgroundColor),c);return c};
    const luminance=c=>c.slice(0,3).map(x=>x/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4).reduce((a,x,i)=>a+x*[.2126,.7152,.0722][i],0);
    const ratio=(a,b)=>{const x=[luminance(a),luminance(b)].sort((a,b)=>a-b);return(x[1]+.05)/(x[0]+.05)};
    const background=bg(element),outside=bg(element.parentElement);
    const clips = [];
    for (let p = element.parentElement; p; p = p.parentElement) {
        const c = getComputedStyle(p), a = rect(p);
        if (['auto', 'scroll', 'hidden', 'clip'].includes(c.overflowX) ||
            ['auto', 'scroll', 'hidden', 'clip'].includes(c.overflowY)) {
            clips.push({tag:p.tagName, class:p.className, x:c.overflowX,
                y:c.overflowY, left:a.left+p.clientLeft,
                right:a.left+p.clientLeft+p.clientWidth,
                top:a.top+p.clientTop, bottom:a.top+p.clientTop+p.clientHeight,
                scrollLeft:p.scrollLeft, scrollTop:p.scrollTop});
        }
    }
    const fit = (a, ring=0, vertical=false) => ({
        viewport:a.left-ring>=-1 && a.right+ring<=innerWidth+1 &&
            (!vertical || a.top-ring>=-1 && a.bottom+ring<=innerHeight+1),
        ancestors:clips.every(c =>
            (!['auto','scroll','hidden','clip'].includes(c.x) ||
             a.left-ring>=c.left-1 && a.right+ring<=c.right+1) &&
            (!vertical || !['auto','scroll','hidden','clip'].includes(c.y) ||
             a.top-ring>=c.top-1 && a.bottom+ring<=c.bottom+1))
    });
    const textRects=[], walker=document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
    for (let n=walker.nextNode(); n; n=walker.nextNode()) {
        if (!n.textContent.trim()) continue;
        const range=document.createRange(); range.selectNodeContents(n);
        const textClips=[];
        for(let p=n.parentElement;p;p=p.parentElement){
            const c=getComputedStyle(p),a=rect(p);
            if(['auto','scroll','hidden','clip'].includes(c.overflowX))
                textClips.push({tag:p.tagName,class:p.className,overflowX:c.overflowX,
                    left:a.left+p.clientLeft,right:a.left+p.clientLeft+p.clientWidth});
        }
        for (const a of range.getClientRects()) if (a.width && a.height)
            textRects.push({...a.toJSON(), ...fit(a),textClips,
                ownAndAncestorTextFit:textClips.every(c=>a.left>=c.left-1&&a.right<=c.right+1)});
    }
    const ring=Math.max(0,parseFloat(s.outlineWidth)+parseFloat(s.outlineOffset));
    const boxFit=fit(b), focusFit=fit(b,ring,true);
    return {tag:element.tagName, text:element.textContent.trim(),
        href:element.getAttribute('href'), name:element.getAttribute('name'),
        value:element.tagName==='INPUT'&&!['csrf_token','revision','key'].includes(element.name)?element.value:undefined,
        box:b, style:Object.fromEntries(['display','fontSize','lineHeight',
            'minHeight','minBlockSize','padding','gap','boxSizing','whiteSpace',
            'overflowWrap','wordBreak','maxWidth','minWidth','overflowX','overflowY',
            'outline','outlineWidth','outlineOffset','outlineStyle','color','backgroundColor','borderColor','borderWidth','borderRadius','fontWeight'].map(k=>[k,s[k]])),
        visual:{background,outside,textContrast:ratio(mix(rgba(s.color),background),background),outlineContrast:ratio(mix(rgba(s.outlineColor),outside),outside),borderContrast:ratio(mix(rgba(s.borderTopColor),outside),outside)},
        clips, textRects, boxFit, textFit:textRects.every(a=>a.viewport&&a.ancestors&&a.ownAndAncestorTextFit),
        focused:element===document.activeElement,
        focusVisible:element.matches(':focus-visible'), ring, focusFit,
        viewport:{width:innerWidth,height:innerHeight,rootFont:getComputedStyle(document.documentElement).fontSize,
            dpr:devicePixelRatio, rootClient:document.documentElement.clientWidth,
            rootScroll:document.documentElement.scrollWidth,scrollX,scrollY},
        associatedLabel:element.labels?.length?{text:element.labels[0].textContent.trim(),box:element.labels[0].getBoundingClientRect().toJSON(),minBlockSize:getComputedStyle(element.labels[0]).minBlockSize,padding:getComputedStyle(element.labels[0]).padding}:null};
};
