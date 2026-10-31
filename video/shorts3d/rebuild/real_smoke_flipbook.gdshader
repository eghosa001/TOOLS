// CC0 Brackeys 8x8 wispy-smoke image sequence, animated as spatial smoke.
// Source: github.com/Brackeys/vfx-in-godot (Creative Commons Zero).
shader_type spatial;
render_mode unshaded, blend_mix, cull_disabled, depth_draw_never, shadows_disabled;
uniform sampler2D flipbook: source_color, filter_linear_mipmap;
uniform float speed = 17.0;
uniform float offset = 0.0;
uniform float opacity = 0.23;
void vertex(){
    VERTEX.x += (1.0-UV.y)*0.14*sin(TIME*0.75+offset);
}
void fragment(){
    float frame=mod(floor(TIME*speed+offset),64.0);
    vec2 tile=vec2(mod(frame,8.0),floor(frame/8.0));
    vec4 rgba=texture(flipbook,(tile+clamp(UV,vec2(0.002),vec2(0.998)))/8.0);
    float k=max(max(rgba.r,rgba.g),rgba.b);
    ALBEDO=mix(vec3(0.20,0.21,0.20),vec3(0.48,0.45,0.41),k);
    ALPHA=opacity*smoothstep(0.08,0.47,k)*clamp(rgba.a*2.0,0.0,1.0);
}
