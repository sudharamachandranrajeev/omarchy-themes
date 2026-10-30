-- Monograph: a single brass rule around the focused window, graphite when
-- idle, and a soft ink shadow. Only colours and shadows change; gaps, input
-- and bindings stay yours.
local active_border_color = "rgba(d4ad6aee)"
local inactive_border_color = "rgba(2e323baa)"
local active_shadow_color = "rgba(0c0e1199)"
local inactive_shadow_color = "rgba(0c0e1166)"

hl.config({
  general = {
    col = {
      active_border = active_border_color,
      inactive_border = inactive_border_color,
    },
  },

  group = {
    col = {
      border_active = active_border_color,
      border_inactive = inactive_border_color,
    },
  },

  decoration = {
    shadow = {
      enabled = true,
      range = 12,
      render_power = 3,
      color = active_shadow_color,
      color_inactive = inactive_shadow_color,
    },
  },
})
