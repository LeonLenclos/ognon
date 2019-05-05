"use strict";

/****************
**** SETTINGS ***
****************/

const PRECISION = 3; // Min pixel length of a stroke

/****************
**** MODULES ****
****************/
let modules = [];
function callModulesMethod(modulesMethod) {
    modules.forEach(mo => {
        if(mo[modulesMethod] && !mo.busy){
            mo.busy = true;
            mo[modulesMethod](()=>{mo.busy = false});
        } else if (mo.busy){
            console.log(mo.id+"."+modulesMethod+" is busy...");
        }
    });
}

class Module {
    constructor(id) {
        this.id = id;
        this.elmt = document.getElementById(id);
        this.busy = false;
    }
}

/***************
**** CANVAS ****
***************/

//// EVENTS ////

const onCanvasMouseDown = (e) => {
    canvas.pMouseX = e.offsetX;
    canvas.pMouseY = e.offsetY;
};

const onMouseUp = (e) => {
    canvas.pMouseX = null;
    canvas.pMouseY = null;
};

const onCanvasMouseMove = (e) => {
    let x = e.offsetX;
    let y = e.offsetY;
    if(canvas.pMouseX){
        // send tool request only if the distance between mouse and pMouse is greater than PRECISION
        if(Math.abs(canvas.pMouseX - x) > PRECISION
        || Math.abs(canvas.pMouseY - y) > PRECISION) {
            let tool = document.getElementById('tool-selector').value
            let args;
            if (tool == 'draw'){
                args = {coords:[canvas.pMouseX,canvas.pMouseY,x,y]};
            } else if (tool == 'erease'){
                args = {coords:[x,y]};
            }
            fetch('/control/drawer/'+tool+'/', initOptions(args))
            .then(()=>callModulesMethod('update'))
            .catch(handleError);
            canvas.pMouseX = x;
            canvas.pMouseY = y;
        }
    }
};

//// UTILS ////

const drawLines = (lines, style, ctx) => {
    ctx.lineWidth = style.lineWidth;
    ctx.strokeStyle = style.lineColor;
    ctx.beginPath();
    lines.forEach((line) => {
        ctx.moveTo(line[0], line[1]);
        for (var i = 2; i < line.length; i+=2) {
            ctx.lineTo(line[i], line[i+1]);
        }
    });
    ctx.stroke();
}

const clearCanvas = (ctx, bgColor) => {
    ctx.fillStyle = bgColor;
    ctx.fillRect(0, 0, ctx.canvas.clientWidth, ctx.canvas.clientHeight);
}

//// CLASS ////

class Canvas extends Module {
    constructor(id, noOnionSkin=false, onTopOfDefault=false) {
        super(id);
        this.noOnionSkin = noOnionSkin;
        this.responseHandler = handleResponse;

        this.cache = {};
        this.currentImageID = "";
        this.updating = false;
    }

    loadConfig(config) {
        this.elmt.width  = config.width;
        this.elmt.height = config.height;
        this.backgroundColor = config.background_color;
        this.lineColor = config.line_color;
        this.lineWidth = config.line_width;
        this.onionFwColor = config.onion_skin_forward_color;
        this.onionBwColor = config.onion_skin_backward_color;
        this.onionWidth = config.onion_skin_line_width;
    }

    setup(callBack) {

        this.ctx = this.elmt.getContext('2d');
        this.elmt.addEventListener('mousedown', onCanvasMouseDown);
        this.elmt.addEventListener('mousemove', onCanvasMouseMove);
        addEventListener('mouseup',   onMouseUp);

        // load config
        fetch('/view/get_view_config/', initOptions())
        .then(this.responseHandler)
        .then(json =>{
            this.loadConfig(json);
            this.update(callBack);
        })
        .catch(handleError);
    }

    update(callBack) {
        /*
        Call draw or drawOnionSkin depending on playing info given by /view/get_cursor_infos/
        */
        fetch('/view/get_cursor_infos/', initOptions())
        .then(this.responseHandler)
        .then(json =>{
            if (json.playing || this.noOnionSkin) {
                this.draw(json, [0])
            } else {
                this.draw(json, [-1, 0, 1])
            }
            this.updating = false;
            callBack();
        })
        .catch(handleError);
    }

    draw(pos, onionRange=[0]) {
        /*
        Draw lines given by /view/get_onion_skin/ 
        */
        let cursorPos = pos.project_name + ' ' + pos.anim + ' ' +  pos.layer + ' ' + pos.frm;
        let projState = pos.project_state_id;
        let imageID = cursorPos + ' ' + projState + ' '  + onionRange;

        let getCol = (skin) => {
            if(skin < 0){
                return this.onionBwColor;
            } else if (skin > 0) {
                return this.onionFwColor;
            } else{
                return this.lineColor;
            }
        };

        let drawSkin = (skins, i) => {
            drawLines(skins[i], {lineWidth:this.lineWidth, lineColor:getCol(i)}, this.ctx);
        };

        let drawSkins = (skins, range) => {
            clearCanvas(this.ctx, this.backgroundColor);
            range.filter(e=>e!=0).forEach(i=>{
                drawSkin(skins, i);
            });
            drawSkin(skins, 0);
        };

        if (this.currentImageID == imageID)
        {
            return;
        }
        else if (cursorPos in this.cache 
                && onionRange.every((i)=> i in this.cache[cursorPos].onionSkin) 
                && this.cache[cursorPos].state_id == projState)
        {
            drawSkins(this.cache[cursorPos].onionSkin, onionRange);
            this.currentImageID = imageID
        }
        else
        {
            fetch('/view/get_onion_skin/', initOptions({onion_range:onionRange}))
            .then(this.responseHandler)
            .then(onionSkin => {
                drawSkins(onionSkin, onionRange);
                this.cache[cursorPos] = {
                    state_id:projState,
                    onionSkin:onionSkin
                };
                this.currentImageID = imageID
            })
            .catch(handleError);

        }
    }
}


class SweetCanvas extends Canvas {
    /*
    Same as Canvas but ignore errors
    */
    constructor(id, noOnionSkin=false) {
        super(id, noOnionSkin);
        this.responseHandler = handleResponseQuiet;
    }

}


/****************
**** TOOLBAR ****
****************/

//// EVENTS ////

const onControlClick = (e) => {
    let url = '/control/'
        + e.currentTarget.parentNode.id + '/'
        + e.currentTarget.id + '/';
    let args = {};

    if(e.currentTarget.dataset.required) {
        let required = e.currentTarget.dataset.required.split(" ");
        required.forEach(r=>{
            args[r] = e.currentTarget.parentNode.querySelector('input[name='+r+']').value;
        });
    }
    

    fetch(url, initOptions(args))
    .then(handleResponse)
    .then(()=>callModulesMethod('update'));
    .catch(handleError);
};

//// CLASS ////

class Toolbar extends Module {
    constructor(id) {
        super(id);
    }

    setup(callBack) {
        this.elmt.querySelectorAll("button")
        .forEach(control=>control.addEventListener('click', onControlClick));
        this.elmt.querySelectorAll('#projectmanager button')
        .forEach(e=>e.addEventListener('click', ()=>callModulesMethod('setup')));
        callBack();
    }
}

/*****************
**** TIMELINE ****
*****************/

//// EVENTS ////

const onFrmClick = (e) => {
    let i = Number(e.currentTarget.dataset.frm);
    fetch('/control/navigator/go_to_frm/', initOptions({i:i}))
    .then(()=>callModulesMethod('update'))
    .catch(handleError);
};

const onLayerClick = (e) => {
    let layer = Number(e.currentTarget.dataset.layer);
    fetch('/control/navigator/go_to_layer/', initOptions({i:layer}))
    .then(()=>callModulesMethod('update'))
    .catch(handleError);
}

const onElementClick = (e) => {
    let i = Number(e.currentTarget.dataset.frm);
    let layer = Number(e.currentTarget.parentNode.dataset.layer);
    fetch('/control/navigator/go_to_frm/', initOptions({i:i}))
    .then(fetch('/control/navigator/go_to_layer/', initOptions({i:layer})))
    .then(()=>callModulesMethod('update'))
    .catch(handleError);
}
///// UTILS /////

const createElement = (frm, element) => {
    let td = document.createElement("td");
    td.addEventListener('click', onElementClick);
    td.dataset.frm = frm;
    td.setAttribute("colspan", element.len);
    return td;
}

const createLayerHead = () => {
    let td = document.createElement("td");
    td.addEventListener('click', onLayerClick);
    return td;
}
const createFrmHead = (i) => {
    let td = document.createElement("td");
    td.addEventListener('click', onFrmClick);
    td.dataset.frm = i;
    return td;
}

const createLayerRow = (i, elements) => {
    let tdArray = [createLayerHead()];
    let frm = 0;
    for (let j = 0; j < elements.length; j++) {
        tdArray.push(createElement(frm, elements[j]));
        frm+=elements[j].len;
    }
    let layerRow = document.createElement("tr");
    layerRow.classList.add('layer-row')
    layerRow.dataset.layer = i;
    tdArray.forEach(td=>layerRow.appendChild(td));
    return layerRow;
}

const createFrmsRow = (len) => {
    let tdArray = [createLayerHead()];
    for (let i = 0; i < len; i++) {
        tdArray.push(createFrmHead(i));
    }
    let frmsRow = document.createElement("tr");
    frmsRow.classList.add('frms-row');
    tdArray.forEach(td=>frmsRow.appendChild(td));
    return frmsRow;
}

const createTimeline = (timeline, table) => {
    while(table.firstChild && table.removeChild(table.firstChild)); //empty
    table.appendChild(createFrmsRow(timeline.len));
    for (var i = 0; i < timeline.layers.length; i++) {
        table.appendChild(createLayerRow(i, timeline.layers[i]));
    }
}

const setActiveElement = (dataname, i, element) => {
    if(element.dataset[dataname] == i){
        element.classList.add('active');
    } else {
        element.classList.remove('active');
    }
}
//// CLASS ////

class Timeline extends Module {
    constructor(id) {
        super(id);

        this.currentImageID = "";
        this.currentProjState = "";

    }

    setup(callBack) {
        this.update(callBack);
    }

    update(callBack) {
        fetch('/view/get_cursor_infos/', initOptions())
        .then(handleResponse)
        .then(json =>{
            let cursorPos = json.project_name + ' ' + json.anim + ' ' +  json.layer + ' ' + json.frm;
            let projState = json.project_state_id;
            if (projState != this.currentProjState) {
                this.updateTimeline(json, callBack);
            } else if (cursorPos != this.currentCursorPos) {
                this.updateActive(json, callBack);
            }
            else {
                callBack();
            }
            this.currentCursorPos = cursorPos;
            this.currentProjState = projState;
        })
    }

    updateActive(pos, callBack) {
        /*
        Remove active class from frm-heading and layer-row.
        Set current layer and frm to active
        */
        this.elmt.querySelectorAll('.frms-row td')
        .forEach((e)=>setActiveElement('frm', pos.frm, e));
        this.elmt.querySelectorAll('.layer-row')
        .forEach((e)=>setActiveElement('layer', pos.layer, e));
        callBack();
    }

    updateTimeline(pos, callBack) {
        fetch('/view/get_timeline/', initOptions())
        .then(handleResponse)
        .then(json => {
            createTimeline(json, this.elmt);
            this.updateActive(pos, callBack);
        })
        .catch(handleError);
    }
}

/******************
**** STATUSBAR ****
******************/


//// UTILS ////

const updateInfos = (infos, statusbar) =>{
    const null_to_str = (a) => a === null ? "" : a
    statusbar.querySelectorAll('span')
    .forEach(e=>e.innerHTML = null_to_str(infos[e.id]))
}

//// CLASS ////

class Statusbar extends Module {
    constructor(id, requestPath) {
        super(id);
        this.requestPath = requestPath
        this.setup = this.onCursorMove
    }

    setup(callBack){
        this.update(callBack);
    }

    update(callBack) {
        fetch(this.requestPath, initOptions())
        .then(handleResponse)
        .then(json => {
            updateInfos(json, this.elmt)
            callBack();
        })
        .catch(handleError);
    }
}
