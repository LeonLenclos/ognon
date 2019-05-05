let playing = false;

const canvas    = new Canvas("canvas");
const timeline  = new Timeline("timeline");
const toolbar   = new Toolbar("toolbar");
const elementStatusbar = new Statusbar("element-statusbar", '/view/get_element_infos/');
const cursorStatusbar = new Statusbar("cursor-statusbar", '/view/get_cursor_infos/');

modules = [canvas, timeline, toolbar, cursorStatusbar, elementStatusbar];

    
///////////// AUTOUPDATE
// const autoUpdateOnPlay = () => {
//     fetch('/view/get_cursor_infos/', initOptions())
//     .then(response=>response.json())
//     .then(json=>{
//         console.log(json.playing)
//         if (json.playing){
//             startAutoUpdate();
//         } else {
//             stopAutoUpdate();
//         }
//     });
// }

// document.getElementById('play').addEventListener('click', autoUpdateOnPlay)
// document.getElementById('auto_play').addEventListener('click', autoUpdateOnPlay)

callModulesMethod('setup');
startAutoUpdate();
