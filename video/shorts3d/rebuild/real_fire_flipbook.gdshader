// Brackeys public-domain (CC0) 64-frame continuous flame flipbook.
// Each frame is original royalty-free footage, animated and positioned
// in the authored 3D London buildings. Source: github.com/Brackeys/vfx-in-godot
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled;
uniform sampler2D flipbook : source_color, filter_linear_mipmap;
uniform float speed : hint_range(2.0,60.0) = 23.0;
uniform float offset = 0.0;
uniform float opacity : hint_range(0.0,3.0) = 1.0;
uniform float brightness : hint_range(0.0,5.0) = 2.0;
void vertex() {
    float root = UV.y;
    VERTEX.x += (1.0-root)*0.065*sin(TIME*3.1+offset*0.73);
}
void fragment(){
    float frame=mod(floor(TIME*speed+offset),64.0);
    vec2 atlas=vec2(mod(frame,16.0),floor(frame/16.0));
    vec2 q=(atlas+clamp(UV,vec2(0.002),vec2(0.998)))/vec2(16.0,4.0);
    vec3 rgb=texture(flipbook,q).rgb;
    float luminous=max(max(rgb.r,rgb.g),rgb.b);
    float key=smoothstep(0.035,0.20,luminous);
    ALBEDO=rgb*brightness;
    EMISSION=rgb*brightness*0.8;
    ALPHA=opacity*key;
}
