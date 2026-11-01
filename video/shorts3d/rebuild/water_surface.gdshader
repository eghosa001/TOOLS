shader_type spatial;
render_mode cull_disabled, diffuse_burley, specular_schlick_ggx;
// Low-cost procedural surface treatment for imported CC0 environment scenes.
// Real geometry and authored shorelines are preserved; no pre-recorded footage.
uniform vec4 deep_water : source_color = vec4(0.025, 0.17, 0.28, 1.0);
uniform vec4 shallow_water : source_color = vec4(0.13, 0.38, 0.48, 1.0);
varying vec3 surface_world;
void vertex() {
    surface_world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
    VERTEX.y += 0.045 * sin(VERTEX.x * 1.32 + TIME * 1.9) * cos(VERTEX.z * 0.85 + TIME * 1.3);
}
void fragment() {
    float wave1 = sin(surface_world.x * 2.5 - TIME * 2.3) * sin(surface_world.z * 1.2 + TIME * 1.7);
    float wave2 = sin(surface_world.x * 0.9 + surface_world.z * 1.9 + TIME * 1.2);
    float highlight = pow(max(0.0, 0.5 + 0.5 * wave1), 12.0) * 0.25;
    float tone = clamp(0.45 + 0.22 * wave1 + 0.15 * wave2, 0.0, 1.0);
    ALBEDO = mix(deep_water.rgb, shallow_water.rgb, tone) + vec3(highlight);
    METALLIC = 0.04;
    ROUGHNESS = 0.19;
    SPECULAR = 0.75;
}
