// Observe actual CSS, text rectangles and ancestor clip edges independently.
exports.observe = element => {
    const rect = e => e.getBoundingClientRect().toJSON();
    const b = rect(element), s = getComputedStyle(element);
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
        value:element.tagName==='INPUT'?element.value:undefined,
        box:b, style:Object.fromEntries(['display','fontSize','lineHeight',
            'minHeight','minBlockSize','padding','gap','boxSizing','whiteSpace',
            'overflowWrap','wordBreak','maxWidth','minWidth','overflowX','overflowY',
            'outline','outlineWidth','outlineOffset','outlineStyle'].map(k=>[k,s[k]])),
        clips, textRects, boxFit, textFit:textRects.every(a=>a.viewport&&a.ancestors&&a.ownAndAncestorTextFit),
        focused:element===document.activeElement,
        focusVisible:element.matches(':focus-visible'), ring, focusFit,
        viewport:{width:innerWidth,height:innerHeight,rootFont:getComputedStyle(document.documentElement).fontSize,
            dpr:devicePixelRatio, rootClient:document.documentElement.clientWidth,
            rootScroll:document.documentElement.scrollWidth,scrollX,scrollY},
        tableLocal:!!element.closest('.o_ydental_settlement_fee_scroll')};
};
