// Spatial fire for constructed, historical roof fires in Godot 4.7.
// Adapted as a lightweight three-layer, noise-eroded flame from the MIT
// Godot 4 "Fire Shader" technique by Yui Kinomoto (@arlez80),
// https://godotshaders.com/shader/fire-shader-for-godot-engine-4/.
// This file is MIT licensed. MIT source credit retained; no paid assets.
shader_type spatial;
render_mode unshaded, cull_disabled, blend_mix, depth_draw_never, shadows_disabled;

uniform float flame_speed : hint_range(0.1, 6.0) = 1.75;
uniform float phase = 0.0;
uniform float intensity : hint_range(0.0, 3.0) = 1.0;
uniform vec3 red_color : source_color = vec3(0.78, 0.105, 0.014);
uniform vec3 middle_color : source_color = vec3(1.0, 0.37, 0.042);
uniform vec3 bright_color : source_color = vec3(1.0, 0.92, 0.42);

float hash21(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}
float n2(vec2 p) {
    vec2 ip = floor(p);
    vec2 fp = fract(p);
    fp = fp * fp * (3.0 - 2.0 * fp);
    return mix(mix(hash21(ip), hash21(ip+vec2(1.0,0.0)), fp.x),
               mix(hash21(ip+vec2(0.0,1.0)), hash21(ip+vec2(1.0,1.0)), fp.x),fp.y);
}
void vertex() {
    // The top of the flame bends with wind; the root stays on the timber roof.
    float h = 1.0 - UV.y;
    VERTEX.x += 0.24 * h * h * sin(TIME * 3.6 + phase + UV.y * 6.1);
}
void fragment() {
    float h = 1.0 - UV.y;
    float t = TIME * flame_speed + phase;
    float wind = 0.12 * h * sin(t*1.23 + h*4.0);
    vec2 p = vec2((UV.x-0.5)*4.7, h*4.2 - t*1.85);
    float n = n2(p)*0.54+n2(p*2.03+vec2(4.3,0.0))*0.33+n2(p*4.17)*0.13;
    float width = mix(0.46,0.024,h) * (0.67+0.72*n);
    float d=abs(UV.x-0.5+wind);
    float shape=1.0-smoothstep(width*0.55,width,d);
    float clip_tip=1.0-smoothstep(0.77+0.10*n, 0.99, h);
    float texture_breakup=smoothstep(0.20,0.56,n+0.17*(1.0-h));
    float base=smoothstep(0.0,0.14,h);
    float opacity=clamp(shape*clip_tip*texture_breakup*base*intensity*1.25,0.0,1.0);
    float heat=clamp((1.0-h)*0.77 + n*0.38,0.0,1.0);
    vec3 c=mix(red_color,middle_color,clamp(n*1.65,0.0,1.0));
    c=mix(c,bright_color,smoothstep(0.52,0.93,heat)*0.82);
    ALBEDO=c;
    EMISSION=c*min(intensity*1.8,2.7);
    ALPHA=opacity;
}
