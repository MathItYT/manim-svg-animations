from manim import *
from manim_mobject_svg import *
from svgpathtools import svg2paths
from types import NoneType
import itertools
import os


HTML_BASIC_STRUCTURE = """<div>
    <svg id="%s" width="%s" viewBox="0 0 %d %d" style="background-color:%s;"></svg>
</div>"""


HTML_STRUCTURE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-svg-full.min.js" integrity="sha512-rt6EnxNkuTTgQX2397gLDTao/kZrmdNM4ZO7n89nX6KqOauwSQTGOq3shcd/oGyUc0czxMKBvj+gML8dxX4hAg==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
    <title>%s</title>
</head>
<body>
    <div>
        <svg id="%s" width="%s" viewBox="0 0 %d %d" style="background-color:%s;"></svg>
    </div>
    <button onclick="render%s()">Render!</button>
    %s
    <script src="%s"></script>
</body>
</html>"""


JAVASCRIPT_STRUCTURE = """function sleep(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

var rendered = false;
var ready = true;
var %s = document.getElementById("%s");
function render%s() {
    if (!ready) {
        ready = true;
        rendered = false;
        sleep(%f);
    }
    ready = false;
    rendered = false;
%s
    ready = true;
    rendered = true;
}"""


JAVASCRIPT_INTERACTIVE_STRUCTURE = """var combsDict = {%s};
var comb = [%s];
function update(i, val) {
if (!rendered) {
    return
}
var keys = Object.keys(combsDict);
var ithElements = [];
for (let arr of keys) {
    if (Array.isArray(arr[i])) {   
        ithElements.push(arr[i]);
    }
    else {
        ithElements.push(arr);
    }
}
var x = val;
var closest = ithElements.sort( (a, b) => Math.abs(x - a) - Math.abs(x - b))[0];
comb[i] = closest;
combsDict[comb]();
}
"""


class HTMLParsedVMobject:
    def __init__(self, vmobject: VMobject, scene: Scene, width: float = "500px", basic_html: bool = False):
        self.vmobject = vmobject
        self.scene = scene
        self.filename_base = scene.__class__.__name__
        self.html_filename = self.filename_base + ".html"
        self.js_filename = self.filename_base + ".js"
        self.current_index = 0
        self.width = width
        self.basic_html = basic_html
        self.js_updates = ""
        self.continue_updating = True
        self.original_frame_width = self.scene.camera.frame_width
        self.original_frame_height = self.scene.camera.frame_height
        self.interactive_html = ""
        self.has_updates = False
        self.scene.add_updater(self.updater)
    
    def updater(self, dt):
        if self.continue_updating is False:
            return
        svg_filename = self.filename_base + str(self.current_index) + ".svg"
        self.vmobject.to_svg(svg_filename)
        html_el_creations = """if (ready) {
            return
        }
        %s.replaceChildren();""" % self.filename_base.lower()
        _, attributes = svg2paths(svg_filename)
        i = 0
        for attr in attributes:
            html_el_creation = f"        var el{i} = document.createElementNS('http://www.w3.org/2000/svg', 'path');\n"            
            for k, v in attr.items():
                html_el_creation += f"       el{i}.setAttribute('{k}', '{v}');\n"
            html_el_creation += f"       {self.filename_base.lower()}.appendChild(el{i});\n"
            html_el_creations += html_el_creation
            i += 1
        background_color = color_to_int_rgba(self.scene.camera.background_color, self.scene.camera.background_opacity)
        background_color = [*[str(c) for c in background_color[:-1]], str(background_color[-1]/255)]
        background_color = [str(par) for par in background_color]
        html_el_creations += f"     {self.filename_base.lower()}.style.backgroundColor = 'rgb({', '.join(background_color)})';\n"
        if isinstance(self.scene, MovingCameraScene):
            frame = self.scene.camera.frame
            frame_corner = frame.get_corner(UL)
            html_el_creations = self.update_viewbox(
                frame_corner,
                self.scene.camera.frame_width,
                self.scene.camera.frame_height,
                html_el_creations
            )
        if self.has_updates is False:
            self.js_updates += "%s\nsleep(%f).then(() => {\nTOREPLACE\n});" % (
                html_el_creations,
                1000 / self.scene.camera.frame_rate,  
            )
            self.last_update = True
        else:
            html_el_creations += "\nsleep(%f).then(() => {\nTOREPLACE\n});" % (
                1000 / self.scene.camera.frame_rate
            )
            self.js_updates.replace("TOREPLACE", html_el_creations)
            self.last_update = html_el_creations
        self.js_updates += "\n"
        self.current_index += 1
        os.remove(svg_filename)
    
    def update_viewbox(
        self,
        frame_corner: np.ndarray,
        new_frame_width: float,
        new_frame_height: float,
        html_str: str
    ):
        pixel_width = self.scene.camera.pixel_width * new_frame_width / self.original_frame_width
        pixel_height = self.scene.camera.pixel_height * new_frame_height / self.original_frame_height
        pixel_center = frame_corner * self.scene.camera.pixel_width / self.original_frame_width
        pixel_center += self.scene.camera.pixel_width / 2 * RIGHT + self.scene.camera.pixel_height / 2 * DOWN
        pixel_center[1] = -pixel_center[1]
        pixel_center = pixel_center[:2]
        arr = [*pixel_center, pixel_width, pixel_height]
        arr = [str(p) for p in arr]
        html_str += f"     {self.filename_base.lower()}.setAttribute('viewBox', '{' '.join(arr)}');\n"
        return html_str
    
    def update_html(self):
        bg_color = color_to_int_rgba(
            self.scene.camera.background_color,
            self.scene.camera.background_opacity
        )
        bg_color = [*[str(c) for c in bg_color[:-1]], str(bg_color[-1]/255)]
        bg_color = f"rgba({', '.join(bg_color)})"
        if self.basic_html is False:
            self.html = HTML_STRUCTURE % (
                self.filename_base,
                self.filename_base,
                self.width,
                self.scene.camera.pixel_width,
                self.scene.camera.pixel_height,
                bg_color,
                self.filename_base,
                self.interactive_html,
                self.js_filename
            )
        else:
            self.html = HTML_BASIC_STRUCTURE % (
                self.filename_base,
                self.width,
                self.scene.camera.pixel_width,
                self.scene.camera.pixel_height,
                bg_color
            )
    
    def finish(self):
        self.scene.remove_updater(self.updater)
        self.update_html()
        self.js_updates.removesuffix("\n")
        if not hasattr(self, "last_t"):
            self.last_t = self.scene.renderer.time
        js_content = JAVASCRIPT_STRUCTURE % (
            self.filename_base.lower(),
            self.filename_base,
            self.filename_base,
            1000 / self.scene.camera.frame_rate,
            self.js_updates
        )
        if hasattr(self, "interactive_js"):
            js_content += f"\n{self.interactive_js}"
        with open(self.js_filename, "w") as f:
            f.write(js_content)
        with open(self.html_filename, "w") as f:
            f.write(self.html)
    
    def start_interactive(
        self,
        value_trackers: list[ValueTracker],
        linspaces: list[np.ndarray],
        names: list[str] | NoneType = None,
        animate_this=True
    ):
        if animate_this is False:
            self.continue_updating = False
            self.last_t = self.scene.renderer.time
            default_values = [vt.get_value() for vt in value_trackers]
        print("This process can be slow, please wait!")
        self.interactive_js = ""
        filename = "update.svg"
        combs = itertools.product(*linspaces)
        combs_dict = ""
        comb_now = ", ".join([str(v.get_value()) for v in value_trackers])
        for comb in combs:
            for vt, val in zip(value_trackers, comb):
                self.scene.wait(1/self.scene.camera.frame_rate)
                vt.set_value(val)
            self.vmobject.to_svg(filename)
            html_el_creations = f"{self.filename_base.lower()}.replaceChildren();\n"
            _, attributes = svg2paths(filename)
            i = 0
            for attr in attributes:
                html_el_creation = f"        var el{i} = document.createElementNS('http://www.w3.org/2000/svg', 'path');\n"            
                for k, v in attr.items():
                    html_el_creation += f"       el{i}.setAttribute('{k}', '{v}');\n"
                html_el_creation += f"       {self.filename_base.lower()}.appendChild(el{i});\n"
                html_el_creations += html_el_creation
                i += 1
            
            combs_dict += "[" + ", ".join([str(v) for v in comb]) + """]: () => {
                %s
            },
            """ % html_el_creations
        if animate_this is True:
            default_values = [vt.get_value() for vt in value_trackers]
        self.interactive_html += "<div>\n"
        for i, vt in enumerate(value_trackers):
            if names is not None:
                self.interactive_html += f'<label for="slider{i}"></label>\n'
            linspace_ordered = linspaces[i].sort()
            min_val = linspace_ordered[0]
            max_val = linspace_ordered[-1]
            step = linspace_ordered[1] - linspace_ordered[0]
            val = default_values[i]
            self.interactive_html += f'<input type="range" name="slider{i}" min="{min_val}" max="{max_val}"' \
                + f' step="{step}" value="{val}" oninput="update({i}, this.value)">\n'
        self.interactive_html += "</div>"
        self.interactive_js += JAVASCRIPT_INTERACTIVE_STRUCTURE % (combs_dict, comb_now)
        os.remove(filename)